"""Google Drive: download by file ID and extract text (Phase 4)."""

from __future__ import annotations

from pathlib import Path

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from config import OUTPUT_DIR
from tools.gdrive_client import download_file_to_path, get_drive_service


class GDriveInput(BaseModel):
    file_id: str = Field(description="Google Drive file ID")


def _extract_local_file(path: Path) -> dict:
    suf = path.suffix.lower()
    if suf == ".pdf":
        from tools.pdf_reader_tool import PDFReaderTool

        return PDFReaderTool()._run(file_path=str(path))  # noqa: SLF001
    if suf == ".docx":
        from tools.docx_reader_tool import DOCXReaderTool

        return DOCXReaderTool()._run(file_path=str(path))  # noqa: SLF001
    if suf in (".txt", ".text"):
        from tools.txt_reader_tool import TXTReaderTool

        return TXTReaderTool()._run(file_path=str(path))  # noqa: SLF001
    # Try UTF-8 for exported Google Docs saved as .txt
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
        return {
            "raw_text": text,
            "page_count": 1,
            "extraction_status": "success" if text.strip() else "partial",
            "error_message": None,
        }
    except OSError as e:
        return {
            "raw_text": "",
            "page_count": 0,
            "extraction_status": "failed",
            "error_message": str(e),
        }


class GDriveTool(BaseTool):
    name: str = "GDriveTool"
    description: str = (
        "Downloads a resume file from Google Drive by file ID and returns extracted text. "
        "Requires GDRIVE_SERVICE_ACCOUNT_JSON or OAuth (GOOGLE_CREDENTIALS_FILE + token). "
        "Share the file or folder with the service account email for read access."
    )
    args_schema: type[BaseModel] = GDriveInput

    def _run(self, file_id: str) -> dict:
        if get_drive_service() is None:
            return {
                "raw_text": "",
                "filename": "",
                "source_type": "gdrive",
                "page_count": 0,
                "file_size_kb": 0.0,
                "extraction_status": "failed",
                "error_message": (
                    "Drive API not configured. Set GDRIVE_SERVICE_ACCOUNT_JSON "
                    "or GOOGLE_APPLICATION_CREDENTIALS to a service account JSON with drive.readonly."
                ),
            }

        tmp_dir = OUTPUT_DIR / "gdrive_tmp"
        tmp_dir.mkdir(parents=True, exist_ok=True)
        dest = tmp_dir / f"{file_id}_download"

        meta = download_file_to_path(file_id, dest)
        if meta.get("extraction_status") != "success" and not dest.is_file():
            return {
                "raw_text": "",
                "filename": meta.get("name") or "",
                "source_type": "gdrive",
                "page_count": 0,
                "file_size_kb": 0.0,
                "extraction_status": "failed",
                "error_message": meta.get("error", "download failed"),
            }

        path = Path(meta.get("saved_path", str(dest)))
        if not path.suffix:
            # Export as plain text from Google Doc → often no extension
            path_txt = path.with_suffix(".txt")
            if path.exists():
                path.rename(path_txt)
                path = path_txt

        extracted = _extract_local_file(path)
        kb = path.stat().st_size / 1024.0 if path.is_file() else 0.0
        name = meta.get("name") or path.name
        return {
            "raw_text": extracted.get("raw_text", ""),
            "filename": name,
            "source_type": "gdrive",
            "page_count": int(extracted.get("page_count") or 0),
            "file_size_kb": round(kb, 2),
            "extraction_status": extracted.get("extraction_status", "partial"),
            "error_message": extracted.get("error_message"),
        }
