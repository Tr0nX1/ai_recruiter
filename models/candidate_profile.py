"""Pydantic: candidate profile (Agent 2)."""

from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class WorkExperience(BaseModel):
    company: str = ""
    role: str = ""
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    duration_months: Optional[int] = None
    responsibilities: List[str] = Field(default_factory=list)
    is_current: bool = False


class Education(BaseModel):
    degree: str = ""
    institution: str = ""
    field_of_study: Optional[str] = None
    year_completed: Optional[int] = None
    grade: Optional[str] = None


class CandidateProfile(BaseModel):
    name: str = ""
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin_url: Optional[str] = None
    total_years_exp: float = 0.0
    seniority_level: Literal["Intern", "Junior", "Mid", "Senior", "Lead", "Executive"] = "Mid"
    skills: List[str] = Field(default_factory=list)
    work_history: List[WorkExperience] = Field(default_factory=list)
    education: List[Education] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    languages: List[str] = Field(default_factory=list)
    source_file: Optional[str] = None
    raw_text_length: Optional[int] = None
