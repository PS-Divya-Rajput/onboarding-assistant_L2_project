"""Typed event and proposal definitions for the Onboarding assistant agent loop."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional
from mcp_server.schemas import SourceRef, WritePreview


@dataclass
class Proposal:
    """Represents a human-in-the-loop write proposal awaiting explicit UI approval."""
    id: str
    tool_name: str
    args: Dict[str, Any]
    preview: WritePreview


@dataclass
class ToolCallEvent:
    """Emitted when the agent decides to invoke an MCP tool."""
    name: str
    args: Dict[str, Any]
    kind: Literal["live", "local"]


@dataclass
class ToolResultEvent:
    """Emitted when an MCP tool execution finishes."""
    name: str
    ok: bool
    summary: str
    duration_ms: float


@dataclass
class ProposalRequestedEvent:
    """Emitted when a write action is proposed, requiring human confirmation before apply."""
    proposal: Proposal


@dataclass
class FinalAnswerEvent:
    """Emitted when the agent produces its final grounded markdown answer."""
    markdown: str
    sources: List[SourceRef]
    provider_used: str
    steps: int
    elapsed_s: float


@dataclass
class AgentErrorEvent:
    """Emitted when an unrecoverable agent error occurs."""
    message: str


# Event union type alias
AgentEvent = ToolCallEvent | ToolResultEvent | ProposalRequestedEvent | FinalAnswerEvent | AgentErrorEvent

