"""Email stub (integrate later)."""

from __future__ import annotations

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class EmailInput(BaseModel):
    subject: str = ""
    body: str = ""


class EmailTool(BaseTool):
    name: str = "EmailTool"
    description: str = "Placeholder for outbound email notifications (not implemented)."
    args_schema: type[BaseModel] = EmailInput

    def _run(self, subject: str = "", body: str = "") -> dict:
        return {"sent": False, "note": "Email integration not configured", "subject": subject}
