"""Application settings and environment (see plan/Ai_recruiter_plan.md)."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent

# Allow LiteLLM to import safely without throwing openai missing key errors
PLACEHOLDER_KEY = "placeholder-set-key-in-env"
if not os.getenv("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = PLACEHOLDER_KEY

# Primary LLM routing is powered by OpenRouter
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    import warnings
    warnings.warn("OPENROUTER_API_KEY not set — LLM calls will fail.")

# Multi-Level LLM Array defaults (Standardized to OpenRouter)
# Allows Graceful Failover through multiple LLM providers seamlessly.
FAST_MODELS = [
    os.getenv("FAST_MODELS_0", "openrouter/meta-llama/llama-3.1-8b-instruct"),
    os.getenv("FAST_MODELS_1", "openrouter/deepseek/deepseek-chat"),
    os.getenv("FAST_MODELS_2", "openrouter/mistral/mistral-7b-instruct"),
]

SMART_MODELS = [
    os.getenv("SMART_MODELS_0", "openrouter/openai/gpt-4o-mini"),
    os.getenv("SMART_MODELS_1", "openrouter/anthropic/claude-3-haiku"),
    os.getenv("SMART_MODELS_2", "openrouter/google/gemini-flash-1.5"),
]
TEMPERATURE_SCORING = float(os.getenv("TEMPERATURE_SCORING", "0.2"))
TEMPERATURE_WRITING = float(os.getenv("TEMPERATURE_WRITING", "0.7"))

# Processing limits
MAX_RESUMES_PER_RUN = int(os.getenv("MAX_RESUMES_PER_RUN", "100"))
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "10"))
MAX_TOKENS_PER_RESUME = int(os.getenv("MAX_TOKENS_PER_RESUME", "8000"))

# Scoring weights (must sum to 1.0)
SCORING_WEIGHTS = {
    "skills": 0.40,
    "experience": 0.30,
    "education": 0.20,
    "culture_fit": 0.10,
}

SHORTLIST_THRESHOLD = int(os.getenv("SHORTLIST_THRESHOLD", "80"))
MAYBE_THRESHOLD = int(os.getenv("MAYBE_THRESHOLD", "60"))

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

OUTPUT_DIR = PROJECT_ROOT / "outputs"
EXCEL_PATH = OUTPUT_DIR / "results.xlsx"
JSON_BACKUP_PATH = OUTPUT_DIR / "results_backup.json"
UPLOAD_DIR = OUTPUT_DIR / "uploads"

# Crew: short-term memory adds latency/deps; enable via env when stable
USE_CREW_MEMORY = os.getenv("USE_CREW_MEMORY", "false").lower() in ("1", "true", "yes")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_CHANNEL_ID = os.getenv("SLACK_CHANNEL_ID")

for d in (OUTPUT_DIR, UPLOAD_DIR):
    d.mkdir(parents=True, exist_ok=True)

# Phase 3 — API resilience fallback configuration
# Removing manual retry constraints; max attempts bounded safely by len(FAST_MODELS/SMART_MODELS) natively.

# Log file (loguru, Phase 3)
_ai_recruiter_log_configured = False
if not _ai_recruiter_log_configured:
    try:
        from loguru import logger as _loguru_logger

        _loguru_logger.add(
            OUTPUT_DIR / "app.log",
            rotation="5 MB",
            retention=3,
            encoding="utf-8",
            level="INFO",
        )
    except Exception:  # noqa: BLE001
        pass
    _ai_recruiter_log_configured = True

# Phase 4 — Drive, Apify, dedupe, long-term memory (plan/Ai_recruiter_plan.md §14)
GDRIVE_FOLDER_ID = os.getenv("GDRIVE_FOLDER_ID")
GDRIVE_SERVICE_ACCOUNT_JSON = os.getenv("GDRIVE_SERVICE_ACCOUNT_JSON")
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
GOOGLE_CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
GOOGLE_TOKEN_FILE = os.getenv("GOOGLE_TOKEN_FILE") or str(OUTPUT_DIR / "gdrive_token.json")
GDRIVE_WATCH_INTERVAL_SECONDS = int(os.getenv("GDRIVE_WATCH_INTERVAL_SECONDS", "60"))

SKIP_DUPLICATE_RESUMES = os.getenv("SKIP_DUPLICATE_RESUMES", "true").lower() in ("1", "true", "yes")
DUPLICATE_HASH_MODE = os.getenv("DUPLICATE_HASH_MODE", "bytes")  # bytes | text

ENABLE_EVALUATION_MEMORY = os.getenv("ENABLE_EVALUATION_MEMORY", "true").lower() in ("1", "true", "yes")

APIFY_ACTOR_ID = os.getenv("APIFY_ACTOR_ID", "bebity/linkedin-premium-actor")
