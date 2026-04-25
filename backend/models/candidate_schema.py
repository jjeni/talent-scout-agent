"""
Unified candidate profile schema — all input modes normalize to this.
"""
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class InputType(str, Enum):
    CSV = "csv"
    JSON = "json"
    PDF = "pdf"
    DOCX = "docx"
    GITHUB = "github"
    LINKEDIN = "linkedin"
    MANUAL = "manual"


class EducationBlock(BaseModel):
    degree: Optional[str] = None      # "B.Tech" | "M.S." | "Ph.D"
    field: Optional[str] = None
    institution: Optional[str] = None
    year_graduated: Optional[int] = None


class UnifiedCandidateProfile(BaseModel):
    id: str
    name: str
    skills: list[str] = []
    experience_years: float = 0.0
    education: Optional[EducationBlock] = None
    location: Optional[str] = None
    email: Optional[str] = None
    source_url: Optional[str] = None
    source_type: InputType = InputType.MANUAL
    raw_text: Optional[str] = None
    data_completeness: float = Field(default=1.0, ge=0.0, le=1.0)
    current_title: Optional[str] = None
    github_username: Optional[str] = None
    linkedin_url: Optional[str] = None
    languages: list[str] = []          # From GitHub scraping
    repos_count: Optional[int] = None  # From GitHub scraping
    parse_errors: list[str] = []


class ParseSummary(BaseModel):
    total: int
    by_source: dict[str, int]
    parse_errors: list[str]
    duplicates_merged: int
