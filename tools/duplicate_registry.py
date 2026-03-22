"""Duplicate resume detection via content hash (Phase 4)."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

from loguru import logger

from config import OUTPUT_DIR

REGISTRY_PATH = OUTPUT_DIR / "duplicate_registry.json"


class DuplicateSkippedError(Exception):
    """Raised when a resume was already processed (same file hash)."""

    def __init__(self, *, file_path: str, content_hash: str) -> None:
        self.file_path = file_path
        self.content_hash = content_hash
        super().__init__(f"Duplicate resume skipped (hash {content_hash[:12]}…): {file_path}")


def _load() -> dict[str, Any]:
    if not REGISTRY_PATH.exists():
        return {"hashes": {}}
    try:
        data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or "hashes" not in data:
            return {"hashes": {}}
        return data
    except json.JSONDecodeError:
        return {"hashes": {}}


def _save(data: dict[str, Any]) -> None:
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def sha256_file_bytes(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_text_normalized(text: str) -> str:
    """Normalize whitespace and lowercase for text-based dedupe."""
    import re

    t = re.sub(r"\s+", " ", text.strip().lower())
    return hashlib.sha256(t.encode("utf-8")).hexdigest()


def compute_resume_fingerprint(path: str | Path) -> str:
    """Hash mode: `bytes` (default) or `text` (txt only; else falls back to bytes)."""
    mode = os.getenv("DUPLICATE_HASH_MODE", "bytes").lower()
    p = Path(path)
    if mode == "text" and p.suffix.lower() == ".txt":
        raw = p.read_text(encoding="utf-8", errors="replace")
        return sha256_text_normalized(raw)
    return sha256_file_bytes(p)


def is_duplicate(content_hash: str) -> bool:
    data = _load()
    return content_hash in data["hashes"]


def ensure_not_duplicate(path: str | Path) -> str:
    """Compute fingerprint; raise DuplicateSkippedError if already processed."""
    fp = compute_resume_fingerprint(path)
    if is_duplicate(fp):
        raise DuplicateSkippedError(file_path=str(path), content_hash=fp)
    return fp


def record_processed(path: str | Path, content_hash: str) -> None:
    """Call after successful pipeline persist."""
    if os.getenv("SKIP_DUPLICATE_RESUMES", "true").lower() not in ("1", "true", "yes"):
        return
    data = _load()
    data["hashes"][content_hash] = {
        "path": str(path),
        "note": "processed",
    }
    _save(data)
    logger.debug("Recorded duplicate-registry entry for {}", path)


def forget_hash(content_hash: str) -> None:
    """Remove a hash (e.g. for testing)."""
    data = _load()
    data["hashes"].pop(content_hash, None)
    _save(data)
