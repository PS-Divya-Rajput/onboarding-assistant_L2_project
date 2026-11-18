"""Pydantic schemas for MCP server tool inputs, outputs, and structured errors.

Every tool returns structured data, never free text blobs.
Errors follow a uniform structure and never crash the server or agent loop.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class SourceRef(BaseModel):
    """Citation metadata reference for verified grounding."""
    id: str = Field(description="Unique citation identifier, e.g. S1")
    kind: Literal["live", "local"] = Field(description="Origin category: live GitHub API or local handbook")
    label: str = Field(description="Human-readable citation label, e.g. 'CONTRIBUTING.md' or 'Issue #123'")
    url: Optional[str] = Field(default=None, description="Direct permalink or reference URL")


class ToolError(BaseModel):
    """Structured error payload returned on failure without raising unhandled exceptions."""
    code: str = Field(description="Machine-readable error code, e.g. 'rate_limited', 'path_blocked'")
    message: str = Field(description="Readable explanation of what failed and why")
    retryable: bool = Field(default=False, description="Whether the tool call might succeed if retried")


class BaseToolResult(BaseModel):
    """Base class for all tool responses."""
    error: Optional[ToolError] = None
    source_refs: List[SourceRef] = Field(default_factory=list)


# --- Live Tool Schemas ---

class RepoOverviewResult(BaseToolResult):
    description: Optional[str] = None
    topics: List[str] = Field(default_factory=list)
    primary_languages: Dict[str, int] = Field(default_factory=dict)
    license: Optional[str] = None
    default_branch: str = "main"
    top_level_entries: List[str] = Field(default_factory=list)
    has_contributing: bool = False
    has_codeowners: bool = False
    has_security: bool = False
    readme_excerpt: Optional[str] = None


class DirectoryEntry(BaseModel):
    name: str
    type: Literal["file", "dir", "symlink", "submodule"]
    size: Optional[int] = None


class DirectoryListingResult(BaseToolResult):
    path: str = ""
    entries: List[DirectoryEntry] = Field(default_factory=list)
    truncated: bool = False
    total_count: int = 0


class IssueItem(BaseModel):
    number: int
    title: str
    labels: List[str] = Field(default_factory=list)
    comment_count: int = 0
    created_at: str = ""
    url: str = ""


class GoodFirstIssuesResult(BaseToolResult):
    issues: List[IssueItem] = Field(default_factory=list)
    total_found: int = 0


class CodeOwnerResult(BaseToolResult):
    path: str
    owners: List[str] = Field(default_factory=list)
    method: Literal["codeowners", "inferred"]
    rule: Optional[str] = None
    note: Optional[str] = None


class PullRequestItem(BaseModel):
    number: int
    title: str
    author: str = ""
    labels: List[str] = Field(default_factory=list)
    state: str = "open"
    created_at: str = ""
    merged_at: Optional[str] = None
    url: str = ""


class RecentPRsResult(BaseToolResult):
    prs: List[PullRequestItem] = Field(default_factory=list)
    total_count: int = 0


# --- Local Tool Schemas ---

class DocMatch(BaseModel):
    text: str
    file: str
    heading_path: str
    origin: Literal["repo_docs", "authored"]
    url: Optional[str] = None
    similarity: float


class SearchDocsResult(BaseToolResult):
    query: str
    matches: List[DocMatch] = Field(default_factory=list)
    coverage: Literal["high", "low", "none"] = "none"


class TaskProgress(BaseModel):
    id: int
    ordinal: int
    title: str
    description: str
    handbook_ref: Optional[str] = None
    status: Literal["todo", "in_progress", "done"]


class OnboardingProgressResult(BaseToolResult):
    user_id: str
    tasks: List[TaskProgress] = Field(default_factory=list)
    done_count: int = 0
    total_count: int = 0
    next_suggested_task: Optional[TaskProgress] = None


class WritePreview(BaseModel):
    action: str
    user_id: str
    description: str
    changes: Dict[str, Any] = Field(default_factory=dict)


class MarkTaskDoneResult(BaseToolResult):
    success: bool = False
    dry_run: bool = True
    task_id: int
    preview: Optional[WritePreview] = None


class LogQuestionResult(BaseToolResult):
    success: bool = False
    dry_run: bool = True
    question: str
    preview: Optional[WritePreview] = None
    question_id: Optional[int] = None


# --- Enhanced Features Schemas (Doctor, Review, Diagnostic, Escalation) ---

class EnvironmentCheckItem(BaseModel):
    name: str
    status: Literal["pass", "warn", "fail"]
    found: Optional[str] = None
    required: str
    remedy: Optional[str] = None


class DiagnoseEnvironmentResult(BaseToolResult):
    all_passed: bool = True
    os_platform: str = ""
    checks: List[EnvironmentCheckItem] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)


class PRPreflightCheckItem(BaseModel):
    rule: str
    passed: bool
    detail: str
    recommendation: Optional[str] = None


class PRPreflightResult(BaseToolResult):
    pr_number: Optional[int] = None
    pr_title: Optional[str] = None
    ready_for_review: bool = False
    checks: List[PRPreflightCheckItem] = Field(default_factory=list)
    sensitive_paths_touched: List[str] = Field(default_factory=list)
    senior_review_checklist: List[str] = Field(default_factory=list)


class BuildErrorDiagnosticResult(BaseToolResult):
    error_type: str
    summary: str
    root_cause: str
    suggested_fixes: List[str] = Field(default_factory=list)
    relevant_docs: List[str] = Field(default_factory=list)
    who_to_ask: List[str] = Field(default_factory=list)


class SmartEscalationResult(BaseToolResult):
    developer_name: str
    developer_role: str
    topic: str
    owners: List[str] = Field(default_factory=list)
    escalation_packet_markdown: str
    slack_payload: Dict[str, Any] = Field(default_factory=dict)


class CohortMemberProgress(BaseModel):
    user_id: str
    display_name: str
    role: str
    done_count: int
    total_count: int = 12
    progress_pct: float
    current_milestone: Optional[str] = None
    stalled: bool = False


class CohortProgressResult(BaseToolResult):
    cohort: List[CohortMemberProgress] = Field(default_factory=list)
    average_completion_pct: float = 0.0
    stalled_count: int = 0
    top_bottlenecks: List[str] = Field(default_factory=list)


