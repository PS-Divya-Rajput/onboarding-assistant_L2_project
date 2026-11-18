"""Live repository overview and directory inspection tools via GitHub REST API.

Enforces zero-source-code inspection, path denylist, output redaction, and audit logging.
"""

from __future__ import annotations

import base64
from typing import Any, Dict, List
from config import config
from mcp_server.github_client import github_client
from mcp_server.privacy import (
    audit_tool_call,
    is_path_denied,
    redact_data,
    redact_string,
)
from mcp_server.schemas import (
    DirectoryEntry,
    DirectoryListingResult,
    RepoOverviewResult,
    SourceRef,
    ToolError,
)


def get_repo_overview() -> RepoOverviewResult:
    """Fetch high-level repository metadata, primary languages, key docs presence, and README excerpt."""
    target_repo = config.target_repo
    source_url = f"https://github.com/{target_repo}"
    source_refs = [
        SourceRef(
            id="S1",
            kind="live",
            label=f"GitHub Repository: {target_repo}",
            url=source_url,
        )
    ]

    # 1. Fetch repository general details
    status, repo_data, _ = github_client.get(f"repos/{target_repo}")
    if status != 200:
        err_msg = repo_data.get("error", {}).get("message") if isinstance(repo_data, dict) else str(repo_data)
        res = RepoOverviewResult(
            error=ToolError(code="repo_fetch_failed", message=f"Failed to fetch repo metadata: {err_msg}"),
            source_refs=source_refs,
        )
        audit_tool_call("get_repo_overview", {}, "error", res, 0)
        return res

    description = repo_data.get("description", "")
    topics = repo_data.get("topics", [])
    default_branch = repo_data.get("default_branch", "main")
    license_info = repo_data.get("license")
    license_name = license_info.get("name") if isinstance(license_info, dict) else None

    # 2. Fetch languages breakdown
    lang_status, lang_data, _ = github_client.get(f"repos/{target_repo}/languages")
    primary_languages = lang_data if (lang_status == 200 and isinstance(lang_data, dict)) else {}

    # 3. Check top-level contents
    contents_status, contents_data, _ = github_client.get(f"repos/{target_repo}/contents")
    top_level_entries: List[str] = []
    has_contributing = False
    has_codeowners = False
    has_security = False

    if contents_status == 200 and isinstance(contents_data, list):
        for item in contents_data:
            name = item.get("name", "")
            top_level_entries.append(name)
            name_lower = name.lower()
            if "contributing" in name_lower:
                has_contributing = True
            if "codeowners" in name_lower:
                has_codeowners = True
            if "security" in name_lower:
                has_security = True

    # 4. Fetch README excerpt (max 4,000 characters)
    readme_status, readme_data, _ = github_client.get(f"repos/{target_repo}/readme")
    readme_excerpt = None
    if readme_status == 200 and isinstance(readme_data, dict):
        raw_content = readme_data.get("content", "")
        encoding = readme_data.get("encoding", "")
        if encoding == "base64" and raw_content:
            try:
                decoded_bytes = base64.b64decode(raw_content)
                text = decoded_bytes.decode("utf-8", errors="replace")
                readme_excerpt = text[:4000]
            except Exception:
                readme_excerpt = None

    # Apply redactions and privacy layer
    redacted_desc, r1 = redact_string(description or "")
    redacted_readme, r2 = redact_string(readme_excerpt or "")
    total_redactions = r1 + r2

    result = RepoOverviewResult(
        description=redacted_desc,
        topics=topics,
        primary_languages=primary_languages,
        license=license_name,
        default_branch=default_branch,
        top_level_entries=top_level_entries,
        has_contributing=has_contributing,
        has_codeowners=has_codeowners,
        has_security=has_security,
        readme_excerpt=redacted_readme if readme_excerpt else None,
        source_refs=source_refs,
    )
    audit_tool_call("get_repo_overview", {}, "success", result, total_redactions)
    return result


def get_directory_listing(path: str = "") -> DirectoryListingResult:
    """Fetch directory entries (names and metadata only) for a given repo path. Never reads file contents."""
    target_repo = config.target_repo
    clean_path = path.strip().replace("\\", "/").strip("/")

    # Enforce Path Denylist
    if is_path_denied(clean_path):
        res = DirectoryListingResult(
            path=clean_path,
            error=ToolError(
                code="path_blocked",
                message=f"Access to path '{clean_path}' is denied by repository security policy.",
                retryable=False,
            ),
            source_refs=[],
        )
        audit_tool_call("get_directory_listing", {"path": path}, "blocked", res, 0)
        return res

    endpoint = f"repos/{target_repo}/contents/{clean_path}" if clean_path else f"repos/{target_repo}/contents"
    source_url = f"https://github.com/{target_repo}/tree/main/{clean_path}" if clean_path else f"https://github.com/{target_repo}"
    source_refs = [
        SourceRef(
            id="S1",
            kind="live",
            label=f"GitHub Directory: {clean_path or 'root'}",
            url=source_url,
        )
    ]

    status, data, _ = github_client.get(endpoint)
    if status != 200:
        err_msg = data.get("error", {}).get("message") if isinstance(data, dict) else str(data)
        res = DirectoryListingResult(
            path=clean_path,
            error=ToolError(
                code="listing_failed",
                message=f"Failed to list directory '{clean_path}': {err_msg}",
                retryable=False,
            ),
            source_refs=source_refs,
        )
        audit_tool_call("get_directory_listing", {"path": path}, "error", res, 0)
        return res

    if not isinstance(data, list):
        # Path was a single file, not a directory
        res = DirectoryListingResult(
            path=clean_path,
            error=ToolError(
                code="not_a_directory",
                message=f"Path '{clean_path}' is a file, not a directory.",
                retryable=False,
            ),
            source_refs=source_refs,
        )
        audit_tool_call("get_directory_listing", {"path": path}, "error", res, 0)
        return res

    entries: List[DirectoryEntry] = []
    total_count = len(data)
    truncated = False

    # Enforce max 100 entries cap
    capped_data = data[:100]
    if total_count > 100:
        truncated = True

    for item in capped_data:
        name = item.get("name", "")
        item_type = item.get("type", "file")
        if item_type not in ("file", "dir", "symlink", "submodule"):
            item_type = "file"
        size = item.get("size") if item_type == "file" else None
        # Never include file contents or download URLs
        entries.append(DirectoryEntry(name=name, type=item_type, size=size))

    result = DirectoryListingResult(
        path=clean_path,
        entries=entries,
        truncated=truncated,
        total_count=total_count,
        source_refs=source_refs,
    )
    audit_tool_call("get_directory_listing", {"path": path}, "success", result, 0)
    return result

