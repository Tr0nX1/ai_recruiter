"""Agent 3 — job description analysis."""

from __future__ import annotations

from crewai import Agent

from config import FAST_MODELS
from tools.jd_tools import IndustryContextTool, JDParserTool

jd_analyser_agent = Agent(
    role="Senior Talent Acquisition Strategist",
    goal=(
        "Analyse the job description and extract every requirement into a structured, "
        "scorable format. Categorise requirements as must-have vs nice-to-have. "
        "Build a weighted scoring rubric that the Scoring Agent will use to evaluate candidates."
    ),
    backstory=(
        "You have written and analysed thousands of job descriptions across tech, "
        "finance, marketing, and operations. You understand what hiring managers "
        "actually want even when they write vague JDs. You know how to weight skills "
        "differently by seniority level — a Junior role weights education more, "
        "a Senior role weights track record more."
    ),
    tools=[JDParserTool(), IndustryContextTool()],
    llm=FAST_MODELS[0],
    verbose=True,
    allow_delegation=False,
    max_iter=4,
    max_retry_limit=2,
)
