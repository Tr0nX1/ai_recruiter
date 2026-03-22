"""Confirmation output for Agent 5 / report task."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ReportConfirmation(BaseModel):
    row_number: int = 0
    excel_path: str = ""
    json_backup_path: str = ""
    notification_sent: bool = False
    interview_questions: list[str] = Field(default_factory=list)
    recruiter_summary: str = ""
