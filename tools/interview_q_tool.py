"""Interview question helpers — template pack + topic STAR (Phase 4)."""

from __future__ import annotations

import json

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class InterviewQInput(BaseModel):
    topic: str = Field(description="Skill gap or theme to target")


class InterviewQGenTool(BaseTool):
    name: str = "InterviewQGenTool"
    description: str = (
        "Returns a STAR-format behavioural question for a single topic (skill gap, risk, or strength)."
    )
    args_schema: type[BaseModel] = InterviewQInput

    def _run(self, topic: str) -> str:
        return (
            f"Tell me about a time you had to deliver results while working with {topic}. "
            "What was the situation, what did you do, and what was the outcome?"
        )


class InterviewPackInput(BaseModel):
    role_title: str = Field(description="Role being hired for")
    top_gap: str = Field(description="Biggest skill or experience gap vs JD")
    top_strength: str = Field(description="Strongest relevant strength from resume")
    risk_theme: str = Field(description="One risk to probe (e.g. tenure, gap)")
    opportunity_theme: str = Field(description="One growth or upside theme")


class InterviewPackTool(BaseTool):
    name: str = "InterviewPackTool"
    description: str = (
        "Builds five structured interview questions (JSON array of strings) tailored to "
        "gap, strength, risk, opportunity, and role — without inventing resume facts."
    )
    args_schema: type[BaseModel] = InterviewPackInput

    def _run(
        self,
        role_title: str,
        top_gap: str,
        top_strength: str,
        risk_theme: str,
        opportunity_theme: str,
    ) -> str:
        qs = [
            f"[Technical gap] The role needs strong capability in: {top_gap}. "
            "Walk me through a project where you had to ramp up on something similar — "
            "what did you learn first, and how did you validate your work?",
            f"[Depth] For this {role_title} position, your background shows strength in: {top_strength}. "
            "What was the hardest trade-off you made on that work, and what would you do differently?",
            f"[Impact] Describe a measurable outcome you owned that is most relevant to this role. "
            "How did you define success and what numbers changed?",
            f"[Risk] I want to understand: {risk_theme}. What happened, and what context should I know?",
            f"[Growth] We see upside in: {opportunity_theme}. How would you leverage that in the first 90 days?",
        ]
        return json.dumps(qs, ensure_ascii=False)


def generate_interview_pack_dict(
    *,
    role_title: str,
    top_gap: str,
    top_strength: str,
    risk_theme: str,
    opportunity_theme: str,
) -> list[str]:
    """Programmatic access (same strings as InterviewPackTool)."""
    t = InterviewPackTool()
    raw = t._run(  # noqa: SLF001
        role_title=role_title,
        top_gap=top_gap,
        top_strength=top_strength,
        risk_theme=risk_theme,
        opportunity_theme=opportunity_theme,
    )
    return json.loads(raw)
