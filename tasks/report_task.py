"""Task 5 — report."""

from __future__ import annotations

from crewai import Task

from agents.report_writer_agent import report_writer_agent
from models.report import ReportConfirmation
from tasks.extraction_task import extraction_task
from tasks.ingestion_task import ingestion_task
from tasks.jd_analysis_task import jd_analysis_task
from tasks.scoring_task import scoring_task

report_task = Task(
    name="report",
    description=(
        "Using outputs from prior tasks: produce a 2–3 sentence recruiter_summary, "
        "confirm five interview_questions (use or refine those in CandidateEvaluation). "
        "If recommendation is Shortlist, send SlackNotifyTool with a short alert. "
        "Optionally call ExcelWriterTool with a JSON string of row keys matching tools/excel_writer_tool. "
        "Return ReportConfirmation with paths; row_number can be 0 if Excel is written by the system."
    ),
    expected_output="ReportConfirmation with summary and interview questions.",
    agent=report_writer_agent,
    context=[ingestion_task, extraction_task, jd_analysis_task, scoring_task],
    output_pydantic=ReportConfirmation,
    output_file="outputs/last_report_confirmation.json",
)
