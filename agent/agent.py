"""ReAct Agent implementation with event streaming and human-in-the-loop proposals.

Features:
- Event generator yielding typed progress events (ToolCall, ToolResult, ProposalRequested, FinalAnswer).
- Max 6 tool execution steps cap with graceful termination.
- Session tool result caching to prevent redundant API calls.
- Strict write protocol: forces dry_run=True on all write tools, generates Proposals, and pauses.
- History retention capped at the last 6 turns with truncated tool payloads.
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from typing import Any, Dict, Iterator, List, Optional

from config import config
from mcp_server.schemas import SourceRef, WritePreview
from agent.events import (
    AgentEvent,
    AgentErrorEvent,
    FinalAnswerEvent,
    Proposal,
    ProposalRequestedEvent,
    ToolCallEvent,
    ToolResultEvent,
)
from agent.llm_provider import LLMMessage, LLMProvider, LLMResponse, LLMUnavailable
from agent.mcp_bridge import MCPBridge, get_mcp_bridge
from agent.system_prompt import get_system_prompt
from logging_config import get_logger

logger = get_logger("onboarding_assistant.agent")

LIVE_TOOLS = {
    "get_repo_overview",
    "get_directory_listing",
    "list_good_first_issues",
    "find_code_owners",
    "get_recent_prs",
    "check_pr_preflight",
}
LOCAL_TOOLS = {
    "search_onboarding_docs",
    "get_onboarding_progress",
    "mark_task_done",
    "log_question",
    "diagnose_local_environment",
    "diagnose_build_error",
    "generate_smart_escalation",
    "get_cohort_progress",
}
WRITE_TOOLS = {"mark_task_done", "log_question"}


class Agent:
    """Semi-autonomous ReAct onboarding assistant agent."""

    def __init__(
        self,
        bridge: Optional[MCPBridge] = None,
        llm_provider: Optional[LLMProvider] = None,
        max_tool_steps: Optional[int] = None,
    ):
        self.bridge = bridge or get_mcp_bridge()
        self.llm = llm_provider or LLMProvider()
        self.max_tool_steps = max_tool_steps or config.max_tool_steps
        self.proposals: Dict[str, Proposal] = {}
        self._session_cache: Dict[str, Any] = {}

    def apply_proposal(self, proposal_id: str) -> Dict[str, Any]:
        """Apply a previously proposed write action with dry_run=False."""
        if proposal_id not in self.proposals:
            raise KeyError(f"Proposal '{proposal_id}' not found or already applied.")

        proposal = self.proposals[proposal_id]
        applied_args = {**proposal.args, "dry_run": False}
        logger.info(f"Applying proposal '{proposal_id}' (tool={proposal.tool_name}) with dry_run=False")
        result = self.bridge.call_tool(proposal.tool_name, applied_args)
        # Remove from active proposals
        del self.proposals[proposal_id]
        logger.info(f"Proposal '{proposal_id}' applied successfully.")
        return result

    def _truncate_history(self, history: List[Dict[str, str]], max_turns: int = 6) -> List[LLMMessage]:
        """Convert chat history dicts into LLMMessages, keeping the most recent turns."""
        recent = history[-max_turns:] if len(history) > max_turns else history
        messages: List[LLMMessage] = []
        for turn in recent:
            role = turn.get("role", "user")
            content = turn.get("content", "")
            if role in ("user", "assistant"):
                messages.append(LLMMessage(role=role, content=content))
        return messages

    def run(
        self,
        question: str,
        user_id: str,
        history: Optional[List[Dict[str, str]]] = None,
        user_role: Optional[str] = None,
    ) -> Iterator[AgentEvent]:
        """Execute the ReAct reasoning loop, yielding live events until a final answer is produced."""
        start_time = time.time()
        step_count = 0
        collected_sources: Dict[str, SourceRef] = {}
        last_provider_used = "Gemini"

        # Resolve role if omitted
        effective_role = user_role
        if not effective_role:
            try:
                from mcp_server.db import get_db_connection
                with get_db_connection() as conn:
                    r = conn.execute("SELECT role FROM users WHERE id = ?", (user_id,)).fetchone()
                    if r:
                        effective_role = r["role"]
            except Exception:
                effective_role = "Developer"

        logger.info(f"Agent received query for user '{user_id}' ({effective_role}): {question}")

        # 1. Prepare system prompt and tools
        system_instruction = get_system_prompt(user_role=effective_role)
        try:
            available_tools = self.bridge.list_tools()
        except Exception as exc:
            yield AgentErrorEvent(message=f"Failed to query available MCP tools: {exc}")
            return

        # 2. Build conversation messages
        messages: List[LLMMessage] = []
        if history:
            messages.extend(self._truncate_history(history, max_turns=6))
        messages.append(LLMMessage(role="user", content=question))

        # 3. ReAct loop
        while step_count < self.max_tool_steps:
            step_count += 1

            # Call LLM
            try:
                llm_resp: LLMResponse = self.llm.chat(
                    messages=messages,
                    tools=available_tools,
                    system=system_instruction,
                )
                last_provider_used = llm_resp.provider_used
            except LLMUnavailable as exc:
                yield AgentErrorEvent(message=str(exc))
                return
            except Exception as exc:
                yield AgentErrorEvent(message=f"Unexpected LLM failure: {type(exc).__name__}: {exc}")
                return

            # Case A: Model provided a final text answer without tool calls
            if not llm_resp.tool_calls:
                elapsed = round(time.time() - start_time, 2)
                logger.info(f"Final answer synthesized via {last_provider_used} in {elapsed}s across {step_count} step(s).")
                yield FinalAnswerEvent(
                    markdown=llm_resp.content or "No response generated.",
                    sources=list(collected_sources.values()),
                    provider_used=last_provider_used,
                    steps=step_count,
                    elapsed_s=elapsed,
                )
                return

            # Case B: Model requested one or more tool calls
            # Record assistant turn with tool calls
            messages.append(
                LLMMessage(
                    role="assistant",
                    content=llm_resp.content,
                    tool_calls=llm_resp.tool_calls,
                )
            )

            for tc in llm_resp.tool_calls:
                tool_name = tc["name"]
                tool_args = dict(tc.get("args", {}))
                tool_kind = "live" if tool_name in LIVE_TOOLS else "local"

                # Enforce parameters injection and dry_run safety
                if tool_name in ("get_onboarding_progress", "mark_task_done", "log_question", "generate_smart_escalation"):
                    tool_args["user_id"] = user_id

                # WRITE TOOL SAFETY: Force dry_run=True regardless of what model supplied
                if tool_name in WRITE_TOOLS:
                    tool_args["dry_run"] = True

                logger.info(f"Step {step_count}: dispatching tool '{tool_name}' ({tool_kind}) with args={tool_args}")

                # Yield ToolCallEvent
                yield ToolCallEvent(name=tool_name, args=tool_args, kind=tool_kind)

                # Execute tool or fetch from session cache
                cache_key = f"{tool_name}_{json.dumps(tool_args, sort_keys=True)}"
                call_start = time.time()

                if cache_key in self._session_cache:
                    tool_raw_result = self._session_cache[cache_key]
                else:
                    try:
                        tool_raw_result = self.bridge.call_tool(tool_name, tool_args)
                        self._session_cache[cache_key] = tool_raw_result
                    except Exception as exc:
                        tool_raw_result = {"error": {"code": "bridge_error", "message": str(exc)}}

                duration_ms = round((time.time() - call_start) * 1000, 1)

                # Collect source_refs
                if isinstance(tool_raw_result, dict):
                    raw_refs = tool_raw_result.get("source_refs", [])
                    for r in raw_refs:
                        if isinstance(r, dict):
                            ref_id = r.get("id", str(uuid.uuid4()))
                            collected_sources[ref_id] = SourceRef(**r)
                        elif isinstance(r, SourceRef):
                            collected_sources[r.id] = r

                # Summarize result for live trace
                is_ok = "error" not in tool_raw_result or not tool_raw_result["error"]
                if is_ok:
                    if tool_name == "search_onboarding_docs":
                        match_count = len(tool_raw_result.get("matches", []))
                        cov = tool_raw_result.get("coverage", "none")
                        summary = f"{match_count} matches (coverage: {cov})"
                    elif tool_name == "list_good_first_issues":
                        summary = f"{len(tool_raw_result.get('issues', []))} issues found"
                    elif tool_name == "find_code_owners":
                        summary = f"{tool_raw_result.get('method', '')}: {', '.join(tool_raw_result.get('owners', []))}"
                    elif tool_name == "get_directory_listing":
                        summary = f"{len(tool_raw_result.get('entries', []))} entries"
                    elif tool_name == "get_recent_prs":
                        summary = f"{len(tool_raw_result.get('prs', []))} pull requests"
                    elif tool_name == "diagnose_local_environment":
                        summary = f"env audit: {'all passed' if tool_raw_result.get('all_passed') else 'remedies found'}"
                    elif tool_name == "check_pr_preflight":
                        summary = f"preflight: {'ready for review' if tool_raw_result.get('ready_for_review') else 'warnings detected'}"
                    elif tool_name == "diagnose_build_error":
                        summary = f"diagnosed: {tool_raw_result.get('error_type', 'error')}"
                    elif tool_name == "generate_smart_escalation":
                        summary = f"escalation packet for {', '.join(tool_raw_result.get('owners', []))}"
                    elif tool_name == "get_cohort_progress":
                        summary = f"cohort: {tool_raw_result.get('average_completion_pct', 0)}% avg completion"
                    elif tool_name in WRITE_TOOLS:
                        summary = "proposal preview generated"
                    else:
                        summary = "ok"
                else:
                    err_info = tool_raw_result.get("error", {})
                    summary = f"error: {err_info.get('message', 'unknown')}"

                yield ToolResultEvent(
                    name=tool_name,
                    ok=is_ok,
                    summary=summary,
                    duration_ms=duration_ms,
                )
                logger.info(f"Tool '{tool_name}' finished in {duration_ms}ms (ok={is_ok}): {summary}")

                # Check if this was a write tool producing a Proposal
                if tool_name in WRITE_TOOLS and is_ok:
                    preview_data = tool_raw_result.get("preview")
                    if preview_data:
                        prop_id = f"prop_{uuid.uuid4().hex[:8]}"
                        preview_obj = (
                            preview_data
                            if isinstance(preview_data, WritePreview)
                            else WritePreview(**preview_data)
                        )
                        proposal = Proposal(
                            id=prop_id,
                            tool_name=tool_name,
                            args=tool_args,
                            preview=preview_obj,
                        )
                        self.proposals[prop_id] = proposal
                        yield ProposalRequestedEvent(proposal=proposal)

                # Feed tool result back to message history
                tool_result_str = (
                    json.dumps(tool_raw_result)
                    if isinstance(tool_raw_result, (dict, list))
                    else str(tool_raw_result)
                )
                # Truncate old tool outputs if very long to stay within token limits
                if len(tool_result_str) > 4000:
                    tool_result_str = tool_result_str[:4000] + "... [truncated]"

                messages.append(
                    LLMMessage(
                        role="tool",
                        content=tool_result_str,
                        tool_call_id=tc.get("id", f"call_{tool_name}"),
                        name=tool_name,
                    )
                )

        # 4. If step cap is reached
        elapsed = round(time.time() - start_time, 2)
        yield FinalAnswerEvent(
            markdown=(
                "I reached the maximum allowed tool execution steps before completing. "
                "Here is what I gathered from the repository and handbook so far."
            ),
            sources=list(collected_sources.values()),
            provider_used=last_provider_used,
            steps=step_count,
            elapsed_s=elapsed,
        )

