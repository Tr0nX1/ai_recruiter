"""Crew assembly, kickoff, batch run, and deterministic Excel/JSON persistence."""

from __future__ import annotations

import os
from collections.abc import Callable
from typing import Any

from crewai import Crew, Process
from crewai.crews.crew_output import CrewOutput
from loguru import logger
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from agents import (
    extractor_agent,
    ingestion_agent,
    jd_analyser_agent,
    report_writer_agent,
    scoring_agent,
)
from config import (
    API_RETRY_MAX_ATTEMPTS,
    API_RETRY_MAX_WAIT_SEC,
    API_RETRY_MIN_WAIT_SEC,
    OUTPUT_DIR,
    USE_CREW_MEMORY,
)
from tools.duplicate_registry import (
    DuplicateSkippedError,
    compute_resume_fingerprint,
    ensure_not_duplicate,
    record_processed,
)
from tasks.extraction_task import extraction_task
from tasks.ingestion_task import ingestion_task
from tasks.jd_analysis_task import jd_analysis_task
from tasks.report_task import report_task
from tasks.scoring_task import scoring_task

_last_kickoff_inputs: dict[str, Any] = {}


def _is_transient_api_error(exc: BaseException) -> bool:
    """Retry rate limits, timeouts, and connection errors (OpenAI + Anthropic)."""
    msg = str(exc).lower()
    if "insufficient_quota" in msg:
        return False
    try:
        from openai import APIConnectionError, APITimeoutError, RateLimitError

        if isinstance(exc, (RateLimitError, APIConnectionError, APITimeoutError)):
            return True
    except ImportError:
        pass
    try:
        from anthropic import APIConnectionError as AnthrAPIConnErr
        from anthropic import RateLimitError as AnthrRateLimitErr

        if isinstance(exc, (AnthrRateLimitErr, AnthrAPIConnErr)):
            return True
    except ImportError:
        pass
    if "429" in msg or "rate limit" in msg:
        return True
    if "timeout" in msg or "timed out" in msg:
        return True
    if "connection" in msg or "connect" in msg:
        return True
    if "503" in msg or "unavailable" in msg or "502" in msg or "504" in msg:
        return True
    return False


def _kickoff_with_retry(crew: Crew, inputs: dict[str, Any]) -> CrewOutput:
    """Run crew.kickoff with optional tenacity retries for transient API failures."""

    if API_RETRY_MAX_ATTEMPTS <= 1:
        return crew.kickoff(inputs=inputs)

    @retry(
        stop=stop_after_attempt(API_RETRY_MAX_ATTEMPTS),
        wait=wait_exponential(
            multiplier=1,
            min=API_RETRY_MIN_WAIT_SEC,
            max=API_RETRY_MAX_WAIT_SEC,
        ),
        retry=retry_if_exception(_is_transient_api_error),
        reraise=True,
    )
    def _do() -> CrewOutput:
        return crew.kickoff(inputs=inputs)

    return _do()


def _persist_from_crew_output(result: CrewOutput) -> CrewOutput:
    """Write Excel + JSON backup from structured task outputs (canonical row)."""
    try:
        outs = result.tasks_output
        if len(outs) < 5:
            logger.warning("Skipping persistence: incomplete task outputs ({})", len(outs))
            return result

        ing = outs[0].pydantic
        pro = outs[1].pydantic
        ev = outs[3].pydantic
        rep = outs[4].pydantic

        if ing is None or pro is None or ev is None:
            logger.warning("Skipping persistence: missing pydantic on task outputs")
            return result

        from models.candidate_profile import CandidateProfile
        from models.evaluation import CandidateEvaluation
        from models.ingestion import IngestionOutput
        from models.report import ReportConfirmation

        if not isinstance(ing, IngestionOutput) or not isinstance(pro, CandidateProfile):
            return result
        if not isinstance(ev, CandidateEvaluation):
            return result

        summary = None
        if isinstance(rep, ReportConfirmation) and rep.recruiter_summary:
            summary = rep.recruiter_summary.strip()

        role_title = str(_last_kickoff_inputs.get("role_title") or "").strip() or "Role"

        from tools.pipeline_io import persist_after_crew
        from tools.slack_notify_tool import SlackNotifyTool

        meta = persist_after_crew(
            role_title=role_title,
            ingestion=ing,
            profile=pro,
            evaluation=ev,
            recruiter_summary=summary,
        )

        fp = _last_kickoff_inputs.get("content_hash")
        rpath = _last_kickoff_inputs.get("resume_path")
        if fp and rpath:
            record_processed(rpath, fp)
            from tools.evaluation_memory import append_record

            append_record(
                content_hash=fp,
                role_title=role_title,
                candidate_name=pro.name,
                overall_score=ev.overall_score,
                recommendation=ev.recommendation,
                source_path=str(rpath),
            )

        if ev.recommendation == "Shortlist":
            slack = SlackNotifyTool()
            slack._run(  # noqa: SLF001
                message=f"Shortlist: {pro.name} — {role_title} (score {ev.overall_score})"
            )

        logger.info("Persisted row {} to {}", meta.get("row_number"), meta.get("excel_path"))
    except Exception as e:  # noqa: BLE001
        logger.exception("Persistence failed: {}", e)
    return result


