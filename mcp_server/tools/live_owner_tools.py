"""Live code ownership discovery tool using CODEOWNERS parsing and 90-day commit fallback.

Uses pathspec for accurate gitignore-style pattern matching with last-rule-wins semantics.
Falls back to commit history when official CODEOWNERS are not defined, explicitly labelling
inferred ownership as a heuristic to maintain complete explainability.
"""

from __future__ import annotations

import base64
import datetime
from collections import Counter
from typing import List, Optional, Tuple
import pathspec
from config import config
from mcp_server.github_client import github_client
from mcp_server.privacy import audit_tool_call, is_path_denied
from mcp_server.schemas import CodeOwnerResult, SourceRef, ToolError

POSSIBLE_CODEOWNERS_PATHS = [
    ".github/CODEOWNERS",
    "CODEOWNERS",
    "docs/CODEOWNERS",
]

BOT_NAMES = {
    "github-actions[bot]",
    "dependabot[bot]",
    "renovate[bot]",
    "pre-commit-ci[bot]",
    "github-actions",
    "dependabot",
}


def _parse_codeowners_content(content: str, query_path: str) -> Optional[Tuple[List[str], str]]:
    """Parse CODEOWNERS text and find the matching rule with last-match-wins semantics."""
    rules: List[Tuple[pathspec.PathSpec, List[str], str]] = []
    # Normalize query path for pathspec (forward slashes, no leading slash)
    norm_query = query_path.strip().replace("\\", "/").lstrip("/")

    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        pattern = parts[0]
        owners = parts[1:]
        try:
            spec = pathspec.PathSpec.from_lines("gitignore", [pattern])
            rules.append((spec, owners, pattern))
        except Exception:
            continue

    # Last matching rule wins
    for spec, owners, pattern in reversed(rules):
        if spec.match_file(norm_query):
            return owners, pattern

    return None


def _fetch_codeowners_file(target_repo: str) -> Optional[Tuple[str, str]]:
    """Attempt to fetch CODEOWNERS from standard repository locations."""
    for path in POSSIBLE_CODEOWNERS_PATHS:
        status, data, _ = github_client.get(f"repos/{target_repo}/contents/{path}")
        if status == 200 and isinstance(data, dict):
            raw_content = data.get("content", "")
            if raw_content:
                try:
                    text = base64.b64decode(raw_content).decode("utf-8", errors="replace")
                    return text, path
                except Exception:
                    continue
    return None


def _infer_owners_from_commits(target_repo: str, path: str) -> Tuple[List[str], Optional[str]]:
    """Infer top 3 non-bot committers for a path over the last 90 days."""
    since_date = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=90)).isoformat()
    endpoint = f"repos/{target_repo}/commits"
    params = {"path": path, "since": since_date, "per_page": 50}

    status, commits_data, _ = github_client.get(endpoint, params=params)
    if status != 200 or not isinstance(commits_data, list):
        return [], None

    author_counts: Counter[str] = Counter()
    for item in commits_data:
        # Check author object first, then committer
        author_obj = item.get("author") or item.get("committer")
        if isinstance(author_obj, dict):
            login = author_obj.get("login")
            if login:
                login_clean = login.strip()
                login_lower = login_clean.lower()
                if login_lower not in BOT_NAMES and not login_lower.endswith("[bot]"):
                    author_counts[login_clean] += 1

    top_authors = [login for login, _ in author_counts.most_common(3)]
    note = (
        "Inferred from top 3 non-bot committers over the last 90 days. "
        "This is an automated heuristic, NOT official code ownership."
    )
    return top_authors, note


def find_code_owners(path: str) -> CodeOwnerResult:
    """Determine official code owners via CODEOWNERS or infer from recent commit history."""
    target_repo = config.target_repo
    clean_path = path.strip().replace("\\", "/").strip("/")

    if is_path_denied(clean_path):
        res = CodeOwnerResult(
            path=clean_path,
            owners=[],
            method="codeowners",
            error=ToolError(
                code="path_blocked",
                message=f"Access to path '{clean_path}' is denied by repository security policy.",
            ),
            source_refs=[],
        )
        audit_tool_call("find_code_owners", {"path": path}, "blocked", res, 0)
        return res

    source_refs = [
        SourceRef(
            id="S1",
            kind="live",
            label=f"GitHub: {target_repo}",
            url=f"https://github.com/{target_repo}",
        )
    ]

    # 1. Look for official CODEOWNERS file
    codeowners_match = _fetch_codeowners_file(target_repo)
    if codeowners_match:
        content, found_path = codeowners_match
        parsed = _parse_codeowners_content(content, clean_path)
        if parsed:
            owners, rule = parsed
            source_refs.append(
                SourceRef(
                    id="S2",
                    kind="live",
                    label=f"CODEOWNERS ({found_path})",
                    url=f"https://github.com/{target_repo}/blob/main/{found_path}",
                )
            )
            res = CodeOwnerResult(
                path=clean_path,
                owners=owners,
                method="codeowners",
                rule=rule,
                note=f"Official ownership defined by rule '{rule}' in {found_path}.",
                source_refs=source_refs,
            )
            audit_tool_call("find_code_owners", {"path": path}, "success", res, 0)
            return res

    # 2. Fall back to inferred ownership from 90-day commits
    inferred_owners, note = _infer_owners_from_commits(target_repo, clean_path)
    source_refs.append(
        SourceRef(
            id="S2",
            kind="live",
            label=f"Git Commit History: {clean_path}",
            url=f"https://github.com/{target_repo}/commits/main/{clean_path}",
        )
    )

    res = CodeOwnerResult(
        path=clean_path,
        owners=inferred_owners,
        method="inferred",
        rule=None,
        note=note or "No active committers found in the last 90 days for this path.",
        source_refs=source_refs,
    )
    audit_tool_call("find_code_owners", {"path": path}, "success", res, 0)
    return res
