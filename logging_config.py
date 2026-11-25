"""Central logging configuration for Onboarding assistant.

Provides rotating file-based logging and safe stderr streaming.
Ensures sys.stdout is never polluted so MCP stdio JSON-RPC transport remains intact.
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional

ROOT_DIR = Path(__file__).resolve().parent
LOGS_DIR = ROOT_DIR / "logs"
LOG_FILE_PATH = LOGS_DIR / "onboarding.log"

_LOGGING_INITIALIZED = False


def setup_logging(
    log_level: int = logging.INFO,
    log_file: Optional[Path] = None,
    force: bool = False,
) -> logging.Logger:
    """Configure centralized file and stderr logging."""
    global _LOGGING_INITIALIZED
    
    target_file = log_file or LOG_FILE_PATH
    target_file.parent.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger()
    
    # Avoid duplicate handlers on Streamlit reruns for the default log file
    if not force and log_file is None and _LOGGING_INITIALIZED and any(isinstance(h, RotatingFileHandler) for h in root_logger.handlers):
        return logging.getLogger("onboarding_assistant")

    root_logger.setLevel(log_level)

    log_format = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 1. Rotating File Handler (5 MB per file, max 5 backups)
    file_handler = RotatingFileHandler(
        filename=str(target_file),
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(log_format)
    root_logger.addHandler(file_handler)

    # 2. Console Stream Handler (Strictly stderr so stdout remains clean for MCP JSON-RPC)
    if not any(isinstance(h, logging.StreamHandler) and not isinstance(h, RotatingFileHandler) for h in root_logger.handlers):
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(log_format)
        root_logger.addHandler(console_handler)

    if log_file is None:
        _LOGGING_INITIALIZED = True
    app_logger = logging.getLogger("onboarding_assistant")
    app_logger.info("Centralized logging initialized. Writing logs to %s", target_file)
    return app_logger


def get_logger(name: str) -> logging.Logger:
    """Return a scoped logger under the onboarding_assistant namespace."""
    if not _LOGGING_INITIALIZED:
        setup_logging()
    return logging.getLogger(name)


def read_recent_logs(
    max_lines: int = 150,
    level_filter: Optional[str] = None,
    log_file: Optional[Path] = None,
) -> List[str]:
    """Read the most recent log entries from disk, optionally filtered by level."""
    target_file = log_file or LOG_FILE_PATH
    if not target_file.exists():
        return []

    try:
        with open(target_file, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except Exception:
        return []

    if level_filter and level_filter.upper() != "ALL":
        target_token = f"[{level_filter.upper()}]"
        lines = [line for line in lines if target_token in line]

    return [line.rstrip("\r\n") for line in lines[-max_lines:]]


def get_audit_records(limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieve the latest audit log records from SQLite."""
    from mcp_server.db import get_db_connection

    records: List[Dict[str, Any]] = []
    try:
        with get_db_connection() as conn:
            rows = conn.execute(
                """
                SELECT id, ts, tool, args_sha256, status, bytes_returned, redactions
                FROM audit_log
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
            for r in rows:
                records.append({
                    "id": r["id"],
                    "ts": r["ts"],
                    "tool": r["tool"],
                    "args_sha256": r["args_sha256"],
                    "status": r["status"],
                    "bytes_returned": r["bytes_returned"],
                    "redactions": r["redactions"],
                })
    except Exception as exc:
        logging.getLogger("onboarding_assistant").error("Failed to query audit_log: %s", exc)

    return records

