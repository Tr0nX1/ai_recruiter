"""Task 1 — ingestion."""

from __future__ import annotations

from crewai import Task

from agents.ingestion_agent import ingestion_agent
from models.ingestion import IngestionOutput

ingestion_task = Task(
    name="ingestion",
    description=(
        "Read the resume from the provided input path. "
        "Input resume_path: {resume_path}. "
        "Use PDFReaderTool for .pdf, DOCXReaderTool for .docx, TXTReaderTool for .txt. "
        "Extract ALL text including headers and tables. "
        "Set filename from the path, file_size_kb using OS file size, page_count from the tool. "
        "Return a complete IngestionOutput."
    ),
    expected_output="A validated IngestionOutput with raw_text and metadata.",
    agent=ingestion_agent,
    output_pydantic=IngestionOutput,
    output_file="outputs/temp_ingestion.json",
)
