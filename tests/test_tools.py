"""Smoke tests for file readers (no API calls)."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SAMPLE = ROOT / "tests" / "sample_resumes" / "sample.txt"


def test_txt_reader_extracts_text():
    from tools.txt_reader_tool import TXTReaderTool

    t = TXTReaderTool()
    out = t._run(file_path=str(SAMPLE))  # noqa: SLF001
    assert out["extraction_status"] == "success"
    assert "Jane Doe" in out["raw_text"]


def test_bias_filter_finds_flags():
    from tools.bias_filter_tool import BiasFilterTool

    t = BiasFilterTool()
    out = t._run(resume_text="Age: 45 years old, male candidate")  # noqa: SLF001
    assert out["flag_count"] >= 1
