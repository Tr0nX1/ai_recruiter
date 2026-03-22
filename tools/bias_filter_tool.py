"""PII / protected-class pattern scan (blueprint-style)."""

from __future__ import annotations

import re

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

PII_PATTERNS = {
    "age": r"\b(age[d]?\s*:?\s*\d{2}|born\s+in\s+\d{4}|\d{2}\s*years\s*old)\b",
    "gender": r"\b(male|female|he/him|she/her|mr\.|mrs\.|miss)\b",
    "photo": r"\b(photo|photograph|picture|image\s+attached)\b",
    "religion": r"\b(hindu|muslim|christian|sikh|jain|buddhist)\b",
    "marital": r"\b(married|single|divorced|widowed|unmarried)\b",
}


class BiasFilterInput(BaseModel):
    resume_text: str = Field(description="Raw resume text to scan")


class BiasFilterTool(BaseTool):
    name: str = "BiasFilterTool"
    description: str = "Scans resume text for PII and protected-class signals. Returns flags list."
    args_schema: type[BaseModel] = BiasFilterInput

    def _run(self, resume_text: str) -> dict:
        flags: list[str] = []
        redacted_text = resume_text
        for pii_type, pattern in PII_PATTERNS.items():
            matches = re.findall(pattern, resume_text, re.IGNORECASE)
            if matches:
                flags.append(f"{pii_type}: {matches[:5]}")
                redacted_text = re.sub(
                    pattern,
                    f"[{pii_type.upper()} REDACTED]",
                    redacted_text,
                    flags=re.IGNORECASE,
                )
        return {"bias_flags": flags, "redacted_text": redacted_text, "flag_count": len(flags)}
