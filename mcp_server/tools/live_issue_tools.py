"""Live GitHub issues and pull requests query tools.

Filters pull requests out of issues endpoints, matches good-first-issue labels,
excludes issues with active PRs, sanitizes untrusted text, and redacts sensitive data.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Set
from config import config
from mcp_server.github_client import github_client
from mcp_server.privacy import (
    audit_tool_call,
    redact_string,
    sanitize_untrusted_text,
)
from mcp_server.schemas import (
    GoodFirstIssuesResult,
    IssueItem,
    PullRequestItem,
    RecentPRsResult,
    SourceRef,
    ToolError,
)

# Regex to detect referenced issue numbers in PR titles and descriptions
PR_ISSUE_REF_PATTERN = re.compile(r"(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?|#)\s*#?(\d+)", re.IGNORECASE)


def _extract_referenced_issues_from_prs(prs: List[Dict[str, Any]]) -> Set[int]:
    """Find issue numbers referenced by open PR titles and descriptions."""
    referenced: Set[int] = set()
    for pr in prs:
        title = pr.get("title", "") or ""
        body = pr.get("body", "") or ""
        text = f"{title} {body}"
        for match in PR_ISSUE_REF_PATTERN.finditer(text):
            try:
                referenced.add(int(match.group(1)))
            except ValueError:
                pass
    return referenced


def list_good_first_issues(limit: int = 5, exclude_with_open_pr: bool = True) -> GoodFirstIssuesResult:
    """Find open, unassigned newcomer-friendly issues, optionally excluding those with active PRs."""
    target_repo = config.target_repo
    source_refs = [
        SourceRef(
            id="S1",
            kind="live",
            label=f"GitHub Issues: {target_repo}",
            url=f"https://github.com/{target_repo}/issues",
        )
    ]

    # 1. If excluding issues with open PRs, fetch open PRs first
    referenced_issue_numbers: Set[int] = set()
    if exclude_with_open_pr:
        pr_status, prs_data, _ = github_client.get(
            f"repos/{target_repo}/pulls", params={"state": "open", "per_page": 50}
        )
        if pr_status == 200 and isinstance(prs_data, list):
            referenced_issue_numbers = _extract_referenced_issues_from_prs(prs_data)

    # 2. Query issues matching good first labels
    all_issues: List[IssueItem] = []
    seen_numbers: Set[int] = set()
    total_redactions = 0

    for label in config.good_first_labels:
        params = {
            "state": "open",
            "labels": label,
            "per_page": 30,
            "sort": "created",
            "direction": "desc",
        }
        status, issues_data, _ = github_client.get(f"repos/{target_repo}/issues", params=params)
        if status != 200 or not isinstance(issues_data, list):
            continue

        for raw_issue in issues_data:
            # Drop items that are pull requests (GitHub API pitfall)
            if "pull_request" in raw_issue:
                continue

            num = raw_issue.get("number")
            if not num or num in seen_numbers:
                continue

            # Must be unassigned
            assignees = raw_issue.get("assignees", [])
            assignee = raw_issue.get("assignee")
            if assignees or assignee:
                continue

            # Exclude if referenced in an open PR
            if exclude_with_open_pr and num in referenced_issue_numbers:
                continue

            seen_numbers.add(num)
            raw_title = raw_issue.get("title", "")
            clean_title = sanitize_untrusted_text(raw_title, max_chars=120)
            redacted_title, r_count = redact_string(clean_title)
            total_redactions += r_count

            labels_list = [
                lbl.get("name", "") if isinstance(lbl, dict) else str(lbl)
                for lbl in raw_issue.get("labels", [])
            ]

            all_issues.append(
                IssueItem(
                    number=num,
                    title=redacted_title,
                    labels=labels_list,
                    comment_count=raw_issue.get("comments", 0),
                    created_at=raw_issue.get("created_at", ""),
                    url=raw_issue.get("html_url", f"https://github.com/{target_repo}/issues/{num}"),
                )
            )

            if len(all_issues) >= limit:
                break

        if len(all_issues) >= limit:
            break

    # Build response source refs for found issues
    for idx, iss in enumerate(all_issues, start=2):
        source_refs.append(
            SourceRef(
                id=f"S{idx}",
                kind="live",
                label=f"Issue #{iss.number}: {iss.title}",
                url=iss.url,
            )
        )

    res = GoodFirstIssuesResult(
        issues=all_issues[:limit],
        total_found=len(all_issues),
        source_refs=source_refs,
    )
    audit_tool_call("list_good_first_issues", {"limit": limit, "exclude_with_open_pr": exclude_with_open_pr}, "success", res, total_redactions)
    return res


def get_recent_prs(state: str = "open", limit: int = 8) -> RecentPRsResult:
    """Fetch metadata for recent pull requests without reading diffs or source patches."""
    target_repo = config.target_repo
    source_refs = [
        SourceRef(
            id="S1",
            kind="live",
            label=f"GitHub Pull Requests: {target_repo}",
            url=f"https://github.com/{target_repo}/pulls",
        )
    ]

    valid_state = state if state in ("open", "closed", "all") else "open"
    params = {"state": valid_state, "per_page": min(limit, 30), "sort": "created", "direction": "desc"}

    status, prs_data, _ = github_client.get(f"repos/{target_repo}/pulls", params=params)
    if status != 200 or not isinstance(prs_data, list):
        err_msg = prs_data.get("error", {}).get("message") if isinstance(prs_data, dict) else str(prss_data if 'prss_data' in locals() else prs_data)
        res = RecentPRsResult(
            error=ToolError(code="pr_fetch_failed", message=f"Failed to fetch recent PRs: {err_msg}"),
            source_refs=source_refs,
        )
        audit_tool_call("get_recent_prs", {"state": state, "limit": limit}, "error", res, 0)
        return res

    prs: List[PullRequestItem] = []
    total_redactions = 0

    for raw_pr in prs_data[:limit]:
        num = raw_pr.get("number", 0)
        raw_title = raw_pr.get("title", "")
        clean_title = sanitize_untrusted_text(raw_title, max_chars=120)
        redacted_title, r_count = redact_string(clean_title)
        total_redactions += r_count

        user_info = raw_pr.get("user")
        author = user_info.get("login", "") if isinstance(user_info, dict) else ""

        labels_list = [
            lbl.get("name", "") if isinstance(lbl, dict) else str(lbl)
            for lbl in raw_pr.get("labels", [])
        ]

        prs.append(
            PullRequestItem(
                number=num,
                title=redacted_title,
                author=author,
                labels=labels_list,
                state=raw_pr.get("state", "open"),
                created_at=raw_pr.get("created_at", ""),
                merged_at=raw_pr.get("merged_at"),
                url=raw_pr.get("html_url", f"https://github.com/{target_repo}/pull/{num}"),
            )
        )

    res = RecentPRsResult(prs=prs, total_count=len(prs), source_refs=source_refs)
    audit_tool_call("get_recent_prs", {"state": state, "limit": limit}, "success", res, total_redactions)
    return res

