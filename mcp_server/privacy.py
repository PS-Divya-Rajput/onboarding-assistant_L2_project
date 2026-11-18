"""Privacy and Data Governance Layer for Onboarding assistant.

Enforces:
1. Strict restriction on source code inspection (only approved documentation files).
2. Path denylist enforcement (blocking access to secrets, workflows, private keys).
3. Comprehensive redaction of sensitive credentials and tokens in tool outputs.
4. Target repository allowlist boundary enforcement.
5. Zero-payload audit logging (SHA-256 hash of arguments only).
6. Sanitization and truncation of untrusted user/repo content (issue & PR titles, READMEs).
"""

from __future__ import annotations

import fnmatch
import hashlib
import json
import re
from pathlib import PurePosixPath
from typing import Any, Dict, List, Tuple
from config import config
from mcp_server.db import record_audit

# Explicit allowlist for documentation files that may be fetched
DOC_FILENAME_PATTERNS = [
    "readme*",
    "contributing*",
    "codeowners",
    "maintainers*",
    "security*",
    "code_of_conduct*",
    "pull_request_template*",
]

# Sensitive patterns for output redaction
REDACTION_PATTERNS: List[re.Pattern] = [
    # GitHub personal access tokens, OAuth tokens, and app tokens
    re.compile(r"\b(ghp|github_pat|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{20,}\b"),
    # AWS access key ID
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    # PEM Private Key Blocks
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----"),
    # HTTP Authorization Bearer tokens
    re.compile(r"(?i)\bbearer\s+[A-Za-z0-9_\-\.]{16,}\b"),
    # Generic API key / secret key assignments
    re.compile(r"(?i)\b(api[_-]?key|secret|token|password|auth_token)\s*[:=]\s*['\"]?([A-Za-z0-9_\-\.]{8,})['\"]?"),
]


def is_path_denied(path: str, denylist: List[str] | None = None) -> bool:
    """Check if a given path matches any entry in the denylist."""
    if not path:
        return False
    active_denylist = denylist if denylist is not None else config.path_denylist
    clean_path = path.strip().replace("\\", "/").strip("/").lower()
    path_parts = clean_path.split("/")

    for blocked in active_denylist:
        blocked_clean = blocked.strip().replace("\\", "/").strip("/").lower()
        if not blocked_clean:
            continue
        # Exact match, prefix match, or path segment match
        if clean_path == blocked_clean or clean_path.startswith(blocked_clean + "/"):
            return True
        if any(part == blocked_clean for part in path_parts):
            return True
        # Wildcard / glob match
        if fnmatch.fnmatch(clean_path, f"*{blocked_clean}*"):
            return True
    return False


def is_allowed_doc_path(path: str) -> bool:
    """Verify that a path points to an allowed documentation file, never source code."""
    if not path or is_path_denied(path):
        return False
    normalized = path.strip().replace("\\", "/").strip("/").lower()
    posix_path = PurePosixPath(normalized)
    filename = posix_path.name

    # Allow explicit root/meta documentation filenames
    for pattern in DOC_FILENAME_PATTERNS:
        if fnmatch.fnmatch(filename, pattern):
            return True

    # Allow markdown files under docs/ or documentation directories
    if "docs" in posix_path.parts and filename.endswith((".md", ".rst", ".txt")):
        return True

    return False


def redact_string(text: str) -> Tuple[str, int]:
    """Redact sensitive credentials from text string and return redacted text and count."""
    if not text:
        return text, 0
    redaction_count = 0
    redacted = text

    for pattern in REDACTION_PATTERNS:
        matches = list(pattern.finditer(redacted))
        if matches:
            redaction_count += len(matches)
            # Replace matches with [REDACTED]
            redacted = pattern.sub("[REDACTED]", redacted)

    return redacted, redaction_count


def redact_data(data: Any) -> Tuple[Any, int]:
    """Recursively redact strings in dictionaries, lists, and primitives."""
    if isinstance(data, str):
        return redact_string(data)
    elif isinstance(data, dict):
        total_redactions = 0
        cleaned_dict = {}
        for k, v in data.items():
            cleaned_v, count = redact_data(v)
            cleaned_dict[k] = cleaned_v
            total_redactions += count
        return cleaned_dict, total_redactions
    elif isinstance(data, list):
        total_redactions = 0
        cleaned_list = []
        for item in data:
            cleaned_item, count = redact_data(item)
            cleaned_list.append(cleaned_item)
            total_redactions += count
        return cleaned_list, total_redactions
    else:
        return data, 0


def sanitize_untrusted_text(text: str, max_chars: int = 120) -> str:
    """Truncate untrusted text (issue titles, PR titles) to mitigate prompt injection."""
    if not text:
        return ""
    # Strip carriage returns and single-line normalize
    normalized = " ".join(text.split())
    if len(normalized) > max_chars:
        return normalized[: max_chars - 3] + "..."
    return normalized


def hash_arguments(args: Dict[str, Any]) -> str:
    """Compute deterministic SHA-256 hash of tool call arguments without logging values."""
    try:
        serialized = json.dumps(args, sort_keys=True, default=str)
    except Exception:
        serialized = str(args)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def audit_tool_call(
    tool_name: str,
    args: Dict[str, Any],
    status: str,
    payload_obj: Any,
    redaction_count: int = 0,
) -> None:
    """Record an audit log entry for a completed tool call."""
    args_sha = hash_arguments(args)
    try:
        if isinstance(payload_obj, str):
            payload_bytes = len(payload_obj.encode("utf-8"))
        elif hasattr(payload_obj, "model_dump_json"):
            payload_bytes = len(payload_obj.model_dump_json().encode("utf-8"))
        else:
            payload_bytes = len(json.dumps(payload_obj, default=str).encode("utf-8"))
    except Exception:
        payload_bytes = 0

    record_audit(
        tool=tool_name,
        args_sha256=args_sha,
        status=status,
        bytes_returned=payload_bytes,
        redactions=redaction_count,
    )

