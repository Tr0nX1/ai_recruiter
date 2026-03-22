"""Structured output for Agent 1 (ingestion)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class IngestionOutput(BaseModel):
    filename: str = Field(description="Original file name or identifier")
    source_type: Literal["pdf", "docx", "txt", "linkedin", "gdrive", "upload"] = "upload"
    raw_text: str = Field(description="Full extracted plain text")
    page_count: int = 0
    file_size_kb: float = 0.0
    extraction_status: Literal["success", "partial", "failed"] = "success"
    error_message: str | None = None
