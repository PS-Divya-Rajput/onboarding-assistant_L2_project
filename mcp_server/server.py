"""Custom Model Context Protocol (MCP) server for Onboarding assistant.

Exposes 9 tools (5 live GitHub tools, 4 local tools) and handbook resources over stdio.
Enforces data governance, redaction, and strict dry_run safety on write tools.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Literal, Optional

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from mcp.server.mcpserver import MCPServer
from mcp_server.privacy import is_path_denied, redact_string
from mcp_server.schemas import (
    BuildErrorDiagnosticResult,
    CodeOwnerResult,
    CohortProgressResult,
    DiagnoseEnvironmentResult,
    DirectoryListingResult,
    GoodFirstIssuesResult,
    LogQuestionResult,
    MarkTaskDoneResult,
    OnboardingProgressResult,
    PRPreflightResult,
    RecentPRsResult,
    RepoOverviewResult,
    SearchDocsResult,
    SmartEscalationResult,
)
from mcp_server.tools.live_repo_tools import get_directory_listing, get_repo_overview
from mcp_server.tools.live_issue_tools import get_recent_prs, list_good_first_issues
from mcp_server.tools.live_owner_tools import find_code_owners
from mcp_server.tools.live_review_tools import check_pr_preflight
from mcp_server.tools.local_diagnostic_tools import diagnose_build_error
from mcp_server.tools.local_doctor_tools import diagnose_local_environment
from mcp_server.tools.local_escalation_tools import (
    generate_smart_escalation,
    get_cohort_progress,
)
from mcp_server.tools.local_handbook_tools import search_onboarding_docs
from mcp_server.tools.local_progress_tools import (
    get_onboarding_progress,
    log_question,
    mark_task_done,
)

HANDBOOK_ROOT = PROJECT_ROOT / "data" / "handbook"

# Initialize FastMCP / MCPServer instance
server = MCPServer(
    name="onboarding-assistant",
    instructions="Assists software engineers onboarding to the target repository.",
)


# ==============================================================================
# Live GitHub Tools (5 tools)
# ==============================================================================

@server.tool(name="get_repo_overview")
def tool_get_repo_overview() -> RepoOverviewResult:
    """Fetch high-level repository metadata, primary languages, license, and sanitized README excerpt."""
    return get_repo_overview()


@server.tool(name="get_directory_listing")
def tool_get_directory_listing(path: str = "") -> DirectoryListingResult:
    """List directory entries (file names, directories, sizes) for a given repo path without reading contents."""
    return get_directory_listing(path=path)


@server.tool(name="list_good_first_issues")
def tool_list_good_first_issues(limit: int = 5, exclude_with_open_pr: bool = True) -> GoodFirstIssuesResult:
    """List unassigned beginner-friendly issues, excluding issues with active pull requests."""
    return list_good_first_issues(limit=limit, exclude_with_open_pr=exclude_with_open_pr)


@server.tool(name="find_code_owners")
def tool_find_code_owners(path: str) -> CodeOwnerResult:
    """Find code owners for a file or directory using CODEOWNERS rules or recent commit activity."""
    return find_code_owners(path=path)


@server.tool(name="get_recent_prs")
def tool_get_recent_prs(state: str = "open", limit: int = 8) -> RecentPRsResult:
    """Inspect recent pull requests metadata (titles, authors, status) without reading diffs."""
    return get_recent_prs(state=state, limit=limit)


# ==============================================================================
# Local Handbook & Progress Tools (4 tools)
# ==============================================================================

@server.tool(name="search_onboarding_docs")
def tool_search_onboarding_docs(query: str, top_k: int = 4) -> SearchDocsResult:
    """Search repository onboarding documentation, guides, FAQs, and setup steps."""
    return search_onboarding_docs(query=query, top_k=top_k)


@server.tool(name="get_onboarding_progress")
def tool_get_onboarding_progress(user_id: str) -> OnboardingProgressResult:
    """Retrieve checklist tasks, completed count, and next suggested onboarding task for a user."""
    return get_onboarding_progress(user_id=user_id)


@server.tool(name="mark_task_done")
def tool_mark_task_done(user_id: str, task_id: int, dry_run: bool = True) -> MarkTaskDoneResult:
    """Mark an onboarding checklist task as complete. Defaults to dry_run=True (proposal preview only)."""
    return mark_task_done(user_id=user_id, task_id=task_id, dry_run=dry_run)


@server.tool(name="log_question")
def tool_log_question(
    user_id: str,
    question: str,
    answered_from: Literal["handbook", "live", "none"] = "none",
    resolved: bool = False,
    dry_run: bool = True,
) -> LogQuestionResult:
    """Log an onboarding question and resolution status. Defaults to dry_run=True (proposal preview only)."""
    return log_question(
        user_id=user_id,
        question=question,
        answered_from=answered_from,
        resolved=resolved,
        dry_run=dry_run,
    )


# ==============================================================================
# Enhanced Tools: Environment Doctor, Review Pre-Flight, Error Diagnostics & Escalations
# ==============================================================================

@server.tool(name="diagnose_local_environment")
def tool_diagnose_local_environment() -> DiagnoseEnvironmentResult:
    """Audit the local developer machine environment (Python, Rust, Git, virtualenv) against prerequisites."""
    return diagnose_local_environment()


@server.tool(name="check_pr_preflight")
def tool_check_pr_preflight(
    pr_number: Optional[int] = None,
    title: str = "",
    body: str = "",
    files_changed: Optional[list[str]] = None,
) -> PRPreflightResult:
    """Audit a pull request for template completeness, test coverage, and security compliance before senior review."""
    return check_pr_preflight(
        pr_number=pr_number,
        title=title,
        body=body,
        files_changed=files_changed,
    )


@server.tool(name="diagnose_build_error")
def tool_diagnose_build_error(error_log: str) -> BuildErrorDiagnosticResult:
    """Analyze compiler or test error logs and generate remediation guidance and code owner contacts."""
    return diagnose_build_error(error_log=error_log)


@server.tool(name="generate_smart_escalation")
def tool_generate_smart_escalation(
    user_id: str,
    question: str,
    steps_attempted: Optional[list[str]] = None,
    path_context: Optional[str] = None,
) -> SmartEscalationResult:
    """Generate a structured, zero-effort Senior Escalation Packet formatted for Slack, Teams, or GitHub."""
    return generate_smart_escalation(
        user_id=user_id,
        question=question,
        steps_attempted=steps_attempted,
        path_context=path_context,
    )


@server.tool(name="get_cohort_progress")
def tool_get_cohort_progress() -> CohortProgressResult:
    """Aggregate onboarding velocity, completion percentages, and bottlenecks across all engineers for leads."""
    return get_cohort_progress()


# ==============================================================================
# MCP Resources (handbook://<relative/path>)
# ==============================================================================

@server.resource("handbook://{path}")
def resource_read_handbook_doc(path: str) -> str:
    """Read a sanitized markdown document from the onboarding handbook."""
    clean_path = path.replace("\\", "/").strip("/")
    if is_path_denied(clean_path):
        return "# Access Denied\nAccess to this document is denied by privacy policy."

    target_file = HANDBOOK_ROOT / clean_path
    if not target_file.exists() or not target_file.is_file():
        return f"# Not Found\nHandbook document '{clean_path}' does not exist."

    try:
        with open(target_file, "r", encoding="utf-8") as f:
            content = f.read()
        redacted_content, _ = redact_string(content)
        return redacted_content
    except Exception as exc:
        return f"# Error\nFailed to read document '{clean_path}': {type(exc).__name__}: {exc}"


def main() -> None:
    """Run the MCP server over stdio transport."""
    server.run(transport="stdio")


if __name__ == "__main__":
    main()

