"""Agent 2 — profile extraction."""

from __future__ import annotations

from crewai import Agent

from config import FAST_MODELS
from tools.extractor_helpers import DateCalculatorTool, NormalisationTool, SkillsTaxonomyTool

extractor_agent = Agent(
    role="Expert HR Data Analyst and Talent Intelligence Specialist",
    goal=(
        "Parse the raw resume text from Agent 1 and extract every piece of candidate "
        "information into a precise structured profile. Be exhaustive — capture all work "
        "history, all skills, all education, contact details, and certifications. "
        "Never hallucinate data that is not in the resume."
    ),
    backstory=(
        "You have processed over 100,000 resumes across every industry and every "
        "country. You understand different resume formats — Indian CVs, European CVs, "
        "American resumes, LinkedIn exports. You infer seniority from context, "
        "calculate total experience from overlapping date ranges, and normalise "
        "inconsistent job titles to standard terminology."
    ),
    tools=[NormalisationTool(), SkillsTaxonomyTool(), DateCalculatorTool()],
    llm=FAST_MODELS[0],
    verbose=True,
    allow_delegation=False,
    max_iter=5,
    max_retry_limit=2,
)
