"""Pydantic: job description analysis (Agent 3)."""

from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class JobRequirements(BaseModel):
    role_title: str = ""
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    min_years_experience: float = 0.0
    education_requirement: str = ""
    seniority_target: str = ""
    key_responsibilities: List[str] = Field(default_factory=list)
    industry: Optional[str] = None
    scoring_weights: Dict[str, float] = Field(
        default_factory=lambda: {
            "skills": 0.40,
            "experience": 0.30,
            "education": 0.20,
            "culture_fit": 0.10,
        }
    )
