"""
Stage 4: Ranker
Combines Match Score + Interest Score, generates AI recruiter notes,
and produces the final ranked shortlist output.
"""
import logging
import os

import google.generativeai as genai
from dotenv import load_dotenv

from models.jd_schema import JDSchema
from models.candidate_schema import UnifiedCandidateProfile
from models.output_schema import (
    MatchBreakdown,
    InterestBreakdown,
    ConversationTranscript,
    ScoredCandidate,
    RankedEntry,
    ShortlistOutput,
)

load_dotenv()
logger = logging.getLogger(__name__)

genai.configure(api_key=os.environ["GEMINI_API_KEY"])

_model = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    generation_config={"temperature": 0.4, "max_output_tokens": 80},
)

DEFAULT_W_MATCH = 0.60
DEFAULT_W_INTEREST = 0.40


def compute_combined_score(
    match_score: float,
    interest_score: float,
    w_match: float = DEFAULT_W_MATCH,
    w_interest: float = DEFAULT_W_INTEREST,
) -> float:
    return round(w_match * match_score + w_interest * interest_score, 1)


def generate_recruiter_note(candidate: ScoredCandidate) -> str:
    """
    Generate a one-sentence AI recruiter note summarizing the recommendation.
    Falls back to a rule-based note if LLM fails.
    """
    interest_summary = candidate.interest_breakdown.summary if candidate.interest_breakdown else "Interest not assessed"
    top_reasons = candidate.match_breakdown.top_reasons[:2]

    prompt = f"""You are a senior technical recruiter. Write exactly ONE concise sentence (max 20 words)
summarizing this candidate's recommendation for a recruiter:

Candidate: {candidate.profile.name}
Match Score: {candidate.match_score}/100 — Top reasons: {', '.join(top_reasons)}
Interest Score: {candidate.interest_score}/100 — Summary: {interest_summary}
Combined Score: {candidate.combined_score}/100

Write only the sentence, no prefix, no quotes."""

    try:
        response = _model.generate_content(prompt)
        return response.text.strip().strip('"').strip("'")
    except Exception as e:
        logger.warning(f"Recruiter note generation failed: {e}")
        return _fallback_note(candidate)


def _fallback_note(c: ScoredCandidate) -> str:
    if c.combined_score >= 85:
        return f"Highly recommended — strong technical match and genuine interest."
    elif c.combined_score >= 70:
        return f"Good candidate with solid skills; worth a screening call."
    elif c.combined_score >= 55:
        return f"Moderate fit; review against other candidates before proceeding."
    else:
        return f"Below threshold — consider only if top candidates are unavailable."


def rank_candidates(
    scored: list[ScoredCandidate],
    jd: JDSchema,
    job_id: str,
    processing_time: float,
    excluded: list[dict],
    w_match: float = DEFAULT_W_MATCH,
    w_interest: float = DEFAULT_W_INTEREST,
) -> ShortlistOutput:
    """
    Sort candidates by combined score, generate recruiter notes, and build ShortlistOutput.
    """
    # Compute combined scores
    for c in scored:
        c.combined_score = compute_combined_score(c.match_score, c.interest_score, w_match, w_interest)

    sorted_candidates = sorted(scored, key=lambda x: x.combined_score, reverse=True)

    ranked_entries: list[RankedEntry] = []
    for i, c in enumerate(sorted_candidates):
        note = generate_recruiter_note(c)
        interest_summary = c.interest_breakdown.summary if c.interest_breakdown else "Not assessed"
        ranked_entries.append(RankedEntry(
            rank=i + 1,
            candidate_id=c.profile.id,
            candidate_name=c.profile.name,
            match_score=c.match_score,
            interest_score=c.interest_score,
            combined_score=c.combined_score,
            top_match_reasons=c.match_breakdown.top_reasons[:3],
            strengths=c.match_breakdown.strengths,
            gaps=c.match_breakdown.gaps,
            interest_summary=interest_summary,
            recruiter_note=note,
            source_type=c.profile.source_type.value,
            data_completeness=c.profile.data_completeness,
            key_signals=c.interest_breakdown.key_signals if c.interest_breakdown else [],
            red_flags=c.interest_breakdown.red_flags if c.interest_breakdown else [],
        ))

    avg_match = round(sum(c.match_score for c in scored) / max(len(scored), 1), 1)
    avg_interest = round(sum(c.interest_score for c in scored) / max(len(scored), 1), 1)
    avg_combined = round(sum(c.combined_score for c in scored) / max(len(scored), 1), 1)

    return ShortlistOutput(
        job_id=job_id,
        role_title=jd.role_title,
        total_evaluated=len(scored) + len(excluded),
        shortlisted_count=len(ranked_entries),
        avg_match_score=avg_match,
        avg_interest_score=avg_interest,
        avg_combined_score=avg_combined,
        processing_time_seconds=round(processing_time, 2),
        ranked_candidates=ranked_entries,
        excluded_candidates=excluded,
        weights={"match": w_match, "interest": w_interest},
    )
