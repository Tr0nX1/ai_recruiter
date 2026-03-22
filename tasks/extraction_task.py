"""Task 2 — profile extraction."""

from __future__ import annotations

from crewai import Task

from agents.extractor_agent import extractor_agent
from models.candidate_profile import CandidateProfile
from tasks.ingestion_task import ingestion_task

extraction_task = Task(
    name="extraction",
    description=(
        "Parse the raw resume text from the ingestion step and extract "
        "every piece of candidate information into CandidateProfile. "
        "Calculate total years of experience; handle overlaps sensibly. "
        "Normalise skills using tools where helpful. "
        "If a field is missing, use null/empty — do not invent data."
    ),
    expected_output="A validated CandidateProfile matching the Pydantic schema.",
    agent=extractor_agent,
    context=[ingestion_task],
    output_pydantic=CandidateProfile,
)
