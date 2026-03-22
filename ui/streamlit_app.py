"""Streamlit UI — Phase 3: batch progress, failures, exports (plan/Ai_recruiter_plan.md §12–14)."""

from __future__ import annotations

import io
import os
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import (  # noqa: E402
    EXCEL_PATH,
    OUTPUT_DIR,
    PLACEHOLDER_OPENAI_KEY,
    UPLOAD_DIR,
)
from crew import run_batch  # noqa: E402

st.set_page_config(page_title="AI Recruiter", page_icon="🤖", layout="wide")
st.title("AI Resume Screener")
st.caption("Powered by CrewAI · GPT-4o family · Sentence Transformers · batch + retries")

with st.sidebar:
    st.header("Job Details")
    role_title = st.text_input("Role Title", placeholder="e.g. Senior Accountant")
    jd_text = st.text_area("Paste Job Description", height=300, placeholder="Full job description here...")
    st.divider()
    st.header("Settings")
    max_files = st.slider("Max resumes per run", 1, 100, 40)
    st.caption("API retries use `API_RETRY_*` in `.env` (see README).")

st.header("Upload Resumes")
uploaded_files = st.file_uploader(
    "Drop PDF, DOCX or TXT files here",
    type=["pdf", "docx", "txt"],
    accept_multiple_files=True,
)

if os.getenv("OPENAI_API_KEY") == PLACEHOLDER_OPENAI_KEY:
    st.warning("Set OPENAI_API_KEY in `.env` before running screening.")

if st.button("Run AI Screening", type="primary", disabled=not (uploaded_files and jd_text and role_title)):
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    saved_paths: list[str] = []
    for f in uploaded_files[:max_files]:
        path = UPLOAD_DIR / f.name
        path.write_bytes(f.read())
        saved_paths.append(str(path))

    progress = st.progress(0)
    status = st.empty()

    def on_progress(
        i: int,
        n: int,
        path: str,
        phase: str,
        err: str | None,
    ) -> None:
        label = Path(path).name
        if phase == "start":
            progress.progress((i - 1) / n if n else 0.0)
            status.markdown(f"**Running** `[{i}/{n}]` **{label}**")
        elif phase == "success":
            progress.progress(i / n if n else 1.0)
        elif phase == "fail":
            progress.progress(i / n if n else 1.0)
            short = (err or "")[:240]
            status.markdown(f"**Failed** `[{i}/{n}]` **{label}** — `{short}`")
        elif phase == "skip":
            progress.progress(i / n if n else 1.0)
            short = (err or "")[:200]
            status.markdown(f"**Skipped (duplicate)** `[{i}/{n}]` **{label}** — `{short}`")

    with st.spinner("Screening in progress…"):
        batch = run_batch(saved_paths, jd_text, role_title, on_progress=on_progress)

    progress.progress(1.0)
    ok = len(batch["results"])
    nf = len(batch["failed"])
    ns = len(batch.get("skipped", []))
    st.success(f"Batch finished: **{ok}** succeeded, **{nf}** failed, **{ns}** skipped (duplicates).")

    if ns:
        with st.expander("Skipped duplicates", expanded=False):
            st.dataframe(pd.DataFrame(batch["skipped"]), use_container_width=True)

    if nf:
        with st.expander("Failed files (download CSV)", expanded=True):
            fail_df = pd.DataFrame(batch["failed"])
            st.dataframe(fail_df, use_container_width=True)
            buf = io.StringIO()
            fail_df.to_csv(buf, index=False)
            st.download_button(
                "Download failures as CSV",
                buf.getvalue().encode("utf-8"),
                file_name="ai_recruiter_failures.csv",
                mime="text/csv",
            )

    if Path(EXCEL_PATH).exists():
        df = pd.read_excel(EXCEL_PATH)
        st.header("Results")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total rows in workbook", len(df))
        if "Recommendation" in df.columns:
            col2.metric("Shortlisted", len(df[df["Recommendation"] == "Shortlist"]))
            col3.metric("Maybe", len(df[df["Recommendation"] == "Maybe"]))
            col4.metric("Rejected", len(df[df["Recommendation"] == "Reject"]))

        display_cols = [
            c
            for c in [
                "Candidate Name",
                "Overall Score",
                "Recommendation",
                "Skills Match %",
                "Seniority Level",
                "Summary",
            ]
            if c in df.columns
        ]
        view = df[display_cols]
        if "Overall Score" in view.columns:
            view = view.sort_values("Overall Score", ascending=False)
        st.dataframe(view, use_container_width=True)

        with open(EXCEL_PATH, "rb") as f:
            st.download_button(
                "Download Full Excel Report",
                f,
                file_name="ai_recruiter_results.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

    log_path = OUTPUT_DIR / "app.log"
    if log_path.exists():
        st.caption(f"Session logs also append to `{log_path}`.")
