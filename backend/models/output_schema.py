"""
Output schemas for scored candidates, shortlist entries, and final ranked output.
"""
from typing import Optional
from pydantic import BaseModel
from .candidate_schema import UnifiedCandidateProfile


class MatchBreakdown(BaseModel):
    skills_score: float       # 0-100, weight 40%
    experience_score: float   # 0-100, weight 25%
    location_score: float     # 0-100, weight 20%
    education_score: float    # 0-100, weight 15%
    total: float              # Weighted sum
    top_reasons: list[str]    # Top 3 human-readable reasons
    strengths: list[str] = [] # Specific asset callouts
    gaps: list[str] = []      # Missing requirements or concerns
    exclusion_reasons: list[str] = []  # Why candidate was filtered (if any)


class InterestBreakdown(BaseModel):
    stated_interest: float    # 0-100, weight 35%
    engagement_depth: float   # 0-100, weight 25%
    availability: float       # 0-100, weight 20%
    sentiment: float          # 0-100, weight 20%
    total: float              # Weighted sum
    key_signals: list[str]    # Notable quotes/signals from conversation
    red_flags: list[str]      # Concerning signals
    summary: str              # One-sentence summary


class ConversationTurn(BaseModel):
    turn: int
    agent: str
    candidate: str


class ConversationTranscript(BaseModel):
    candidate_id: str
    turns: list[ConversationTurn]
    total_turns: int
    exit_reason: Optional[str] = None  # "natural_end" | "declined" | "max_turns"


class ScoredCandidate(BaseModel):
    profile: UnifiedCandidateProfile
    match_score: float
    match_breakdown: MatchBreakdown
    interest_score: float
    interest_breakdown: Optional[InterestBreakdown] = None
    combined_score: float
    transcript: Optional[ConversationTranscript] = None


class RankedEntry(BaseModel):
    rank: int
    candidate_id: str
    candidate_name: str
    match_score: float
    interest_score: float
    combined_score: float
    top_match_reasons: list[str]
    strengths: list[str] = []
    gaps: list[str] = []
    interest_summary: str
    recruiter_note: str
    source_type: str
    data_completeness: float
    key_signals: list[str] = []
    red_flags: list[str] = []


class ShortlistOutput(BaseModel):
    job_id: str
    role_title: str
    total_evaluated: int
    shortlisted_count: int
    avg_match_score: float
    avg_interest_score: float
    avg_combined_score: float
    processing_time_seconds: float
    ranked_candidates: list[RankedEntry]
    excluded_candidates: list[dict]   # Candidates that failed hard filters
    weights: dict[str, float]         # {"match": 0.6, "interest": 0.4}


class PipelineStatus(BaseModel):
    job_id: str
    stage: str        # "parsing_jd" | "ingesting" | "matching" | "conversing" | "ranking" | "done"
    progress: float   # 0-100
    current_candidate: Optional[str] = None
    message: str
    error: Optional[str] = None
