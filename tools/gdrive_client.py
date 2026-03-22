"""Google Drive API v3 helpers (read-only; service account or OAuth)."""

from __future__ import annotations

import io
import os
from pathlib import Path
from typing import Any

from loguru import logger

SCOPES_RO = ("https://www.googleapis.com/auth/drive.readonly",)


def _service_account_credentials():
    path = os.getenv("GDRIVE_SERVICE_ACCOUNT_JSON") or os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not path:
        return None
    p = Path(path)
    if not p.is_file():
        return None
    try:
        from google.oauth2 import service_account

        return service_account.Credentials.from_service_account_file(str(p), scopes=SCOPES_RO)
    except Exception as e:  # noqa: BLE001
        logger.warning("Could not load Drive service account: {}", e)
        return None


def _oauth_credentials():
    """Load OAuth token from token file (created by interactive auth)."""
    token_path = os.getenv("GOOGLE_TOKEN_FILE") or str(Path("outputs") / "gdrive_token.json")
    creds_path = os.getenv("GOOGLE_CREDENTIALS_FILE") or "credentials.json"
    if not Path(creds_path).is_file():
        return None
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials

        creds = None
        if Path(token_path).is_file():
            creds = Credentials.from_authorized_user_file(token_path, SCOPES_RO)
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        elif not creds or not creds.valid:
            # Headless: skip interactive flow
            return None
        return creds
    except Exception as e:  # noqa: BLE001
        logger.debug("OAuth credentials not available: {}", e)
        return None


def get_drive_service():
    """Return Drive v3 service or None if not configured."""
    creds = _service_account_credentials() or _oauth_credentials()
    if creds is None:
        return None
    try:
        from googleapiclient.discovery import build

        return build("drive", "v3", credentials=creds, cache_discovery=False)
    except Exception as e:  # noqa: BLE001
        logger.warning("Could not build Drive service: {}", e)
        return None


def list_files_in_folder(folder_id: str, mime_prefixes: tuple[str, ...] | None = None) -> list[dict[str, Any]]:
    """List non-trashed files directly under a folder."""
    service = get_drive_service()
    if service is None:
        return []
    q = f"'{folder_id}' in parents and trashed = false"
    out: list[dict[str, Any]] = []
    page_token = None
    while True:
        resp = (
            service.files()
            .list(
                q=q,
                spaces="drive",
                fields="nextPageToken, files(id, name, mimeType, modifiedTime, size)",
                pageToken=page_token,
                pageSize=100,
            )
            .execute()
        )
        for f in resp.get("files", []):
            mt = f.get("mimeType") or ""
            if mime_prefixes and not any(mt.startswith(p) for p in mime_prefixes):
                continue
            out.append(f)
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return out


def _with_suffix_for_mime(dest: Path, mime: str) -> Path:
    if dest.suffix:
        return dest
    ext = {
        "application/pdf": ".pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
        "application/msword": ".doc",
        "text/plain": ".txt",
        "application/vnd.google-apps.document": ".txt",
    }.get(mime)
    return dest.with_suffix(ext) if ext else dest


def download_file_to_path(file_id: str, dest: Path) -> dict[str, Any]:
    """Download or export a Drive file to ``dest``. Returns metadata dict."""
    service = get_drive_service()
    if service is None:
        return {"error": "Drive not configured", "extraction_status": "failed"}

    meta = service.files().get(fileId=file_id, fields="id, name, mimeType").execute()
    mime = meta.get("mimeType", "")
    dest = _with_suffix_for_mime(dest, mime)
    dest.parent.mkdir(parents=True, exist_ok=True)

    if mime == "application/vnd.google-apps.document":
        from googleapiclient.http import MediaIoBaseDownload

        request = service.files().export_media(fileId=file_id, mimeType="text/plain")
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        dest.write_bytes(fh.getvalue())
        return {
            "name": meta.get("name"),
            "mimeType": mime,
            "saved_path": str(dest),
            "extraction_status": "success",
        }

    if mime == "application/vnd.google-apps.spreadsheet":
        return {"error": "Google Sheets export not supported for resumes", "extraction_status": "failed"}

    from googleapiclient.http import MediaIoBaseDownload

    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    dest.write_bytes(fh.getvalue())
    return {
        "name": meta.get("name"),
        "mimeType": mime,
        "saved_path": str(dest),
        "extraction_status": "success",
    }
