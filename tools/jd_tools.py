"""JD parsing helpers for Agent 3."""

from __future__ import annotations

import re
from typing import Any

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class JDParserInput(BaseModel):
    jd_text: str = Field(description="Full job description text")


class JDParserTool(BaseTool):
    name: str = "JDParserTool"
    description: str = "Extracts bullet-like lines and keyword tokens from a JD (heuristic)."
    args_schema: type[BaseModel] = JDParserInput

    def _run(self, jd_text: str) -> dict[str, Any]:
        lines = [ln.strip() for ln in jd_text.splitlines() if ln.strip()]
        bullets = [ln for ln in lines if ln[:1] in "-•*" or re.match(r"^\d+[\).]", ln)]
        return {"line_count": len(lines), "bullet_candidates": bullets[:40]}


class IndustryInput(BaseModel):
    role_title: str = ""
    jd_text: str = ""


class IndustryContextTool(BaseTool):
    name: str = "IndustryContextTool"
    description: str = "Returns coarse industry hint from JD keywords (heuristic)."
    args_schema: type[BaseModel] = IndustryInput

    def _run(self, role_title: str = "", jd_text: str = "") -> dict[str, str]:
        text = f"{role_title}\n{jd_text}".lower()
        if any(k in text for k in ("software", "engineer", "developer", "api", "cloud")):
            return {"industry": "technology"}
        if any(k in text for k in ("bank", "finance", "account", "audit", "cpa")):
            return {"industry": "finance"}
        if any(k in text for k in ("marketing", "brand", "seo", "growth")):
            return {"industry": "marketing"}
        return {"industry": "general"}
