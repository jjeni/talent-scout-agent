"""
Pydantic schemas for Job Description parsing output.
"""
from typing import Optional
from pydantic import BaseModel, Field


class SkillEntry(BaseModel):
    skill: str
    importance: float = Field(ge=0.0, le=1.0)


class LocationSchema(BaseModel):
    type: str  # "Remote" | "Hybrid" | "On-site"
    city: Optional[str] = None
    country: Optional[str] = None
    constraint: Optional[str] = None  # e.g. "US timezone preferred"


class ExperienceSchema(BaseModel):
    min_years: Optional[float] = None
    preferred_years: Optional[float] = None


class EducationRequirement(BaseModel):
    degree_level: Optional[str] = None  # "Bachelor's" | "Master's" | "PhD" | "Any"
    field: Optional[str] = None
    is_strict: Optional[bool] = False  # True = hard requirement, False = nice-to-have


class CompensationSchema(BaseModel):
    min: Optional[float] = None
    max: Optional[float] = None
    currency: str = "USD"
    equity: bool = False


class JDSchema(BaseModel):
    role_title: str
    seniority: Optional[str] = None          # "Junior" | "Mid" | "Senior" | "Staff" | "Lead"
    employment_type: Optional[str] = None    # "Full-time" | "Part-time" | "Contract"
    location: Optional[LocationSchema] = None
    experience: Optional[ExperienceSchema] = None
    required_skills: list[SkillEntry] = []
    nice_to_have_skills: list[str] = []
    education: Optional[EducationRequirement] = None
    compensation: Optional[CompensationSchema] = None
    urgency: Optional[str] = None            # "immediate" | "within_month" | "flexible"
    raw_text: Optional[str] = None
    confidence_flags: dict[str, float] = {}  # field → confidence 0-1
