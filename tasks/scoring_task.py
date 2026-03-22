"""Task 4 — scoring."""

from __future__ import annotations

from crewai import Task

from agents.scoring_agent import scoring_agent
from models.evaluation import CandidateEvaluation
from tasks.extraction_task import extraction_task
from tasks.ingestion_task import ingestion_task
from tasks.jd_analysis_task import jd_analysis_task

scoring_task = Task(
    name="scoring",
    description=(
        "Compare CandidateProfile (extraction) against JobRequirements (JD analysis). "
        "Use SentenceEmbeddingTool for skills similarity and ScoringCalculatorTool with "
        "weights from JobRequirements. "
        "Run BiasFilterTool on raw resume text from context. "
        "Fill SWOT with evidence-backed bullets. "
        "Set recommendation: Shortlist (80+), Maybe (60–79), Reject (<60). "
        "Provide exactly five interview_questions tailored to gaps and strengths."
    ),
    expected_output="A validated CandidateEvaluation object.",
    agent=scoring_agent,
    context=[ingestion_task, extraction_task, jd_analysis_task],
    output_pydantic=CandidateEvaluation,
)
