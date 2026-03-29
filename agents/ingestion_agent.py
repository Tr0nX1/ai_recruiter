"""Agent 1 — resume ingestion."""

from __future__ import annotations

from crewai import Agent

from config import FAST_MODELS
from tools.apify_tool import ApifyTool
from tools.docx_reader_tool import DOCXReaderTool
from tools.gdrive_tool import GDriveTool
from tools.pdf_reader_tool import PDFReaderTool
from tools.txt_reader_tool import TXTReaderTool

ingestion_agent = Agent(
    role="Senior Document Processing Specialist",
    goal=(
        "Read every uploaded resume regardless of file format — PDF, DOCX, or TXT — "
        "and extract clean, complete raw text. Handle encoding issues, multi-page documents, "
        "and malformed files gracefully. Never lose data silently."
    ),
    backstory=(
        "You are an expert document parser with 15 years of experience processing "
        "millions of documents across every industry and format. You understand PDF "
        "encoding, Word document structure, and text extraction quirks. When you cannot "
        "extract a file, you say so explicitly rather than returning garbage data."
    ),
    tools=[
        PDFReaderTool(),
        DOCXReaderTool(),
        TXTReaderTool(),
        GDriveTool(),
        ApifyTool(),
    ],
    llm=FAST_MODELS[0],
    verbose=True,
    allow_delegation=False,
    max_iter=5,
    max_retry_limit=2,
)
