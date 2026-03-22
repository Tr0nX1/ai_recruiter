"""Long-term SQLite store of evaluations for cross-run ranking (Phase 4)."""

from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config import OUTPUT_DIR

DB_PATH = OUTPUT_DIR / "evaluation_memory.db"


def _conn() -> sqlite3.Connection:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def init_db() -> None:
    with _conn() as c:
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS evaluations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content_hash TEXT NOT NULL,
                role_title TEXT NOT NULL,
                candidate_name TEXT,
                overall_score INTEGER,
                recommendation TEXT,
                source_path TEXT,
                created_at TEXT NOT NULL,
                UNIQUE(content_hash, role_title)
            )
            """
        )
        c.execute(
            "CREATE INDEX IF NOT EXISTS idx_eval_role_score ON evaluations (role_title, overall_score DESC)"
        )


@dataclass
class EvaluationRecord:
    content_hash: str
    role_title: str
    candidate_name: str | None
    overall_score: int
    recommendation: str | None
    source_path: str | None
    created_at: str


def append_record(
    *,
    content_hash: str,
    role_title: str,
    candidate_name: str | None,
    overall_score: int,
    recommendation: str | None,
    source_path: str | None,
) -> None:
    if os.getenv("ENABLE_EVALUATION_MEMORY", "true").lower() not in ("1", "true", "yes"):
        return
    init_db()
    now = datetime.now(timezone.utc).isoformat()
    with _conn() as c:
        c.execute(
            """
            INSERT INTO evaluations (content_hash, role_title, candidate_name, overall_score, recommendation, source_path, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(content_hash, role_title) DO UPDATE SET
                candidate_name=excluded.candidate_name,
                overall_score=excluded.overall_score,
                recommendation=excluded.recommendation,
                source_path=excluded.source_path,
                created_at=excluded.created_at
            """,
            (content_hash, role_title, candidate_name, overall_score, recommendation, source_path, now),
        )
        c.commit()


def rank_for_role(role_title: str, limit: int = 50) -> list[dict[str, Any]]:
    """Return recent evaluations for a role, highest score first."""
    init_db()
    with _conn() as c:
        cur = c.execute(
            """
            SELECT content_hash, role_title, candidate_name, overall_score, recommendation, source_path, created_at
            FROM evaluations
            WHERE role_title = ?
            ORDER BY overall_score DESC, created_at DESC
            LIMIT ?
            """,
            (role_title, limit),
        )
        return [dict(r) for r in cur.fetchall()]
