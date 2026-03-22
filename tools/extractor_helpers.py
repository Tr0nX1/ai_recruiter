"""Lightweight helpers for Agent 2 (normalisation / dates)."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class NormInput(BaseModel):
    items: list[str] = Field(description="List of skill or title strings to normalise")


class NormalisationTool(BaseTool):
    name: str = "NormalisationTool"
    description: str = "Normalises casing and trims whitespace on a list of strings."
    args_schema: type[BaseModel] = NormInput

    def _run(self, items: list[str]) -> list[str]:
        return sorted({i.strip().title() for i in items if i and i.strip()})


class SkillsTaxonomyInput(BaseModel):
    skills: list[str] = Field(description="Raw skills from resume")


class SkillsTaxonomyTool(BaseTool):
    name: str = "SkillsTaxonomyTool"
    description: str = "Deduplicates skills and removes obvious noise tokens."
    args_schema: type[BaseModel] = SkillsTaxonomyInput

    def _run(self, skills: list[str]) -> list[str]:
        noise = {"and", "or", "the", "a", "an"}
        out: list[str] = []
        for s in skills:
            t = s.strip()
            if len(t) < 2 or t.lower() in noise:
                continue
            if t not in out:
                out.append(t)
        return out


class DateCalcInput(BaseModel):
    text_block: str = Field(description="Work history text containing dates")


class DateCalculatorTool(BaseTool):
    name: str = "DateCalculatorTool"
    description: str = "Extracts year mentions from a text block (coarse helper)."
    args_schema: type[BaseModel] = DateCalcInput

    def _run(self, text_block: str) -> dict[str, Any]:
        years = [int(y) for y in re.findall(r"\b(19\d{2}|20\d{2})\b", text_block)]
        if not years:
            return {"years_found": [], "span_years": None}
        span = max(years) - min(years)
        return {"years_found": years[:20], "span_years": span}
