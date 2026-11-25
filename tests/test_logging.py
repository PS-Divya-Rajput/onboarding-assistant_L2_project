"""Unit tests for the centralized logging and audit trail system.

Tests:
- Log file creation and formatting in logs/
- Recent log reading and level filtering (INFO, WARNING, ERROR)
- Audit log extraction from SQLite
- CLI subcommands for logs and audit
"""

from __future__ import annotations

import logging
import subprocess
import sys
from pathlib import Path

from logging_config import (
    LOG_FILE_PATH,
    get_audit_records,
    get_logger,
    read_recent_logs,
    setup_logging,
)
from mcp_server.db import init_db, record_audit


def test_setup_logging_creates_file(tmp_path: Path):
    """Verify setup_logging initializes log file on disk."""
    custom_log = tmp_path / "test_app.log"
    test_logger = setup_logging(log_level=logging.INFO, log_file=custom_log)
    test_logger.info("Test log line alpha")
    test_logger.warning("Test log line beta")

    assert custom_log.exists()
    content = custom_log.read_text(encoding="utf-8")
    assert "Test log line alpha" in content
    assert "Test log line beta" in content
    assert "[INFO]" in content
    assert "[WARNING]" in content


def test_read_recent_logs_and_level_filter(tmp_path: Path):
    """Verify reading and filtering log entries by level."""
    test_log = tmp_path / "filter_test.log"
    with open(test_log, "w", encoding="utf-8") as f:
        f.write("2026-11-18 10:00:00 [INFO] [test] Info message\n")
        f.write("2026-11-18 10:00:01 [WARNING] [test] Warning message\n")
        f.write("2026-11-18 10:00:02 [ERROR] [test] Error message\n")

    # Read all
    all_lines = read_recent_logs(max_lines=10, level_filter="ALL", log_file=test_log)
    assert len(all_lines) == 3

    # Filter WARNING
    warn_lines = read_recent_logs(max_lines=10, level_filter="WARNING", log_file=test_log)
    assert len(warn_lines) == 1
    assert "Warning message" in warn_lines[0]

    # Filter ERROR
    err_lines = read_recent_logs(max_lines=10, level_filter="ERROR", log_file=test_log)
    assert len(err_lines) == 1
    assert "Error message" in err_lines[0]


def test_get_audit_records():
    """Verify querying audit log records from SQLite."""
    init_db()
    record_audit(
        tool="test_audit_tool",
        args_sha256="abc123sha",
        status="success",
        bytes_returned=1024,
        redactions=1,
    )
    records = get_audit_records(limit=10)
    assert len(records) >= 1
    latest = records[0]
    assert latest["tool"] == "test_audit_tool"
    assert latest["args_sha256"] == "abc123sha"
    assert latest["status"] == "success"
    assert latest["bytes_returned"] == 1024
    assert latest["redactions"] == 1


def test_cli_logs_and_audit():
    """Verify 'python cli.py logs' and 'python cli.py audit' run cleanly."""
    python_bin = sys.executable
    cli_file = str(Path(__file__).resolve().parent.parent / "cli.py")

    # 1. Test cli.py logs
    p_logs = subprocess.run([python_bin, cli_file, "logs", "--lines", "10"], capture_output=True, text=True, check=False)
    assert p_logs.returncode == 0
    assert "Onboarding Assistant Logs" in p_logs.stdout

    # 2. Test cli.py audit
    p_audit = subprocess.run([python_bin, cli_file, "audit", "--limit", "5"], capture_output=True, text=True, check=False)
    assert p_audit.returncode == 0
    assert "MCP Security & Audit Trail" in p_audit.stdout

