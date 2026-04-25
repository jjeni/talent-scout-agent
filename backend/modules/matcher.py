"""
Stage 2b: Matcher
Scores each candidate against the parsed JD using hybrid semantic + rule-based matching.
Match Score = Skills(40%) + Experience(25%) + Location(20%) + Education(15%)
"""
import logging
import os
from typing import Optional

import numpy as np
import google.generativeai as genai
from dotenv import load_dotenv

from models.jd_schema import JDSchema, SkillEntry
from models.candidate_schema import UnifiedCandidateProfile
from models.output_schema import MatchBreakdown

load_dotenv()
logger = logging.getLogger(__name__)

genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# Weights for sub-scores
WEIGHTS = {"skills": 0.40, "experience": 0.25, "location": 0.20, "education": 0.15}

# Similarity threshold for semantic skill matching
SEMANTIC_THRESHOLD = 0.80

# Embedding model available on this API key
EMBEDDING_MODEL = "models/gemini-embedding-001"


# ─── Embeddings ───────────────────────────────────────────────────────────────

def _get_embeddings(texts: list[str]) -> np.ndarray:
    """Get embeddings for a list of texts using Gemini embedding model.
    Processes each text individually to avoid batch format issues.
    """
    if not texts:
        return np.array([])
    embeddings = []
    for text in texts:
        result = genai.embed_content(
            model=EMBEDDING_MODEL,
            content=text,
            task_type="SEMANTIC_SIMILARITY",
        )
        embeddings.append(result["embedding"])
    return np.array(embeddings)


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Compute cosine similarity matrix between rows of a and b."""
    a_norm = a / (np.linalg.norm(a, axis=1, keepdims=True) + 1e-10)
    b_norm = b / (np.linalg.norm(b, axis=1, keepdims=True) + 1e-10)
    return a_norm @ b_norm.T


# ─── Skills Match (40%) ───────────────────────────────────────────────────────

def _normalize_skill(skill: str) -> str:
    return skill.lower().strip().replace(".", "").replace("-", "").replace(" ", "")


def _exact_skills_match(candidate_skills: list[str], jd_skills: list[SkillEntry]) -> dict:
    """Fast exact-match pass (normalized)."""
    candidate_normalized = {_normalize_skill(s) for s in candidate_skills}
    matches = {}
    for entry in jd_skills:
        jd_norm = _normalize_skill(entry.skill)
        if jd_norm in candidate_normalized:
            matches[entry.skill] = entry.importance
    return matches


def compute_skills_score(
    candidate_skills: list[str],
    jd: JDSchema,
) -> tuple[float, list[str]]:
    """
    Compute skills match score (0-100) using exact + semantic matching.
    Returns (score, matched_skills_list, missing_skills_gaps).
    """
    if not jd.required_skills:
        return 80.0, [], []

    required = jd.required_skills
    total_importance = sum(e.importance for e in required)
    if total_importance == 0:
        return 0.0, [], []

    # Pass 1: Exact match
    exact_matches = _exact_skills_match(candidate_skills, required)
    matched_score = sum(exact_matches.values())
    matched_skills = list(exact_matches.keys())

    # Pass 2: Semantic match for unmatched JD skills
    unmatched_jd = [e for e in required if e.skill not in exact_matches]

    if unmatched_jd and candidate_skills:
        try:
            cand_texts = candidate_skills
            jd_texts = [e.skill for e in unmatched_jd]

            cand_emb = _get_embeddings(cand_texts)
            jd_emb = _get_embeddings(jd_texts)

            if cand_emb.ndim == 2 and jd_emb.ndim == 2:
                sim_matrix = _cosine_similarity(jd_emb, cand_emb)  # [n_jd_skills x n_cand_skills]

                for i, jd_entry in enumerate(unmatched_jd):
                    best_sim = sim_matrix[i].max()
                    if best_sim >= SEMANTIC_THRESHOLD:
                        best_cand_idx = sim_matrix[i].argmax()
                        matched_score += jd_entry.importance * best_sim
                        matched_skills.append(
                            f"{jd_entry.skill} ≈ {candidate_skills[best_cand_idx]}"
                        )
        except Exception as e:
            logger.warning(f"Semantic skill matching error: {e}")

    # Identify Gaps
    gaps = []
    if unmatched_jd:
        for entry in unmatched_jd:
            # If not even semantically matched above
            if not any(entry.skill in s for s in matched_skills):
                 gaps.append(f"Missing Skill: {entry.skill}")

    # Nice-to-have bonus (up to 5 points)
    nice_bonus = 0.0
    candidate_normalized = {_normalize_skill(s) for s in candidate_skills}
    for nice_skill in jd.nice_to_have_skills:
        if _normalize_skill(nice_skill) in candidate_normalized:
            nice_bonus += 0.5
    nice_bonus = min(nice_bonus, 5.0)

    score = min((matched_score / total_importance) * 100 + nice_bonus, 100.0)
    return round(score, 1), matched_skills[:5], gaps[:3]


# ─── Experience Fit (25%) ─────────────────────────────────────────────────────

def compute_experience_score(candidate: UnifiedCandidateProfile, jd: JDSchema) -> tuple[float, str]:
    """Score 0-100 based on years of experience vs JD requirement."""
    exp = candidate.experience_years
    if not jd.experience:
        return 75.0, "No experience requirement specified"

    min_yrs = jd.experience.min_years or 0
    pref_yrs = jd.experience.preferred_years or min_yrs

    if exp < min_yrs * 0.7:
        score = 20.0
        reason = f"Under-experienced ({exp}y vs {min_yrs}y required)"
    elif exp < min_yrs:
        score = 55.0
        reason = f"Slightly below minimum ({exp}y vs {min_yrs}y)"
    elif exp <= pref_yrs * 1.5:
        score = 100.0
        reason = f"Strong experience match ({exp}y, ideal range {min_yrs}–{pref_yrs}y)"
    elif exp <= pref_yrs * 2.5:
        score = 80.0
        reason = f"Overqualified but experienced ({exp}y)"
    else:
        score = 60.0
        reason = f"Significantly overqualified ({exp}y)"

    return round(score, 1), reason


# ─── Location Fit (20%) ───────────────────────────────────────────────────────

def compute_location_score(candidate: UnifiedCandidateProfile, jd: JDSchema) -> tuple[float, str]:
    """Score based on location compatibility."""
    if not jd.location:
        return 90.0, "No location requirement"

    jd_type = (jd.location.type or "").lower()
    cand_loc = (candidate.location or "").lower()

    if jd_type == "remote":
        if "remote" in cand_loc or "flexible" in cand_loc:
            return 100.0, "Remote-ready candidate"
        if jd.location.constraint and "us timezone" in (jd.location.constraint or "").lower():
            tz_signals = ["us", "est", "cst", "mst", "pst", "america", "canada", "mexico"]
            if any(tz in cand_loc for tz in tz_signals):
                return 95.0, "US timezone compatible"
            return 65.0, "Non-US timezone, may have overlap issues"
        return 85.0, "Location compatible (remote role)"

    elif jd_type == "hybrid":
        jd_city = (jd.location.city or "").lower()
        if jd_city and jd_city in cand_loc:
            return 100.0, f"Local candidate in {jd.location.city}"
        if "remote" in cand_loc:
            return 60.0, "Hybrid role — remote candidate may need to relocate"
        return 50.0, "Location mismatch for hybrid role"

    else:  # On-site
        jd_city = (jd.location.city or "").lower()
        if jd_city and jd_city in cand_loc:
            return 100.0, f"Lives in {jd.location.city}"
        return 30.0, "On-site role — candidate not local"


# ─── Education Fit (15%) ──────────────────────────────────────────────────────

DEGREE_RANK = {
    "high school": 1, "associate's": 2, "associates": 2,
    "bachelor's": 3, "b.s.": 3, "b.sc": 3, "b.tech": 3, "b.e.": 3, "b.eng": 3, "b.a.": 3, "be": 3,
    "master's": 4, "m.s.": 4, "m.sc": 4, "m.tech": 4, "mba": 4, "m.eng": 4,
    "phd": 5, "ph.d": 5, "doctorate": 5,
}


def compute_education_score(candidate: UnifiedCandidateProfile, jd: JDSchema) -> tuple[float, str]:
    """Score education fit."""
    if not jd.education or not jd.education.degree_level:
        return 80.0, "No specific education requirement"

    if not candidate.education or not candidate.education.degree:
        return 50.0, "No education data available"

    jd_degree_lower = jd.education.degree_level.lower()
    cand_degree_lower = (candidate.education.degree or "").lower()

    jd_rank = DEGREE_RANK.get(jd_degree_lower, 3)
    cand_rank = DEGREE_RANK.get(cand_degree_lower, 3)

    if cand_rank >= jd_rank:
        score = 100.0
        reason = f"Education meets requirement ({candidate.education.degree})"
    elif jd.education.is_strict:
        score = 20.0
        reason = "Strict education requirement not met"
    else:
        score = 65.0
        reason = f"Education below preferred ({candidate.education.degree} vs {jd.education.degree_level})"

    return round(score, 1), reason


# ─── Hard Filters ─────────────────────────────────────────────────────────────

def apply_hard_filters(
    candidates: list[UnifiedCandidateProfile],
    jd: JDSchema,
) -> tuple[list[UnifiedCandidateProfile], list[dict]]:
    """
    Apply must-pass filters before soft scoring.
    Returns (passed, excluded_with_reasons).
    """
    passed = []
    excluded = []

    for c in candidates:
        reasons = []

        # Filter: Minimum experience
        if jd.experience and jd.experience.min_years:
            if c.experience_years < jd.experience.min_years * 0.6:
                reasons.append(
                    f"Insufficient experience: {c.experience_years}y < "
                    f"{jd.experience.min_years * 0.6:.1f}y (60% of minimum)"
                )

        # Filter: Strict education
        if jd.education and jd.education.is_strict and jd.education.degree_level:
            if c.education:
                cand_rank = DEGREE_RANK.get((c.education.degree or "").lower(), 0)
                jd_rank = DEGREE_RANK.get(jd.education.degree_level.lower(), 3)
                if cand_rank < jd_rank:
                    reasons.append(f"Strict education requirement not met")

        if reasons:
            excluded.append({"candidate": c.name, "id": c.id, "reasons": reasons})
        else:
            passed.append(c)

    logger.info(f"Hard filters: {len(passed)} passed, {len(excluded)} excluded")
    return passed, excluded


# ─── Full Match Score ─────────────────────────────────────────────────────────

def score_candidate(
    candidate: UnifiedCandidateProfile,
    jd: JDSchema,
) -> MatchBreakdown:
    """Compute full Match Score with all sub-dimensions."""
    skills_score, matched_skills, skill_gaps = compute_skills_score(candidate.skills, jd)
    exp_score, exp_reason = compute_experience_score(candidate, jd)
    loc_score, loc_reason = compute_location_score(candidate, jd)
    edu_score, edu_reason = compute_education_score(candidate, jd)

    total = (
        skills_score * WEIGHTS["skills"]
        + exp_score * WEIGHTS["experience"]
        + loc_score * WEIGHTS["location"]
        + edu_score * WEIGHTS["education"]
    )

    # Build Explainability Signals
    strengths = []
    if skills_score > 80: strengths.append("Core technical skills strongly aligned")
    if exp_score >= 100: strengths.append("Directly matches required experience depth")
    if loc_score >= 100: strengths.append(loc_reason)
    
    gaps = skill_gaps
    if exp_score < 70: gaps.append(exp_reason)
    if loc_score < 60: gaps.append(loc_reason)

    reasons = []
    if matched_skills:
        reasons.append(f"Matched: {', '.join(matched_skills[:2])}")
    reasons.append(exp_reason)
    if loc_score >= 80: reasons.append(loc_reason)

    return MatchBreakdown(
        skills_score=round(skills_score, 1),
        experience_score=round(exp_score, 1),
        location_score=round(loc_score, 1),
        education_score=round(edu_score, 1),
        total=round(total, 1),
        top_reasons=reasons[:3],
        strengths=strengths[:3],
        gaps=gaps[:3],
    )
