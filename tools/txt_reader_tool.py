"""Plain text file reader."""

from __future__ import annotations

import os

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class TXTReaderInput(BaseModel):
    file_path: str = Field(description="Path to a .txt file")


class TXTReaderTool(BaseTool):
    name: str = "TXTReaderTool"
    description: str = "Reads a UTF-8 text file and returns its contents."
    args_schema: type[BaseModel] = TXTReaderInput

    def _run(self, file_path: str) -> dict:
        if not os.path.isfile(file_path):
            return {
                "raw_text": "",
                "page_count": 0,
                "extraction_status": "failed",
                "error_message": f"File not found: {file_path}",
            }
        try:
            with open(file_path, encoding="utf-8", errors="replace") as f:
                raw = f.read()
            return {
                "raw_text": raw,
                "page_count": 1,
                "extraction_status": "success" if raw.strip() else "partial",
                "error_message": None,
            }
        except OSError as e:
            return {
                "raw_text": "",
                "page_count": 0,
                "extraction_status": "failed",
                "error_message": str(e),
            }
