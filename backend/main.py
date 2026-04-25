"""
TalentScout FastAPI Backend
Main application entrypoint with all pipeline routes and SSE streaming.
"""
import asyncio
import json
import logging
import os
import time
import uuid
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

from models.candidate_schema import UnifiedCandidateProfile
from models.output_schema import (
    PipelineStatus,
    ShortlistOutput,
    ScoredCandidate,
    ConversationTranscript,
)
from modules.jd_parser import parse_jd
from modules.candidate_ingestor import (
    ingest_csv,
    ingest_json,
    ingest_resume_bytes,
    ingest_github_url,
    ingest_linkedin_url,
    ingest_from_default_dataset,
    deduplicate,
    build_parse_summary,
)
from modules.matcher import score_candidate, apply_hard_filters
from modules.conversation_agent import run_conversation
from modules.interest_scorer import score_interest, _fallback_breakdown
from modules.ranker import rank_candidates, compute_combined_score

from fastapi import Header, Query

async def get_api_key(
    x_gemini_api_key: Optional[str] = Header(None, alias="X-Gemini-API-Key"),
    api_key: Optional[str] = Query(None)
) -> Optional[str]:
    """Retrieves the Gemini API key from either the custom header or query parameters."""
    return x_gemini_api_key or api_key

# ─── App Setup ────────────────────────────────────────────────────────────────

app = FastAPI(
    title="TalentScout AI API",
    description="AI-Powered Talent Scouting & Engagement Agent",
    version="1.0.0",
)

