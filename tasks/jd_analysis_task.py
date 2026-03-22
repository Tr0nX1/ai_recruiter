"""Task 3 — JD analysis."""

from __future__ import annotations

from crewai import Task

from agents.jd_analyser_agent import jd_analyser_agent
from models.job_requirements import JobRequirements

jd_analysis_task = Task(
    name="jd_analysis",
    description=(
        "Analyse the job description text: {jd_text} for the role: {role_title}. "
        "Extract requirements, must-have vs nice-to-have skills, min years, education, "
        "seniority target, responsibilities, and scoring_weights summing to 1.0."
    ),
    expected_output="A validated JobRequirements object.",
    agent=jd_analyser_agent,
    output_pydantic=JobRequirements,
)
