"""Crew assembly, kickoff, batch run, and deterministic Excel/JSON persistence."""

from __future__ import annotations

import os
from collections.abc import Callable
from typing import Any

from crewai import Crew, Process
from crewai.crews.crew_output import CrewOutput
from loguru import logger
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
import time

import types
import concurrent.futures

_circuit_breaker: dict[str, int] = {}

def _patch_agent(agent: Any, models_list: list[str], agent_id: str) -> None:
    original_execute_task = agent.execute_task
    
    def execute_with_fallback(self, *args, **kwargs):
        for attempt, model in enumerate(models_list):
            if _circuit_breaker.get(model, 0) >= 3:
                logger.info("[LLM SKIP] agent={} model={} reason=circuit_breaker_active", getattr(self, "role", agent_id), model)
                continue
                
            self.llm = model
            logger.info("[LLM TRY] agent={} model={} attempt={}", getattr(self, "role", agent_id), model, attempt + 1)
            
            try:
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(original_execute_task, *args, **kwargs)
                    out = future.result(timeout=30)
                    
                logger.info("[LLM SUCCESS] agent={} model={}", getattr(self, "role", agent_id), model)
                _circuit_breaker[model] = 0
                return out
                
            except concurrent.futures.TimeoutError:
                logger.error("[LLM FAIL] agent={} model={} reason=timeout", getattr(self, "role", agent_id), model)
                _circuit_breaker[model] = _circuit_breaker.get(model, 0) + 1
                
            except Exception as e:
                reason = str(e).split('\n')[0][:100]
                logger.error("[LLM FAIL] agent={} model={} reason={}", getattr(self, "role", agent_id), model, reason)
                _circuit_breaker[model] = _circuit_breaker.get(model, 0) + 1
                
            if attempt < len(models_list) - 1:
                next_model = models_list[attempt + 1]
                logger.info("[LLM FALLBACK] switching → {}", next_model)
                time.sleep(1)
                
        logger.error("All LLM providers failed for {}", getattr(self, "role", agent_id))
        return {
            "status": "error",
            "reason": "All LLM providers failed",
            "agent": getattr(self, "role", agent_id)
        }
        
    agent.execute_task = types.MethodType(execute_with_fallback, agent)

def isolate_agent_fallbacks(crew: Crew) -> None:
    from config import FAST_MODELS, SMART_MODELS
    for agent in crew.agents:
        role = (agent.role or "").lower()
        fast_keywords = ["document processing", "data analyst", "talent acquisition"]
        if any(k in role for k in fast_keywords):
            _patch_agent(agent, FAST_MODELS, "fast")
        else:
            _patch_agent(agent, SMART_MODELS, "smart")

def _kickoff_with_retry(crew: Crew, inputs: dict[str, Any]) -> CrewOutput:
    """Run crew.kickoff with fallback logic handled at the agent execution level."""
    isolate_agent_fallbacks(crew)
    return crew.kickoff(inputs=inputs)


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
