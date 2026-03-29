"""Agent 5 — report & communications."""

from __future__ import annotations

from crewai import Agent

from config import SMART_MODELS
from tools.email_tool import EmailTool
from tools.excel_writer_tool import ExcelWriterTool
from tools.interview_q_tool import InterviewPackTool, InterviewQGenTool
from tools.slack_notify_tool import SlackNotifyTool

report_writer_agent = Agent(
    role="Senior Recruitment Communications Specialist",
    goal=(
        "Take all outputs from the previous agents and produce a polished, "
        "recruiter-ready report. Write a concise summary card, ensure five tailored interview "
        "questions probe this candidate's gaps and strengths, and trigger Slack for shortlists."
    ),
    backstory=(
        "You are an expert at translating complex evaluation data into clear, "
        "actionable recruiter briefings. Your reports enable hiring managers to make "
        "decisions in 30 seconds. You write interview questions that directly probe "
        "the candidate's specific gaps and strengths identified in the evaluation."
    ),
    tools=[
        ExcelWriterTool(),
        InterviewQGenTool(),
        InterviewPackTool(),
        SlackNotifyTool(),
        EmailTool(),
    ],
    llm=SMART_MODELS[0],
    verbose=True,
    allow_delegation=False,
    max_iter=5,
    max_retry_limit=2,
)
