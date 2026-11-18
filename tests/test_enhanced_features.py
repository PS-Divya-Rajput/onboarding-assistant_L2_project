"""Unit and integration tests for enhanced developer & senior onboarding features.

Tests:
- Local Environment Doctor tool (diagnose_local_environment)
- Automated PR Pre-Flight Check tool (check_pr_preflight)
- Build Error & Compiler Diagnostic tool (diagnose_build_error)
- Smart Escalation Packet & Cohort Analytics (generate_smart_escalation, get_cohort_progress)
- Persona-adapted system prompts (get_system_prompt)
- CLI entrypoint subcommands (doctor, preflight, progress, cohort)
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
import pytest

from agent.system_prompt import get_persona_guidance, get_system_prompt
from mcp_server.schemas import (
    BuildErrorDiagnosticResult,
    CohortProgressResult,
    DiagnoseEnvironmentResult,
    PRPreflightResult,
    SmartEscalationResult,
)
from mcp_server.tools.live_review_tools import check_pr_preflight
from mcp_server.tools.local_diagnostic_tools import diagnose_build_error
from mcp_server.tools.local_doctor_tools import diagnose_local_environment
from mcp_server.tools.local_escalation_tools import (
    generate_smart_escalation,
    get_cohort_progress,
)


def test_diagnose_local_environment():
    """Verify local environment doctor audits Python, Git, and virtualenv."""
    res = diagnose_local_environment()
    assert isinstance(res, DiagnoseEnvironmentResult)
    assert len(res.checks) >= 4

    check_names = [c.name for c in res.checks]
    assert "Python Version" in check_names
    assert "Virtual Environment" in check_names
    assert "Git CLI" in check_names
    assert res.os_platform != ""
    assert len(res.source_refs) == 1
    assert res.source_refs[0].id == "DOC-ENV"


def test_check_pr_preflight_passing():
    """Verify PR preflight passes on compliant PR parameters."""
    res = check_pr_preflight(
        pr_number=None,
        title="Add AST visitor support for match expressions",
        body="## Summary\nCloses #101 by implementing AST match visitor.\n## Test Plan\ncargo test -p ruff_python_parser",
        files_changed=["crates/ruff_python_parser/src/visitor.rs", "crates/ruff_python_parser/tests/fixtures/match.py"],
    )
    assert isinstance(res, PRPreflightResult)
    assert res.ready_for_review is True
    assert len(res.sensitive_paths_touched) == 0
    assert len(res.senior_review_checklist) >= 3


def test_check_pr_preflight_blocks_denylist_paths():
    """Verify PR preflight detects and blocks restricted paths (.env, workflows)."""
    res = check_pr_preflight(
        pr_number=None,
        title="Fix production configuration",
        body="## Summary\nUpdating secret configs.\n## Test Plan\nNone",
        files_changed=["crates/ruff/src/main.rs", ".env", ".github/workflows/deploy.yml"],
    )
    assert isinstance(res, PRPreflightResult)
    assert res.ready_for_review is False
    assert len(res.sensitive_paths_touched) == 2
    assert ".env" in res.sensitive_paths_touched
    assert ".github/workflows/deploy.yml" in res.sensitive_paths_touched


def test_diagnose_build_error_borrow_checker():
    """Verify compiler diagnostics detects Rust borrow-checker errors."""
    error_log = """
    error[E0382]: use of moved value: `tokens`
       --> crates/ruff_python_parser/src/lexer.rs:45:12
        |
     42 |     let tokens = tokenize(source);
        |         ------ move occurs because `tokens` has type `Vec<Token>`
     45 |     process(tokens);
        |             ^^^^^^ value used here after move
    """
    res = diagnose_build_error(error_log)
    assert isinstance(res, BuildErrorDiagnosticResult)
    assert res.error_type == "rust_borrow_checker"
    assert "Borrow Checker" in res.summary
    assert len(res.suggested_fixes) >= 2


def test_diagnose_build_error_missing_import():
    """Verify compiler diagnostics detects Python missing import error."""
    error_log = "ModuleNotFoundError: No module named 'respx'"
    res = diagnose_build_error(error_log)
    assert isinstance(res, BuildErrorDiagnosticResult)
    assert res.error_type == "python_import_error"
    assert "respx" in res.summary
    assert any("pip install" in f for f in res.suggested_fixes)


def test_generate_smart_escalation():
    """Verify smart escalation generates markdown packet with owners and user info."""
    res = generate_smart_escalation(
        user_id="user_ravi",
        question="How do I resolve linking error during cargo build?",
        steps_attempted=["Ran cargo build", "Checked docs/contributing.md"],
        path_context="crates/ruff_python_parser",
    )
    assert isinstance(res, SmartEscalationResult)
    assert "Ravi Patel" in res.developer_name
    assert "Senior Escalation Packet" in res.escalation_packet_markdown
    assert "crates/ruff_python_parser" in res.escalation_packet_markdown
    assert len(res.owners) >= 1
    assert "slack_payload" in res.model_dump()


def test_get_cohort_progress():
    """Verify cohort progress aggregates all 3 seeded developers."""
    res = get_cohort_progress()
    assert isinstance(res, CohortProgressResult)
    assert len(res.cohort) == 3
    user_ids = [m.user_id for m in res.cohort]
    assert "user_ravi" in user_ids
    assert "user_elena" in user_ids
    assert "user_marcus" in user_ids
    assert 0.0 <= res.average_completion_pct <= 100.0


def test_persona_prompt_adaptation():
    """Verify system prompt adapts tone and guidance for different personas."""
    junior_prompt = get_system_prompt(user_role="Junior Contributor")
    assert "Junior Contributor" in junior_prompt
    assert "step-by-step guidance" in junior_prompt

    systems_prompt = get_system_prompt(user_role="Systems Programmer")
    assert "Systems" in systems_prompt
    assert "command-first" in systems_prompt

    lead_prompt = get_system_prompt(user_role="Team Lead")
    assert "Team Lead" in lead_prompt
    assert "review readiness" in lead_prompt


def test_cli_subcommands():
    """Verify CLI subcommands (doctor, preflight, progress, cohort) execute cleanly."""
    python_bin = sys.executable
    cli_file = str(Path(__file__).resolve().parent.parent / "cli.py")

    # 1. Doctor command
    p_doc = subprocess.run([python_bin, cli_file, "doctor"], capture_output=True, text=True, check=False)
    assert p_doc.returncode == 0
    assert "Local Environment Doctor Audit" in p_doc.stdout

    # 2. Preflight command
    p_pref = subprocess.run([python_bin, cli_file, "preflight", "--title", "Add AST visitor tests"], capture_output=True, text=True, check=False)
    assert p_pref.returncode == 0
    assert "PR Pre-Flight Audit" in p_pref.stdout

    # 3. Progress command
    p_prog = subprocess.run([python_bin, cli_file, "progress", "--user", "user_ravi"], capture_output=True, text=True, check=False)
    assert p_prog.returncode == 0
    assert "Onboarding Milestone Progress (user_ravi)" in p_prog.stdout

    # 4. Cohort command
    p_coh = subprocess.run([python_bin, cli_file, "cohort"], capture_output=True, text=True, check=False)
    assert p_coh.returncode == 0
    assert "Cohort Onboarding Velocity" in p_coh.stdout

