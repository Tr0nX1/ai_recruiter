"""Deterministic Excel + JSON backup from structured crew outputs."""

from __future__ import annotations

from typing import Any

from models.candidate_profile import CandidateProfile
from models.evaluation import CandidateEvaluation
from models.ingestion import IngestionOutput
from tools.excel_writer_tool import append_excel_row, append_json_backup, utc_now_iso


def _pipe_join(items: list[str]) -> str:
    return " | ".join(x.strip() for x in items if x and str(x).strip())


def _comma_join(items: list[str]) -> str:
    return ", ".join(x.strip() for x in items if x and str(x).strip())


def _format_work_history(profile: CandidateProfile) -> str:
    parts: list[str] = []
    for w in profile.work_history:
        bits = [w.company, w.role]
        if w.start_date or w.end_date:
            bits.append(f"{w.start_date or '?'} – {w.end_date or 'Present'}")
        parts.append(" · ".join(b for b in bits if b))
    return _pipe_join(parts)


def _format_education(profile: CandidateProfile) -> str:
    parts: list[str] = []
    for e in profile.education:
        bits = [e.degree, e.institution]
        if e.year_completed:
            bits.append(str(e.year_completed))
        parts.append(" · ".join(b for b in bits if b))
    return _pipe_join(parts)


def build_row_payload(
    *,
    role_title: str,
    ingestion: IngestionOutput,
    profile: CandidateProfile,
    evaluation: CandidateEvaluation,
    recruiter_summary: str | None = None,
) -> dict[str, Any]:
    summary = recruiter_summary.strip() if recruiter_summary else evaluation.summary
    strengths = _pipe_join(evaluation.strengths)
    weaknesses = _pipe_join(evaluation.weaknesses)
    risks = _pipe_join(evaluation.risks)
    opps = _pipe_join(evaluation.opportunities)
    iq = _pipe_join(evaluation.interview_questions)

    return {
        "candidate_name": profile.name,
        "email": profile.email or "",
        "phone": profile.phone or "",
        "location": profile.location or "",
        "role_applied": role_title,
        "overall_score": evaluation.overall_score,
        "skills_match_pct": evaluation.skills_match_pct,
        "experience_score": evaluation.experience_score,
        "education_score": evaluation.education_score,
        "recommendation": evaluation.recommendation,
        "seniority_level": evaluation.seniority_level,
        "summary": summary,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "risks": risks,
        "opportunities": opps,
        "skills": _comma_join(profile.skills),
        "missing_skills": _comma_join(evaluation.missing_skills),
        "past_experience": _format_work_history(profile),
        "total_years_exp": profile.total_years_exp,
        "education": _format_education(profile),
        "certifications": _comma_join(profile.certifications),
        "interview_questions": iq,
        "file_name": ingestion.filename,
        "processed_date": utc_now_iso(),
        "source": ingestion.source_type,
        "recruiter_notes": "",
        "interview_status": "Pending",
    }


def persist_after_crew(
    *,
    role_title: str,
    ingestion: IngestionOutput,
    profile: CandidateProfile,
    evaluation: CandidateEvaluation,
    recruiter_summary: str | None = None,
) -> dict[str, Any]:
    row = build_row_payload(
        role_title=role_title,
        ingestion=ingestion,
        profile=profile,
        evaluation=evaluation,
        recruiter_summary=recruiter_summary,
    )
    excel_meta = append_excel_row(row)
    append_json_backup(
        {
            "role_title": role_title,
            "ingestion": ingestion.model_dump(),
            "profile": profile.model_dump(),
            "evaluation": evaluation.model_dump(),
            "excel": excel_meta,
        }
    )
    return excel_meta
