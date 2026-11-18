"""Automated PR Pre-Flight Check and Senior Review Readiness tool for Onboarding assistant.

Audits open pull requests against project standards (PR template adherence, test inclusion,
privacy/sensitive path touch, and senior reviewer checklist) before requesting maintainer review.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from config import config
from mcp_server.github_client import github_client
from mcp_server.privacy import audit_tool_call, is_path_denied, sanitize_untrusted_text
from mcp_server.schemas import (
    PRPreflightCheckItem,
    PRPreflightResult,
    SourceRef,
    ToolError,
)

# Common test file patterns
TEST_PATH_PATTERNS = [
    re.compile(r"(^|/)(tests?|testing)/", re.IGNORECASE),
    re.compile(r"(_test|\.test|test_)\.(rs|py|ts|js|go)$", re.IGNORECASE),
    re.compile(r"/tests/fixtures/", re.IGNORECASE),
]


def _is_test_file(path: str) -> bool:
    clean = path.strip().replace("\\", "/")
    return any(p.search(clean) for p in TEST_PATH_PATTERNS)


def check_pr_preflight(
    pr_number: Optional[int] = None,
    title: str = "",
    body: str = "",
    files_changed: Optional[List[str]] = None,
) -> PRPreflightResult:
    """Audit a pull request for template completeness, test coverage, and security compliance."""
    effective_title = title
    effective_body = body
    effective_files = list(files_changed or [])
    pr_url = None

    # If pr_number is specified, fetch live PR details from GitHub
    if pr_number is not None and pr_number > 0:
        try:
            status, pr_data, _ = github_client.get(f"/repos/{config.target_repo}/pulls/{pr_number}")
            if status < 400 and isinstance(pr_data, dict):
                effective_title = effective_title or pr_data.get("title", "")
                effective_body = effective_body or pr_data.get("body", "") or ""
                pr_url = pr_data.get("html_url")
        except Exception:
            pass

        # Try fetching files changed
        if not effective_files:
            try:
                status, files_data, _ = github_client.get(f"/repos/{config.target_repo}/pulls/{pr_number}/files")
                if status < 400 and isinstance(files_data, list):
                    effective_files = [f.get("filename", "") for f in files_data if isinstance(f, dict) and "filename" in f]
            except Exception:
                pass

    checks: List[PRPreflightCheckItem] = []
    sensitive_paths: List[str] = []
    senior_checklist: List[str] = []

    # 1. Title format check
    clean_title = sanitize_untrusted_text(effective_title.strip()) if effective_title else ""
    if len(clean_title) >= 10:
        checks.append(PRPreflightCheckItem(
            rule="PR Title Clarity",
            passed=True,
            detail=f"Descriptive title provided ({len(clean_title)} chars).",
            recommendation=None,
        ))
    else:
        checks.append(PRPreflightCheckItem(
            rule="PR Title Clarity",
            passed=False,
            detail="Title is missing or too short (< 10 chars).",
            recommendation="Provide an imperative title describing the change (e.g. 'Add AST visitor for match expressions').",
        ))

    # 2. PR Template / Summary completeness
    lower_body = (effective_body or "").lower()
    has_summary = any(kw in lower_body for kw in ["summary", "description", "motivation", "closes #", "fixes #"])
    has_test_plan = any(kw in lower_body for kw in ["test plan", "testing", "how tested", "cargo test", "pytest"])

    if has_summary:
        checks.append(PRPreflightCheckItem(
            rule="PR Description / Summary",
            passed=True,
            detail="Summary or issue reference present.",
            recommendation=None,
        ))
    else:
        checks.append(PRPreflightCheckItem(
            rule="PR Description / Summary",
            passed=False,
            detail="No Summary, Motivation, or 'Fixes #' issue link found.",
            recommendation="Explain what this PR solves and link related issues using 'Closes #...' or 'Fixes #...'.",
        ))

    if has_test_plan:
        checks.append(PRPreflightCheckItem(
            rule="Test Plan in Description",
            passed=True,
            detail="Test plan or testing instructions documented in PR body.",
            recommendation=None,
        ))
    else:
        checks.append(PRPreflightCheckItem(
            rule="Test Plan in Description",
            passed=False,
            detail="No explicit 'Test Plan' section found in the description.",
            recommendation="Add a '## Test Plan' section specifying how reviewers can reproduce test verification.",
        ))

    # 3. Test files modified / added
    has_test_files = any(_is_test_file(f) for f in effective_files) if effective_files else has_test_plan
    if has_test_files:
        checks.append(PRPreflightCheckItem(
            rule="Test File Coverage",
            passed=True,
            detail=f"Test coverage verified (test files modified or testing plan documented).",
            recommendation=None,
        ))
    else:
        checks.append(PRPreflightCheckItem(
            rule="Test File Coverage",
            passed=False,
            detail="No test files modified in PR changeset.",
            recommendation="Add unit or integration tests verifying the fix or feature under the crates/tests directory.",
        ))

    # 4. Sensitive Paths & Security Policy
    for f in effective_files:
        if is_path_denied(f):
            sensitive_paths.append(f)

    if not sensitive_paths:
        checks.append(PRPreflightCheckItem(
            rule="Security & Policy Isolation",
            passed=True,
            detail="Zero sensitive or denylisted repository paths touched.",
            recommendation=None,
        ))
    else:
        checks.append(PRPreflightCheckItem(
            rule="Security & Policy Isolation",
            passed=False,
            detail=f"PR touches {len(sensitive_paths)} restricted path(s): {', '.join(sensitive_paths)}.",
            recommendation="Remove changes to security-denylisted paths (.env, workflows, secrets) before requesting review.",
        ))

    # 5. Build Senior Reviewer Checklist
    ready_for_review = all(c.passed for c in checks)
    senior_checklist.append("Verify code ownership alignment with .github/CODEOWNERS.")
    senior_checklist.append("Confirm all test assertions execute cleanly and avoid flaky timing.")
    if any("crates/" in f for f in effective_files):
        senior_checklist.append("Review public API signature changes for semver backward compatibility.")
    senior_checklist.append("Ensure zero hardcoded credentials or debug print statements remain.")

    source_refs = [
        SourceRef(
            id=f"PR-{pr_number}" if pr_number else "PR-PREFLIGHT",
            kind="live",
            label=f"PR Preflight #{pr_number}" if pr_number else "Local PR Preflight",
            url=pr_url,
        )
    ]

    res = PRPreflightResult(
        pr_number=pr_number,
        pr_title=clean_title or (f"Pull Request #{pr_number}" if pr_number else "Draft PR"),
        ready_for_review=ready_for_review,
        checks=checks,
        sensitive_paths_touched=sensitive_paths,
        senior_review_checklist=senior_checklist,
        source_refs=source_refs,
    )

    audit_tool_call(
        tool_name="check_pr_preflight",
        args={"pr_number": pr_number, "title": clean_title},
        status="success" if ready_for_review else "warn",
        payload_obj=res,
        redaction_count=0,
    )
    return res
