"""Weighted score helper for Agent 4."""

from __future__ import annotations

from typing import Any

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class ScoringInput(BaseModel):
    skills_score: float = Field(ge=0, le=100)
    experience_score: float = Field(ge=0, le=100)
    education_score: float = Field(ge=0, le=100)
    culture_score: float = Field(ge=0, le=100)
    weights_skills: float = 0.40
    weights_experience: float = 0.30
    weights_education: float = 0.20
    weights_culture: float = 0.10


class ScoringCalculatorTool(BaseTool):
    name: str = "ScoringCalculatorTool"
    description: str = "Computes weighted overall score (0–100) from sub-scores and weights."
    args_schema: type[BaseModel] = ScoringInput

    def _run(
        self,
        skills_score: float,
        experience_score: float,
        education_score: float,
        culture_score: float,
        weights_skills: float = 0.40,
        weights_experience: float = 0.30,
        weights_education: float = 0.20,
        weights_culture: float = 0.10,
    ) -> dict[str, Any]:
        w = weights_skills + weights_experience + weights_education + weights_culture
        if w <= 0:
            w = 1.0
        overall = (
            skills_score * weights_skills
            + experience_score * weights_experience
            + education_score * weights_education
            + culture_score * weights_culture
        ) / w
        return {"overall_score": int(round(min(100, max(0, overall))))}
