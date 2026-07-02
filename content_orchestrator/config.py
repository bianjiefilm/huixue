# Pipeline Configuration
# ============================================================
# Lightweight CLI tool for course content generation workflow.
#
# Env: reads from backend/.env
# Usage: python pipeline.py <command> [args]

import os
from pathlib import Path

from dotenv import load_dotenv

_BACKEND_ENV = Path(__file__).parent.parent / "backend" / ".env"
if not _BACKEND_ENV.exists():
    raise FileNotFoundError(f"backend/.env not found: {_BACKEND_ENV}")
load_dotenv(_BACKEND_ENV)

# --- Database ------------------------------------------------------------
DATABASE_URL: str = os.environ.get("DATABASE_URL", "")
if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL not found in backend/.env. "
        "Please set it before running pipeline."
    )

# --- Container eval ------------------------------------------------------
CONTAINER_EVAL_ENABLED: bool = True
CONTAINER_TIMEOUT_SECONDS: int = 30

# --- Dry run ------------------------------------------------------------
# True: log everything, print DB writes, never commit to DB
# False: fully operational
DRY_RUN: bool = True

# --- Logging ------------------------------------------------------------
LOG_LEVEL: str = "INFO"
BASE_DIR: Path = Path(__file__).parent
LOGS_DIR: Path = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# --- Output -------------------------------------------------------------
OUTPUT_DIR: Path = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)
