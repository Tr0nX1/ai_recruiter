"""CLI entry point for AI Recruiter (see plan/Ai_recruiter_plan.md)."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


def _configure_stdio_utf8() -> None:
    """Avoid Windows console 'charmap' errors when CrewAI prints emoji."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8")
            except (OSError, ValueError, AttributeError):
                pass


_configure_stdio_utf8()

from loguru import logger

from config import MAX_RESUMES_PER_RUN, MAX_FILE_SIZE_MB
from crew import run_batch, run_for_resume


def _read_jd(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def main() -> None:
    if not os.getenv("OPENROUTER_API_KEY"):
        logger.error("Set OPENROUTER_API_KEY in .env (see .env.example).")
        raise SystemExit(1)

    parser = argparse.ArgumentParser(
        description="AI Recruiter — CrewAI resume screening (API retries: API_RETRY_* in .env)",
    )
    parser.add_argument("--resume", type=str, help="Single resume file (pdf, docx, txt)")
    parser.add_argument("--resumes-dir", type=str, help="Directory of resume files")
    parser.add_argument(
        "--gdrive-poll",
        action="store_true",
        help="Download new files from GDRIVE_FOLDER_ID then screen them (Phase 4)",
    )
    parser.add_argument("--jd", type=str, help="Path to job description .txt file")
    parser.add_argument("--role", type=str, required=True, help="Role title (e.g. Senior Accountant)")
    parser.add_argument(
        "--no-skip-duplicates",
        action="store_true",
        help="Process even if resume content hash was seen before",
    )
    parser.add_argument(
        "--memory-rank",
        action="store_true",
        help="Print top candidates for --role from evaluation_memory.db and exit",
    )
    args = parser.parse_args()

    if args.memory_rank:
        from tools.evaluation_memory import rank_for_role

        rows = rank_for_role(args.role, limit=30)
        print(json.dumps(rows, indent=2, ensure_ascii=False))
        return

    if not args.jd:
        parser.error("--jd is required unless using --memory-rank")

    jd_text = _read_jd(Path(args.jd))
    if not jd_text.strip():
        logger.error("Job description file is empty.")
        raise SystemExit(1)

    dedup_enabled = not args.no_skip_duplicates

    if args.gdrive_poll:
        from tools.gdrive_poll import poll_new_resume_files

        new_items = poll_new_resume_files()
        paths = [x["local_path"] for x in new_items if x.get("local_path")]
        if not paths:
            logger.info("No new Drive files to process.")
            return
        logger.info("Drive: {} new file(s)", len(paths))
        batch = run_batch(paths, jd_text, args.role, dedup_enabled=dedup_enabled)
        logger.info(
            "Batch finished: {} ok, {} failed, {} skipped",
            len(batch["results"]),
            len(batch["failed"]),
            len(batch["skipped"]),
        )
        return

    if args.resume:
        p = Path(args.resume)
        if not p.is_file():
            logger.error("Resume not found: {}", p)
            raise SystemExit(1)
        mb = p.stat().st_size / (1024 * 1024)
        if mb > MAX_FILE_SIZE_MB:
            logger.error("Resume exceeds {} MB", MAX_FILE_SIZE_MB)
            raise SystemExit(1)
        out = run_for_resume(
            str(p.resolve()),
            jd_text,
            args.role,
            dedup_enabled=dedup_enabled,
        )
        logger.info("Done. Crew output: {}", out)
        return

    if args.resumes_dir:
        d = Path(args.resumes_dir)
        if not d.is_dir():
            logger.error("Not a directory: {}", d)
            raise SystemExit(1)
        paths: list[str] = []
        for ext in (".pdf", ".docx", ".txt"):
            paths.extend(str(x.resolve()) for x in d.glob(f"*{ext}"))
        paths = sorted(paths)[:MAX_RESUMES_PER_RUN]
        if not paths:
            logger.error("No pdf/docx/txt files in {}", d)
            raise SystemExit(1)
        batch = run_batch(paths, jd_text, args.role, dedup_enabled=dedup_enabled)
        logger.info(
            "Batch finished: {} ok, {} failed, {} skipped",
            len(batch["results"]),
            len(batch["failed"]),
            len(batch["skipped"]),
        )
        return

    parser.error("Provide --resume, --resumes-dir, --gdrive-poll, or --memory-rank")


if __name__ == "__main__":
    main()
