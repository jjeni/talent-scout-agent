import asyncio
import csv
import io
import json
import logging
import os
import re
import uuid
from pathlib import Path
from typing import Optional

import httpx
import pdfplumber
from bs4 import BeautifulSoup
from docx import Document
import google.generativeai as genai
from dotenv import load_dotenv

from models.candidate_schema import (
    UnifiedCandidateProfile,
    InputType,
    EducationBlock,
    ParseSummary,
)

from utils.gemini_utils import get_model

load_dotenv()
logger = logging.getLogger(__name__)

# Constants for resume parsing
RESUME_MODEL = "gemini-2.5-flash-lite"

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")

PROFILE_PARSE_PROMPT = """
You are a resume parser. Extract candidate information from the following text and return JSON:
{
  "name": "Full Name",
  "skills": ["skill1", "skill2", ...],
  "experience_years": <float>,
  "current_title": "Current Job Title or null",
  "location": "City, Country or Remote description or null",
  "email": "email@example.com or null",
  "education": {
    "degree": "degree type or null",
    "field": "field of study or null",
    "institution": "university name or null",
    "year_graduated": <int or null>
  }
}
Return ONLY valid JSON. Infer experience_years from the career timeline if not stated explicitly.
"""


def _make_id() -> str:
    return f"cand_{uuid.uuid4().hex[:8]}"


def detect_input_type(value: str) -> InputType:
    """Detect input type from a URL or filename string."""
    v = value.lower().strip()
    if "github.com/" in v:
        return InputType.GITHUB
    if "linkedin.com/in/" in v:
        return InputType.LINKEDIN
    if v.endswith(".csv"):
        return InputType.CSV
    if v.endswith(".json") or v.endswith(".jsonl"):
        return InputType.JSON
    if v.endswith(".pdf"):
        return InputType.PDF
    if v.endswith(".docx"):
        return InputType.DOCX
    return InputType.MANUAL


# ─── CSV Ingestor ───────────────────────────────────────────────────────────

def ingest_csv(content: str) -> list[UnifiedCandidateProfile]:
    """Parse a CSV string with columns: name, skills, experience_years, education, location, email."""
    profiles = []
    errors = []
    reader = csv.DictReader(io.StringIO(content))

    for i, row in enumerate(reader):
        try:
            skills = [s.strip() for s in row.get("skills", "").split(",") if s.strip()]
            exp = float(row.get("experience_years", 0) or 0)
            edu_raw = row.get("education", "")
            education = EducationBlock(degree=edu_raw) if edu_raw else None

            profile = UnifiedCandidateProfile(
                id=row.get("id") or _make_id(),
                name=row.get("name", f"Unknown_{i}"),
                skills=skills,
                experience_years=exp,
                location=row.get("location"),
                email=row.get("email"),
                education=education,
                source_type=InputType.CSV,
                data_completeness=_calc_completeness(skills, exp, row.get("location")),
            )
            profiles.append(profile)
        except Exception as e:
            errors.append(f"Row {i}: {e}")
            logger.warning(f"CSV row {i} parse error: {e}")

    logger.info(f"CSV ingested: {len(profiles)} profiles, {len(errors)} errors")
    return profiles


# ─── JSON Ingestor ───────────────────────────────────────────────────────────

def ingest_json(content: str) -> list[UnifiedCandidateProfile]:
    """Parse a JSON array of candidate objects."""
    profiles = []
    try:
        data = json.loads(content)
        if isinstance(data, dict):
            data = [data]
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        return []

    for i, item in enumerate(data):
        try:
            raw_edu = item.get("education", {}) or {}
            if isinstance(raw_edu, str):
                raw_edu = {"degree": raw_edu}
            education = EducationBlock(**raw_edu) if raw_edu else None
            skills_raw = item.get("skills", [])
            if isinstance(skills_raw, str):
                skills_raw = [s.strip() for s in skills_raw.split(",")]

            profile = UnifiedCandidateProfile(
                id=item.get("id") or _make_id(),
                name=item.get("name", f"Unknown_{i}"),
                skills=skills_raw,
                experience_years=float(item.get("experience_years", 0) or 0),
                location=item.get("location"),
                email=item.get("email"),
                education=education,
                current_title=item.get("current_title"),
                source_type=InputType.JSON,
                data_completeness=_calc_completeness(
                    skills_raw, item.get("experience_years"), item.get("location")
                ),
            )
            profiles.append(profile)
        except Exception as e:
            logger.warning(f"JSON item {i} error: {e}")

    return profiles


# ─── PDF / DOCX Ingestor ─────────────────────────────────────────────────────

def _extract_text_pdf(file_bytes: bytes) -> str:
    """Extract plain text from PDF bytes using pdfplumber."""
    text_parts = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                text_parts.append(t)
    return "\n".join(text_parts)


def _extract_text_docx(file_bytes: bytes) -> str:
    """Extract plain text from DOCX bytes."""
    doc = Document(io.BytesIO(file_bytes))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