CORS_ORIGINS = [
    "http://localhost:3000",
    "https://hr-scout-agent.vercel.app",
    "https://hr-scout-agent.vercel.app/",
    "*"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,  # MUST be False if using "*" in origins with most browsers
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request, call_next):
    logger.info(f"Incoming request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response

# In-memory job store (replace with Redis/DB for production)
_jobs: dict[str, dict] = {}
_job_updates: dict[str, asyncio.Queue] = {}

TOP_N = int(os.getenv("TOP_N_CANDIDATES", "10"))
W_MATCH = float(os.getenv("MATCH_WEIGHT", "0.6"))
W_INTEREST = float(os.getenv("INTEREST_WEIGHT", "0.4"))


# ─── Request / Response Models ────────────────────────────────────────────────

class JDParseRequest(BaseModel):
    jd_text: str
    provider: str = "gemini"
    model: str = "gemini-2.5-flash-lite"

class PipelineRunRequest(BaseModel):
    jd_text: str
    job_id: Optional[str] = None
    use_default_dataset: bool = True
    top_n: int = 10
    w_match: float = 0.6
    w_interest: float = 0.4
    candidate_urls: Optional[list[str]] = None
    provider: str = "gemini"
    model: str = "gemini-2.5-flash-lite"


# ─── Helper: SSE Emitter ─────────────────────────────────────────────────────

async def _emit(job_id: str, status: PipelineStatus):
    if job_id in _job_updates:
        await _job_updates[job_id].put(status.model_dump_json())
    _jobs[job_id]["last_status"] = status.model_dump()


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {"status": "TalentScout API is running", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/api/parse-jd")
async def api_parse_jd(request: JDParseRequest, user_key: Optional[str] = Header(None, alias="X-Gemini-API-Key")):
    """Parse a raw job description into structured JSON."""
    try:
        jd = await parse_jd(request.jd_text, api_key=user_key, provider=request.provider, model=request.model)
        return jd.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ingest-candidates")
async def api_ingest_candidates(
    files: list[UploadFile] = File(default=[]),
    urls: str = Form(default=""),
    use_default: bool = Form(default=True),
):
    """
    Ingest candidates from uploaded files (CSV/JSON/PDF/DOCX) and/or URLs.
    Returns a summary + list of parsed profiles.
    """
    all_profiles: list[UnifiedCandidateProfile] = []
    errors: list[str] = []

    # Load default dataset if requested
    if use_default:
        defaults = await ingest_from_default_dataset()
        all_profiles.extend(defaults)

    # Process uploaded files
    for f in files:
        try:
            content = await f.read()
            filename = f.filename or ""
            if filename.endswith(".csv"):
                all_profiles.extend(ingest_csv(content.decode("utf-8", errors="ignore")))
            elif filename.endswith(".json"):
                all_profiles.extend(ingest_json(content.decode("utf-8", errors="ignore")))
            elif filename.endswith((".pdf", ".docx")):
                profile = await ingest_resume_bytes(content, filename)
                all_profiles.append(profile)
        except Exception as e:
            errors.append(f"{f.filename}: {e}")
            logger.error(f"File ingest error ({f.filename}): {e}")

    # Process URLs
    url_list = [u.strip() for u in urls.splitlines() if u.strip()]
    for url in url_list:
        try:
            if "github.com" in url:
                profile = await ingest_github_url(url)
            elif "linkedin.com" in url:
                profile = await ingest_linkedin_url(url)
            else:
                errors.append(f"Unsupported URL: {url}")
                continue
            all_profiles.append(profile)
        except Exception as e:
            errors.append(f"{url}: {e}")

    # Deduplicate
    unique_profiles, merged_count = deduplicate(all_profiles)
    summary = build_parse_summary(unique_profiles, merged_count, errors)

    return {
        "summary": summary.model_dump(),
        "profiles": [p.model_dump() for p in unique_profiles],
    }

async def _ingest_with_key(files, urls, use_default, api_key):
    # Internal helper for pipeline tasks
    all_profiles = []
    if use_default:
        all_profiles.extend(await ingest_from_default_dataset())
    
    for f in files:
        # Note: In the pipeline task, files are already pre-loaded into jobs dict or memory
        pass

    return all_profiles


@app.post("/api/start-pipeline")
async def api_start_pipeline(request: PipelineRunRequest, user_key: Optional[str] = Header(None, alias="X-Gemini-API-Key")):
    """
    Start the full 4-stage pipeline asynchronously.
    Returns a job_id to poll for status via SSE.
    """
    job_id = request.job_id or str(uuid.uuid4())
    _jobs[job_id] = {
        "status": "started", 
        "result": None, 
        "api_key": user_key, 
        "provider": request.provider,
        "model": request.model
    }
    _job_updates[job_id] = asyncio.Queue()

    asyncio.create_task(_run_pipeline_task(job_id, request))
    return {"job_id": job_id, "status": "started"}


@app.post("/api/start-pipeline-with-files")
async def api_start_pipeline_with_files(
    jd_text: str = Form(...),
    job_id: str = Form(default=""),
    use_default_dataset: bool = Form(default=True),
    top_n: int = Form(default=10),
    w_match: float = Form(default=0.6),
    w_interest: float = Form(default=0.4),
    candidate_urls: str = Form(default=""),
    files: list[UploadFile] = File(default=[]),
    user_key: Optional[str] = Header(None, alias="X-Gemini-API-Key"),
    provider: str = Form(default="gemini"),
    model: str = Form(default="gemini-2.5-flash-lite"),
):
    """
    Combined multipart endpoint — upload resumes/CSV/JSON alongside JD text.
    """
    fid = job_id.strip() or f"job_{uuid.uuid4().hex[:10]}"
    _jobs[fid] = {
        "status": "started", 
        "result": None, 
        "extra_profiles": [], 
        "api_key": user_key, 
        "provider": provider,
        "model": model
    }
    _job_updates[fid] = asyncio.Queue()

    # Pre-ingest uploaded files so they're available inside the pipeline task
    extra_profiles: list[UnifiedCandidateProfile] = []
    for f in files:
        try:
            content = await f.read()
            filename = f.filename or ""
            if filename.endswith(".csv"):
                extra_profiles.extend(ingest_csv(content.decode("utf-8", errors="ignore")))
            elif filename.endswith(".json"):
                extra_profiles.extend(ingest_json(content.decode("utf-8", errors="ignore")))
            elif filename.endswith((".pdf", ".docx")):
                profile = await ingest_resume_bytes(content, filename, api_key=user_key, provider=provider)
                extra_profiles.append(profile)
        except Exception as e:
            logger.warning(f"File pre-ingest error ({f.filename}): {e}")

    _jobs[fid]["extra_profiles"] = extra_profiles
    logger.info(f"Pre-ingested {len(extra_profiles)} profiles from {len(files)} files")

    url_list = [u.strip() for u in candidate_urls.splitlines() if u.strip()]
    request = PipelineRunRequest(
        job_id=fid,
        jd_text=jd_text,
        candidate_urls=url_list,
        use_default_dataset=use_default_dataset,
        top_n=top_n,
        w_match=w_match,
        w_interest=w_interest,
        provider=provider,
        model=model,
    )
    asyncio.create_task(_run_pipeline_task(fid, request))
    return {"job_id": fid, "status": "started", "files_ingested": len(extra_profiles)}


@app.get("/api/pipeline/status/{job_id}")
async def api_pipeline_status(job_id: str):
    """SSE stream for live pipeline progress updates."""
    if job_id not in _jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    async def event_stream():
        queue = _job_updates.get(job_id)
        if not queue:
            yield f"data: {json.dumps({'stage': 'done', 'progress': 100})}\n\n"
            return

        timeout = 600  # 10 min max
        start = time.time()
        while time.time() - start < timeout:
            try:
                msg = await asyncio.wait_for(queue.get(), timeout=2.0)
                yield f"data: {msg}\n\n"
                data = json.loads(msg)
                if data.get("stage") in ("done", "error"):
                    break
            except asyncio.TimeoutError:
                yield f": heartbeat\n\n"  # SSE keep-alive

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.get("/api/shortlist/{job_id}")
async def api_get_shortlist(job_id: str):
    """Retrieve the completed ranked shortlist for a job."""
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if not job.get("result"):
        raise HTTPException(status_code=202, detail="Pipeline still running")
    return job["result"]


@app.get("/api/transcript/{job_id}/{candidate_id}")
async def api_get_transcript(job_id: str, candidate_id: str):
    """Get the full conversation transcript for a specific candidate."""
    job = _jobs.get(job_id)
    if not job or not job.get("transcripts"):
        raise HTTPException(status_code=404, detail="Transcript not found")
    transcript = job["transcripts"].get(candidate_id)
    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript not found for this candidate")
    return transcript


@app.get("/api/scored-candidates/{job_id}")
async def api_get_scored_candidates(job_id: str):
    """Get the full scored candidate data including sub-scores."""
    job = _jobs.get(job_id)
    if not job or not job.get("scored_candidates"):
        raise HTTPException(status_code=404, detail="Scored candidates not found")
    return job["scored_candidates"]


@app.post("/api/quick-run")
async def api_quick_run(request: PipelineRunRequest):
    """
    Synchronous pipeline run — blocks until complete.
    Use for testing/demo with small candidate sets.
    """
    job_id = request.job_id or str(uuid.uuid4())
    _jobs[job_id] = {"status": "started", "result": None}
    _job_updates[job_id] = asyncio.Queue()

    await _run_pipeline_task(job_id, request)
    return _jobs[job_id].get("result", {"error": "Pipeline failed"})


# ─── Pipeline Task ────────────────────────────────────────────────────────────

async def _run_pipeline_task(job_id: str, request: PipelineRunRequest):
    """Main pipeline execution task."""
    start_time = time.time()
    transcripts: dict[str, dict] = {}
    scored_candidates: list[dict] = []

    try:
        # ── Stage 1: Parse JD ────────────────────────────────────────────────
        api_key = _jobs[job_id].get("api_key")
        provider = _jobs[job_id].get("provider", "gemini")
        model_override = _jobs[job_id].get("model")
        await _emit(job_id, PipelineStatus(
            job_id=job_id, stage="parsing_jd",
            progress=5, message="Parsing job description..."
        ))
        jd = await parse_jd(request.jd_text, api_key=api_key, provider=provider, model=model_override)
        await _emit(job_id, PipelineStatus(
            job_id=job_id, stage="parsing_jd",
            progress=15, message=f"JD parsed: '{jd.role_title}' | {len(jd.required_skills)} required skills"
        ))

        # ── Stage 2a: Load candidates ─────────────────────────────────────────
        await _emit(job_id, PipelineStatus(
            job_id=job_id, stage="ingesting",
            progress=20, message="Loading candidate profiles..."
        ))

        all_profiles: list[UnifiedCandidateProfile] = []

        # Load pre-ingested file profiles (from /api/start-pipeline-with-files)
        extra_profiles = _jobs[job_id].get("extra_profiles", [])
        if extra_profiles:
            all_profiles.extend(extra_profiles)
            logger.info(f"Loaded {len(extra_profiles)} pre-ingested file profiles")

        if request.use_default_dataset:
            all_profiles.extend(await ingest_from_default_dataset())

        for url in request.candidate_urls:
            try:
                if "github.com" in url:
                    all_profiles.append(await ingest_github_url(url))
                elif "linkedin.com" in url:
                    all_profiles.append(await ingest_linkedin_url(url))
            except Exception as e:
                logger.warning(f"URL ingest failed ({url}): {e}")

        unique_profiles, _ = deduplicate(all_profiles)
        file_note = f" + {len(extra_profiles)} from uploads" if extra_profiles else ""
        await _emit(job_id, PipelineStatus(
            job_id=job_id, stage="ingesting",
            progress=30, message=f"Loaded {len(unique_profiles)} unique candidates{file_note}"
        ))

        # ── Stage 2b: Hard filters + Match Scoring ────────────────────────────
        await _emit(job_id, PipelineStatus(
            job_id=job_id, stage="matching",
            progress=35, message="Applying hard filters and computing match scores..."
        ))

        passed, excluded = apply_hard_filters(unique_profiles, jd)
        scored: list[ScoredCandidate] = []

        for i, candidate in enumerate(passed):
            match_breakdown = score_candidate(candidate, jd, api_key=api_key)
            scored.append(ScoredCandidate(
                profile=candidate,
                match_score=match_breakdown.total,
                match_breakdown=match_breakdown,
                interest_score=0.0,
                interest_breakdown=_fallback_breakdown("Pending conversation stage"),
                combined_score=0.0,
            ))
            progress = 35 + int((i + 1) / len(passed) * 20)
            await _emit(job_id, PipelineStatus(
                job_id=job_id, stage="matching",
                progress=progress,
                current_candidate=candidate.name,
                message=f"Matched {i+1}/{len(passed)}: {candidate.name} → {match_breakdown.total:.0f}/100"
            ))

        # Sort by match score, take top-N for conversation stage
        scored.sort(key=lambda x: x.match_score, reverse=True)
        top_n = min(request.top_n, len(scored))
        shortlisted_for_convo = scored[:top_n]
        remaining = scored[top_n:]

        # Add neutral interest score for non-conversed candidates (already have fallback from above)
        for c in remaining:
            c.interest_score = 0.0
            c.interest_breakdown = _fallback_breakdown("Outside top-N — not contacted")

        await _emit(job_id, PipelineStatus(
            job_id=job_id, stage="matching",
            progress=55,
            message=f"Top {top_n} candidates selected for conversation stage"
        ))

        # ── Stage 3: Conversation + Interest Scoring ──────────────────────────
        model_override = _jobs[job_id].get("model")
        for i, cand in enumerate(shortlisted_for_convo):
            await _emit(job_id, PipelineStatus(
                job_id=job_id, stage="conversing",
                progress=55 + int((i / top_n) * 30),
                current_candidate=cand.profile.name,
                message=f"Conversing with {cand.profile.name} ({i+1}/{top_n})..."
            ))

            try:
                transcript = await run_conversation(cand.profile, jd, api_key=api_key, provider=provider, model=model_override)
                interest_breakdown = await score_interest(transcript, api_key=api_key, provider=provider, model=model_override)

                cand.transcript = transcript
                cand.interest_score = interest_breakdown.total
                cand.interest_breakdown = interest_breakdown
                cand.combined_score = compute_combined_score(
                    cand.match_score, cand.interest_score, request.w_match, request.w_interest
                )
                transcripts[cand.profile.id] = transcript.model_dump()
            except Exception as conv_err:
                logger.warning(f"Conversation failed for {cand.profile.name}: {conv_err}")
                cand.interest_score = 0.0
                cand.interest_breakdown = _fallback_breakdown(f"Conversation error: {conv_err}")
                cand.combined_score = compute_combined_score(
                    cand.match_score, 0.0, request.w_match, request.w_interest
                )

            scored_candidates.append(cand.model_dump())

        # ── Stage 4: Rank ─────────────────────────────────────────────────────
        await _emit(job_id, PipelineStatus(
            job_id=job_id, stage="ranking",
            progress=90, message="Building ranked shortlist..."
        ))

        all_scored = shortlisted_for_convo + remaining
        processing_time = time.time() - start_time

        shortlist = rank_candidates(
            all_scored, jd, job_id, processing_time, excluded,
            request.w_match, request.w_interest
        )

        result = shortlist.model_dump()
        _jobs[job_id]["result"] = result
        _jobs[job_id]["transcripts"] = transcripts
        _jobs[job_id]["scored_candidates"] = scored_candidates

        await _emit(job_id, PipelineStatus(
            job_id=job_id, stage="done",
            progress=100,
            message=f"Pipeline complete! {len(shortlist.ranked_candidates)} candidates ranked in {processing_time:.1f}s"
        ))

    except Exception as e:
        logger.error(f"Pipeline error (job={job_id}): {e}", exc_info=True)
        await _emit(job_id, PipelineStatus(
            job_id=job_id, stage="error",
            progress=0, message="Pipeline failed", error=str(e)
        ))
