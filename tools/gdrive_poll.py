"""Poll a Google Drive folder for new resume files (Phase 4)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from loguru import logger

from config import OUTPUT_DIR
from tools.gdrive_client import get_drive_service, list_files_in_folder

STATE_PATH = OUTPUT_DIR / "gdrive_poll_state.json"

ALLOWED_MIME = (
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
    "application/vnd.google-apps.document",
)


def _load_state() -> dict[str, Any]:
    if not STATE_PATH.exists():
        return {"seen_ids": []}
    try:
        data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
        if not isinstance(data.get("seen_ids"), list):
            data["seen_ids"] = []
        return data
    except json.JSONDecodeError:
        return {"seen_ids": []}


def _save_state(data: dict[str, Any]) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def poll_new_resume_files(
    folder_id: str | None = None,
    *,
    mark_seen: bool = True,
) -> list[dict[str, Any]]:
    """
    Return Drive file entries under ``folder_id`` that were not in the last poll state.
    Each item: ``{"id", "name", "mimeType", "download_path"}`` where ``download_path`` is set after download.
    """
    fid = folder_id or os.getenv("GDRIVE_FOLDER_ID")
    if not fid:
        logger.error("GDRIVE_FOLDER_ID not set")
        return []

    if get_drive_service() is None:
        logger.error("Google Drive credentials not configured (service account or OAuth).")
        return []

    state = _load_state()
    seen: set[str] = set(state.get("seen_ids", []))

    raw = list_files_in_folder(
        fid,
        mime_prefixes=("application/", "text/"),
    )
    new_files: list[dict[str, Any]] = []
    for f in raw:
        fid_ = f.get("id")
        mt = f.get("mimeType") or ""
        if mt not in ALLOWED_MIME:
            continue
        if fid_ in seen:
            continue
        new_files.append(f)

    if not mark_seen:
        return new_files

    # Download each new file to outputs/gdrive_inbox/
    inbox = OUTPUT_DIR / "gdrive_inbox"
    inbox.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []
    from tools.gdrive_client import download_file_to_path

    for f in new_files:
        fid_ = f["id"]
        name = f.get("name") or fid_
        mt = f.get("mimeType") or ""
        dest = inbox / f"{fid_}_{Path(name).stem}"
        meta = download_file_to_path(fid_, dest)
        if meta.get("extraction_status") == "success":
            saved = meta.get("saved_path") or str(dest)
            results.append(
                {
                    "id": fid_,
                    "name": name,
                    "mimeType": mt,
                    "local_path": saved,
                }
            )
            seen.add(fid_)

    state["seen_ids"] = list(seen)
    _save_state(state)
    return results