async def _parse_text_with_llm(raw_text: str, source_type: InputType, model) -> UnifiedCandidateProfile:
    """Use Gemini to parse arbitrary resume text into a UnifiedCandidateProfile."""
    prompt = f"{PROFILE_PARSE_PROMPT}\n\n--- RESUME TEXT ---\n{raw_text[:4000]}\n--- END ---"
    
    # Rate limit check: 5 RPM means we should wait ~12s if several resumes are in a batch, 
    # but we'll start with 5s and use a global lock if needed.
    await asyncio.sleep(5.0) 

    try:
        response = await model.generate_content_async(prompt)
        data = json.loads(response.text)
        raw_edu = data.get("education", {}) or {}
        education = EducationBlock(**raw_edu) if raw_edu else None
        skills = data.get("skills", [])
        return UnifiedCandidateProfile(
            id=_make_id(),
            name=data.get("name", "Unknown"),
            skills=skills,
            experience_years=float(data.get("experience_years", 0) or 0),
            current_title=data.get("current_title"),
            location=data.get("location"),
            email=data.get("email"),
            education=education,
            source_type=source_type,
            raw_text=raw_text[:2000],
            data_completeness=_calc_completeness(skills, data.get("experience_years"), data.get("location")),
        )
    except Exception as e:
        logger.error(f"LLM resume parse error: {e}")
        return UnifiedCandidateProfile(
            id=_make_id(), name="Parse Failed",
            source_type=source_type, raw_text=raw_text[:500],
            parse_errors=[str(e)], data_completeness=0.1,
        )


async def ingest_resume_bytes(file_bytes: bytes, filename: str, api_key: str = None) -> UnifiedCandidateProfile:
    """Uses Gemini vision/multimodal features to parse PDF/DOCX resumes."""
    model = await get_model(
        model_name=RESUME_MODEL,
        api_key=api_key,
        generation_config={"response_mime_type": "application/json", "temperature": 0.1}
    )
    
    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        text = _extract_text_pdf(file_bytes)
        return await _parse_text_with_llm(text, InputType.PDF, model)
    elif ext == ".docx":
        text = _extract_text_docx(file_bytes)
        return await _parse_text_with_llm(text, InputType.DOCX, model)
    else:
        raise ValueError(f"Unsupported resume format: {ext}")


# ─── GitHub Scraper ───────────────────────────────────────────────────────────

