"""Pydantic: scoring & evaluation (Agent 4)."""

from __future__ import annotations

from typing import List, Literal

from pydantic import BaseModel, Field


class CandidateEvaluation(BaseModel):
    overall_score: int = Field(ge=0, le=100, default=0)
    skills_match_pct: int = Field(ge=0, le=100, default=0)
    experience_score: int = Field(ge=0, le=100, default=0)
    education_score: int = Field(ge=0, le=100, default=0)

    recommendation: Literal["Shortlist", "Maybe", "Reject"] = "Maybe"
    seniority_level: Literal["Intern", "Junior", "Mid", "Senior", "Lead", "Executive"] = "Mid"

    summary: str = ""
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    opportunities: List[str] = Field(default_factory=list)

    skills_list: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)

    bias_flags: List[str] = Field(default_factory=list)
    pii_redacted: bool = False

    interview_questions: List[str] = Field(default_factory=list)
