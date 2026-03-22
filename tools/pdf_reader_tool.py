"""PDF text extraction via PyMuPDF (fitz)."""

from __future__ import annotations

import os

import fitz  # PyMuPDF
from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class PDFReaderInput(BaseModel):
    file_path: str = Field(description="Absolute or relative path to a .pdf file")


class PDFReaderTool(BaseTool):
    name: str = "PDFReaderTool"
    description: str = "Reads a PDF file and extracts all text content from every page."
    args_schema: type[BaseModel] = PDFReaderInput

    def _run(self, file_path: str) -> dict:
        if not os.path.isfile(file_path):
            return {
                "raw_text": "",
                "page_count": 0,
                "extraction_status": "failed",
                "error_message": f"File not found: {file_path}",
            }
        try:
            doc = fitz.open(file_path)
            try:
                text = ""
                for page in doc:
                    text += page.get_text()
                n_pages = len(doc)
            finally:
                doc.close()
            stripped = text.strip()
            return {
                "raw_text": stripped,
                "page_count": n_pages,
                "extraction_status": "success" if stripped else "partial",
                "error_message": None,
            }
        except Exception as e:  # noqa: BLE001
            return {
                "raw_text": "",
                "page_count": 0,
                "extraction_status": "failed",
                "error_message": str(e),
            }