async def ingest_github_url(url: str) -> UnifiedCandidateProfile:
    """Scrape a GitHub profile URL and infer skills from repos, languages, and bio."""
    username = _extract_github_username(url)
    if not username:
        raise ValueError(f"Could not extract GitHub username from: {url}")

    headers = {"Accept": "application/vnd.github+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

    async with httpx.AsyncClient(timeout=15.0) as client:
        user_resp = await client.get(f"https://api.github.com/users/{username}", headers=headers)
        user_data = user_resp.json() if user_resp.status_code == 200 else {}

        # Fetch more repos for better skill coverage
        repos_resp = await client.get(
            f"https://api.github.com/users/{username}/repos?sort=pushed&per_page=15",
            headers=headers
        )
        repos = repos_resp.json() if repos_resp.status_code == 200 else []

    # Gather languages and topics
    langs_map: dict[str, int] = {}
    all_topics = []
    for r in repos:
        lang = r.get("language")
        if lang:
            langs_map[lang] = langs_map.get(lang, 0) + 1
        all_topics.extend(r.get("topics", []))
    
    # Sort languages by frequency
    sorted_langs = sorted(langs_map.keys(), key=lambda x: langs_map[x], reverse=True)
    
    # Extract high-intent keywords from repo descriptions
    desc_skills = []
    for r in repos:
        desc = (r.get("description") or "").lower()
        if "react" in desc: desc_skills.append("React")
        if "next.js" in desc or "nextjs" in desc: desc_skills.append("Next.js")
        if "aws" in desc: desc_skills.append("AWS")
        if "docker" in desc: desc_skills.append("Docker")
        if "kubernetes" in desc or " k8s" in desc: desc_skills.append("Kubernetes")
        if "python" in desc: desc_skills.append("Python")
        if "fastapi" in desc: desc_skills.append("FastAPI")

    skills = list(set(sorted_langs[:5] + [t.replace("-", " ").title() for t in all_topics[:10]] + list(set(desc_skills))))

    name = user_data.get("name") or username
    bio = user_data.get("bio", "")
    location = user_data.get("location", "")
    public_repos = user_data.get("public_repos", len(repos))
    created_at = user_data.get("created_at", "")
    
    # Rough seniority estimate from account age
    exp_years = _estimate_exp_from_github(created_at, public_repos)

    completeness = _calc_completeness(skills, exp_years, location)

    return UnifiedCandidateProfile(
        id=_make_id(),
        name=name,
        skills=skills,
        experience_years=exp_years,
        location=location or None,
        source_url=url,
        source_type=InputType.GITHUB,
        github_username=username,
        languages=sorted_langs,
        repos_count=public_repos,
        raw_text=bio,
        data_completeness=completeness,
    )


def _extract_github_username(url: str) -> Optional[str]:
    match = re.search(r"github\.com/([^/?#]+)", url)
    return match.group(1) if match else None


def _estimate_exp_from_github(created_at: str, public_repos: int) -> float:
    """Rough estimate: account age in years (capped at 12)."""
    if not created_at:
        return max(1.0, min(public_repos / 10, 8.0))
    from datetime import datetime
    try:
        created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        years = (datetime.now(created.tzinfo) - created).days / 365.25
        return min(round(years, 1), 12.0)
    except Exception:
        return 2.0


# ─── LinkedIn Scraper ─────────────────────────────────────────────────────────

async def ingest_linkedin_url(url: str) -> UnifiedCandidateProfile:
    """Scrape a public LinkedIn profile page. Returns partial profile (login wall)."""
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36"
    }
    profile = UnifiedCandidateProfile(
        id=_make_id(), name="LinkedIn Profile",
        source_url=url, source_type=InputType.LINKEDIN,
        data_completeness=0.3,
        parse_errors=["LinkedIn public scraping is limited; provide CSV/JSON for full data"],
    )
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            resp = await client.get(url, headers=headers)
        soup = BeautifulSoup(resp.text, "lxml")

        name_tag = soup.find("h1") or soup.find("meta", property="og:title")
        if name_tag:
            n_text = name_tag.get("content") if name_tag.name == "meta" else name_tag.get_text(strip=True)
            # LinkedIn og:title is often "Name - Job Title | LinkedIn"
            profile.name = n_text.split("-")[0].split("|")[0].strip()

        desc_tag = soup.find("meta", property="og:description") or soup.find("div", class_=re.compile(r"text-body-medium"))
        if desc_tag:
            d_text = desc_tag.get("content") if desc_tag.name == "meta" else desc_tag.get_text(strip=True)
            # Remove name from description if it starts with it
            if profile.name in d_text:
                d_text = d_text.replace(profile.name, "").replace("·", "").strip()
            profile.current_title = d_text.split("·")[0].strip()[:100]

        # Extract location if possible
        loc_tag = soup.find("span", class_="top-card__subline-item")
        if loc_tag:
            profile.location = loc_tag.get_text(strip=True)

        profile.linkedin_url = url
        profile.data_completeness = 0.45
    except Exception as e:
        logger.warning(f"LinkedIn scrape failed for {url}: {e}")

    return profile


# ─── Mixed Session Ingestor ────────────────────────────────────────────────────

async def ingest_from_default_dataset() -> list[UnifiedCandidateProfile]:
    """Load the built-in synthetic candidate dataset."""
    from data.candidates import CANDIDATES
    profiles = []
    for item in CANDIDATES:
        raw_edu = item.get("education", {}) or {}
        education = EducationBlock(**raw_edu) if raw_edu else None
        skills = item.get("skills", [])
        profiles.append(UnifiedCandidateProfile(
            id=item["id"],
            name=item["name"],
            skills=skills,
            experience_years=float(item.get("experience_years", 0)),
            location=item.get("location"),
            email=item.get("email"),
            education=education,
            current_title=item.get("current_title"),
            source_type=InputType(item.get("source_type", "csv")),
            data_completeness=_calc_completeness(skills, item.get("experience_years"), item.get("location")),
        ))
    return profiles


def deduplicate(profiles: list[UnifiedCandidateProfile]) -> tuple[list[UnifiedCandidateProfile], int]:
    """Remove duplicate candidates (same name + email or same name + similar skills)."""
    seen_emails: dict[str, UnifiedCandidateProfile] = {}
    seen_names: dict[str, UnifiedCandidateProfile] = {}
    unique = []
    merged = 0

    for p in profiles:
        key_email = (p.email or "").lower().strip()
        key_name = p.name.lower().strip()

        if key_email and key_email in seen_emails:
            merged += 1
            continue
        if key_name in seen_names:
            merged += 1
            continue

        if key_email:
            seen_emails[key_email] = p
        seen_names[key_name] = p
        unique.append(p)

    return unique, merged


def build_parse_summary(profiles: list[UnifiedCandidateProfile], merged: int, errors: list[str]) -> ParseSummary:
    by_source: dict[str, int] = {}
    for p in profiles:
        key = p.source_type.value
        by_source[key] = by_source.get(key, 0) + 1
    return ParseSummary(
        total=len(profiles),
        by_source=by_source,
        parse_errors=errors,
        duplicates_merged=merged,
    )


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _calc_completeness(skills: list, exp_years, location) -> float:
    score = 0.0
    if skills:
        score += 0.4
    if exp_years and float(exp_years or 0) > 0:
        score += 0.3
    if location:
        score += 0.2
    score += 0.1  # name always present
    return min(round(score, 2), 1.0)