def build_crew() -> Crew:
    embedder_cfg = None
    if USE_CREW_MEMORY:
        embedder_cfg = {
            "provider": "huggingface",
            "config": {"model": "all-MiniLM-L6-v2"},
        }

    return Crew(
        agents=[
            ingestion_agent,
            extractor_agent,
            jd_analyser_agent,
            scoring_agent,
            report_writer_agent,
        ],
        tasks=[
            ingestion_task,
            extraction_task,
            jd_analysis_task,
            scoring_task,
            report_task,
        ],
        process=Process.sequential,
        memory=USE_CREW_MEMORY,
        embedder=embedder_cfg,
        verbose=True,
        max_rpm=30,
        output_log_file=str(OUTPUT_DIR / "crew_log.txt"),
        after_kickoff_callbacks=[_persist_from_crew_output],
    )


def run_for_resume(
    resume_path: str,
    jd_text: str,
    role_title: str,
    *,
    dedup_enabled: bool | None = None,
) -> CrewOutput:
    global _last_kickoff_inputs

    if dedup_enabled is None:
        dedup_enabled = os.getenv("SKIP_DUPLICATE_RESUMES", "true").lower() in ("1", "true", "yes")

    _last_kickoff_inputs = {
        "resume_path": resume_path,
        "jd_text": jd_text,
        "role_title": role_title,
        "content_hash": None,
    }

    if dedup_enabled:
        fp = ensure_not_duplicate(resume_path)
    else:
        fp = compute_resume_fingerprint(resume_path)
    _last_kickoff_inputs["content_hash"] = fp

    crew = build_crew()
    inputs = {
        "resume_path": resume_path,
        "jd_text": jd_text,
        "role_title": role_title,
    }
    logger.info("Processing: {}", resume_path)
    result = _kickoff_with_retry(crew, inputs)
    logger.info("Completed: {}", resume_path)
    return result


ProgressCallback = Callable[[int, int, str, str, str | None], None]
"""Args: index (1-based), total, path, phase ('start'|'success'|'fail'|'skip'), error message."""


def run_batch(
    resume_paths: list[str],
    jd_text: str,
    role_title: str,
    *,
    on_progress: ProgressCallback | None = None,
    dedup_enabled: bool | None = None,
) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    failed: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    total = len(resume_paths)

    for i, path in enumerate(resume_paths, 1):
        logger.info("[{}/{}] Processing {}", i, total, path)
        if on_progress:
            on_progress(i, total, path, "start", None)
        try:
            result = run_for_resume(
                path,
                jd_text,
                role_title,
                dedup_enabled=dedup_enabled,
            )
            results.append({"file": path, "status": "success", "result": result})
            if on_progress:
                on_progress(i, total, path, "success", None)
        except DuplicateSkippedError as e:
            logger.info("Skipped duplicate: {} — {}", path, e.content_hash[:16])
            skipped.append(
                {"file": e.file_path, "reason": "duplicate", "hash": e.content_hash}
            )
            if on_progress:
                on_progress(i, total, path, "skip", str(e))
        except Exception as e:  # noqa: BLE001
            logger.error("Failed: {} — {}", path, e)
            failed.append({"file": path, "error": str(e)})
            if on_progress:
                on_progress(i, total, path, "fail", str(e))

    logger.info(
        "Batch complete: {} success, {} failed, {} skipped",
        len(results),
        len(failed),
        len(skipped),
    )
    return {"results": results, "failed": failed, "skipped": skipped}
