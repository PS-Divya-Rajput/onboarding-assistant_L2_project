"""View renderers for Onboarding assistant: Ask view, Path view, and Question log view.

Integrated from Google Stitch MCP 'Warm Editorial Dev' design system.
Optimized for high usability, clear information hierarchy, and responsive interaction.
"""

from __future__ import annotations

import html
import time
from typing import Any, Dict, List, Optional
import streamlit as st
from config import config
from agent.agent import Agent
from agent.events import (
    AgentErrorEvent,
    FinalAnswerEvent,
    ProposalRequestedEvent,
    ToolCallEvent,
    ToolResultEvent,
)
from mcp_server.db import get_db_connection
from mcp_server.schemas import TaskProgress
from ui.components import (
    render_cohort_table_html,
    render_doctor_report_html,
    render_preflight_card_html,
    render_proposal_card_html,
    render_sources_footer_html,
    render_step_row_html,
    render_trace_summary_html,
    render_user_query_html,
    render_welcome_hero_html,
)

SUGGESTED_PROMPTS = [
    {
        "category": "Setup & Toolchain",
        "title": "Local Environment Setup",
        "desc": "Cargo workspace, rustup targets, and pre-commit hooks for Ruff development.",
        "query": "How do I set the project up locally and build Ruff?",
    },
    {
        "category": "Diagnostics & Health",
        "title": "Environment Doctor",
        "desc": "Audit local Python, Rust toolchain, Git, and virtualenv prerequisites.",
        "query": "Run local environment doctor audit and check my setup",
    },
    {
        "category": "PR Review Readiness",
        "title": "PR Pre-Flight Audit",
        "desc": "Audit PR template completeness, test coverage, and security isolation.",
        "query": "Run a pre-flight review on PR #101 before senior review",
    },
    {
        "category": "Architecture & Ownership",
        "title": "Architecture & Ownership",
        "desc": "Linter vs Formatter crate split and AST visitor pipelines across crates.",
        "query": "Where is the parser code located and who should I ask for review?",
    },
    {
        "category": "First Contribution",
        "title": "Unassigned Beginner Issues",
        "desc": "Filter good-first-issue labels with core team mentors attached for review.",
        "query": "Give me something to work on without an open PR",
    },
    {
        "category": "Weekly Goals",
        "title": "Weekly Goals & First PR",
        "desc": "Review onboarding checklist and target first PR to ruff_linter.",
        "query": "What should I do this week based on my onboarding checklist?",
    },
]


def render_ask_view(agent: Agent, current_user_id: str) -> None:
    """Render the thread-based Ask view."""
    # Initialize thread history in session state
    if "threads" not in st.session_state:
        st.session_state.threads = []

    # Prefill question handler from sidebar, examples, or path view
    prompt_to_run = None
    if st.session_state.get("prefill_query"):
        prompt_to_run = st.session_state.pop("prefill_query")

    # Action bar (Clear Conversation when threads exist)
    if st.session_state.threads:
        top_col1, top_col2 = st.columns([5, 1])
        with top_col1:
            st.markdown(
                f'<div style="font-family:var(--font-mono); font-size:12px; color:var(--text-muted); padding-top:6px;">'
                f'Active Conversation Stream ({len(st.session_state.threads)} {"query" if len(st.session_state.threads) == 1 else "queries"})'
                f'</div>',
                unsafe_allow_html=True,
            )
        with top_col2:
            if st.button("Clear thread", key="btn_clear_thread"):
                st.session_state.threads = []
                st.rerun()

    # Render previous threads
    for t_idx, thread in enumerate(st.session_state.threads):
        # 1. User Question Card
        st.markdown(render_user_query_html(thread["question"]), unsafe_allow_html=True)

        # 2. Collapsed execution trace
        if thread.get("trace"):
            st.markdown(thread["trace"], unsafe_allow_html=True)

        # 3. Assistant Answer Card
        if thread.get("answer"):
            sources_block = thread.get("sources_html") or ""
            st.markdown(
                f"""
                <div class="answer-container">
                    <div class="answer-header">
                        <span class="answer-badge">Gemini Onboarding Agent · Grounded</span>
                        <span style="font-family:var(--font-mono); font-size:11px; color:var(--text-muted);">Verified Ruff Docs</span>
                    </div>
                    <div class="answer-body">
                """,
                unsafe_allow_html=True,
            )
            st.markdown(thread["answer"])
            if sources_block:
                st.markdown(sources_block, unsafe_allow_html=True)
            st.markdown("</div></div>", unsafe_allow_html=True)

        # 4. Render active proposal card if pending
        if thread.get("pending_proposal"):
            prop = thread["pending_proposal"]
            st.markdown(render_proposal_card_html(prop.preview), unsafe_allow_html=True)
            col1, col2, _ = st.columns([1.5, 1.2, 3])
            with col1:
                if st.button("Apply Change & Advance", key=f"apply_{prop.id}"):
                    try:
                        agent.apply_proposal(prop.id)
                        thread["pending_proposal"] = None
                        st.session_state[f"applied_{prop.id}"] = True
                        st.rerun()
                    except Exception as e:
                        st.markdown(f'<span style="color:var(--error-primary);">Error: {html.escape(str(e))}</span>', unsafe_allow_html=True)
            with col2:
                if st.button("Discard Proposal", key=f"discard_{prop.id}"):
                    if prop.id in agent.proposals:
                        del agent.proposals[prop.id]
                    thread["pending_proposal"] = None
                    st.rerun()

    # Empty State Welcome Dashboard
    if not st.session_state.threads:
        st.markdown(render_welcome_hero_html(config.target_repo), unsafe_allow_html=True)
        st.markdown(
            '<div class="section-label" style="margin-top:1.5rem; margin-bottom:0.75rem;">Explore Common Onboarding Workflows</div>',
            unsafe_allow_html=True,
        )

        col_a, col_b = st.columns(2)
        for idx, item in enumerate(SUGGESTED_PROMPTS):
            target_col = col_a if idx % 2 == 0 else col_b
            with target_col:
                st.markdown(
                    f"""
                    <div class="prompt-card">
                        <div class="prompt-card-category">{html.escape(item['category'])}</div>
                        <div class="prompt-card-title">{html.escape(item['title'])}</div>
                        <div class="prompt-card-desc">{html.escape(item['desc'])}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if st.button(f"Ask: {item['title']}", key=f"btn_prompt_{idx}"):
                    prompt_to_run = item["query"]

    # Chat Input
    user_input = st.chat_input("Ask a question about setup, code ownership, or what to work on next...")
    if user_input:
        prompt_to_run = user_input

    # Run agent if a prompt is submitted
    if prompt_to_run:
        _execute_query(agent, prompt_to_run, current_user_id)
        st.rerun()


def _execute_query(agent: Agent, question: str, user_id: str) -> None:
    """Execute query through agent, streaming live trace into UI."""
    trace_container = st.empty()
    trace_rows: List[Dict[str, Any]] = []
    handbook_count = 0
    live_count = 0
    final_answer = ""
    provider_used = "Gemini"
    elapsed_time = 0.0
    pending_proposal = None
    sources = []

    # Display running indicator
    trace_container.markdown(
        f'<div class="trace-row running"><span>Reading repository documentation and live state...</span><span></span></div>',
        unsafe_allow_html=True,
    )

    history = [
        {"role": "user" if i % 2 == 0 else "assistant", "content": t.get("question") if i % 2 == 0 else t.get("answer", "")}
        for i, t in enumerate(st.session_state.threads)
    ]

    for event in agent.run(question=question, user_id=user_id, history=history):
        if isinstance(event, ToolCallEvent):
            if event.kind == "live":
                live_count += 1
            else:
                handbook_count += 1

            trace_rows.append({
                "name": event.name,
                "kind": event.kind,
                "args": event.args,
                "summary": "running...",
                "duration_ms": 0.0,
            })
            # Update trace display
            trace_container.markdown(
                f'<div class="trace-row running"><span>STEP {len(trace_rows):02d}&nbsp;&nbsp;<code>{html.escape(event.name)}</code>&nbsp;&nbsp;<span style="color:var(--text-muted);">({event.kind})</span></span><span>running...</span></div>',
                unsafe_allow_html=True,
            )

        elif isinstance(event, ToolResultEvent):
            if trace_rows:
                trace_rows[-1]["summary"] = event.summary
                trace_rows[-1]["duration_ms"] = event.duration_ms

        elif isinstance(event, ProposalRequestedEvent):
            pending_proposal = event.proposal

        elif isinstance(event, FinalAnswerEvent):
            final_answer = event.markdown
            provider_used = event.provider_used
            elapsed_time = event.elapsed_s
            sources = event.sources
            st.session_state.last_provider_used = provider_used

        elif isinstance(event, AgentErrorEvent):
            final_answer = f"Error: {event.message}"

    # Build collapsed trace summary
    trace_html = render_trace_summary_html(
        steps=len(trace_rows),
        handbook_count=handbook_count,
        live_count=live_count,
        provider=provider_used,
        elapsed_s=elapsed_time,
        trace_rows=trace_rows,
    )

    sources_html = render_sources_footer_html(sources)

    # Store thread in session state
    st.session_state.threads.append({
        "question": question,
        "answer": final_answer,
        "trace": trace_html,
        "sources_html": sources_html,
        "pending_proposal": pending_proposal,
    })


def render_path_view(agent: Agent, current_user_id: str) -> None:
    """Render the 12 onboarding steps path grouped by milestone stage."""
    with get_db_connection() as conn:
        query = """
            SELECT t.id, t.ordinal, t.title, t.description, t.handbook_ref,
                   COALESCE(up.status, 'todo') AS status
            FROM tasks t
            LEFT JOIN user_progress up ON t.id = up.task_id AND up.user_id = ?
            ORDER BY t.ordinal ASC
        """
        rows = conn.execute(query, (current_user_id,)).fetchall()

    total_tasks = len(rows)
    done_tasks = sum(1 for r in rows if r["status"] == "done")
    pending_tasks = total_tasks - done_tasks

    # Filter Bar & Summary
    f_col1, f_col2 = st.columns([3, 2])
    with f_col1:
        st.markdown(
            f'<div class="filter-summary">'
            f'<span><strong>{done_tasks}</strong> completed · <strong>{pending_tasks}</strong> remaining</span>'
            f'<span style="color:var(--accent-primary); font-weight:600;">{int((done_tasks / max(total_tasks, 1)) * 100)}% progress</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with f_col2:
        status_filter = st.selectbox(
            "Filter tasks",
            ["All milestones (12)", "Pending only", "Completed only"],
            label_visibility="collapsed",
            key="path_status_filter",
        )

    # Define stage buckets matching Stitch layout
    stages = [
        {"name": "Phase 1: Day 1 — Toolchain & Local Setup", "range": (1, 4), "desc": "Prerequisites, build validation, tests, and linters"},
        {"name": "Phase 2: Week 1 — Architecture & First Contribution", "range": (5, 8), "desc": "Crate structure, code ownership, issue triage, and initial PR"},
        {"name": "Phase 3: Month 1 — Deep Dives & Governance", "range": (9, 12), "desc": "Performance benchmarks, parser snapshots, schema generation, and releases"},
    ]

    first_incomplete_found = False

    for stage in stages:
        stage_rows = [r for r in rows if stage["range"][0] <= r["ordinal"] <= stage["range"][1]]
        
        # Apply filter
        if status_filter == "Pending only":
            stage_rows = [r for r in stage_rows if r["status"] != "done"]
        elif status_filter == "Completed only":
            stage_rows = [r for r in stage_rows if r["status"] == "done"]

        if not stage_rows:
            continue

        st.markdown(
            f"""
            <div class="phase-header">
                <span class="phase-title">{stage['name']}</span>
                <span class="phase-meta">{stage['desc']}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        for r in stage_rows:
            status = r["status"]
            is_next = False
            if not first_incomplete_found and status in ("todo", "in_progress"):
                is_next = True
                first_incomplete_found = True

            task = TaskProgress(
                id=r["id"],
                ordinal=r["ordinal"],
                title=r["title"],
                description=r["description"],
                handbook_ref=r["handbook_ref"],
                status=status,
            )

            col1, col2, col3 = st.columns([5, 1.3, 1.3])
            with col1:
                st.markdown(render_step_row_html(task, is_next=is_next), unsafe_allow_html=True)
            with col2:
                if st.button("Ask help", key=f"ask_help_{task.id}"):
                    st.session_state.prefill_query = f"How do I complete step {task.ordinal}: '{task.title}'?"
                    st.session_state.active_tab = "Ask"
                    st.rerun()
            with col3:
                if status != "done":
                    if st.button("Mark done", key=f"mark_btn_{task.id}"):
                        res = agent.bridge.call_tool("mark_task_done", {"user_id": current_user_id, "task_id": task.id, "dry_run": True})
                        if res.get("preview"):
                            st.session_state.path_proposal = res["preview"]
                            st.session_state.path_task_id = task.id
                            st.rerun()

    # Active path proposal card
    if st.session_state.get("path_proposal"):
        prev = st.session_state.path_proposal
        st.markdown(
            f"""
            <div class="proposal-card">
                <div class="proposal-title">Action Required · Human-in-the-Loop Proposal</div>
                <div class="proposal-body"><strong>Proposed state update:</strong> {html.escape(prev.get('description', ''))}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        col_a, col_b, _ = st.columns([1.5, 1.2, 3])
        with col_a:
            if st.button("Apply Change", key="apply_path_btn"):
                task_id = st.session_state.pop("path_task_id")
                st.session_state.pop("path_proposal")
                agent.bridge.call_tool("mark_task_done", {"user_id": current_user_id, "task_id": task_id, "dry_run": False})
                st.rerun()
        with col_b:
            if st.button("Discard", key="discard_path_btn"):
                st.session_state.pop("path_task_id", None)
                st.session_state.pop("path_proposal", None)
                st.rerun()


def render_question_log_view(current_user_id: str) -> None:
    """Render question log and documentation gaps view with search and filters."""
    with get_db_connection() as conn:
        rows = conn.execute(
            """
            SELECT ql.id, ql.user_id, u.display_name, ql.question, ql.answered_from, ql.resolved, ql.created_at
            FROM question_log ql
            LEFT JOIN users u ON ql.user_id = u.id
            ORDER BY ql.id DESC
            """
        ).fetchall()

    handbook_answered = sum(1 for r in rows if r["answered_from"] == "handbook")
    live_answered = sum(1 for r in rows if r["answered_from"] == "live")
    unresolved_count = sum(1 for r in rows if r["resolved"] == 0)

    # Search & Filter controls
    log_col1, log_col2 = st.columns([3, 2])
    with log_col1:
        st.markdown(
            f'<div class="filter-summary">'
            f'<span>Handbook: <strong>{handbook_answered}</strong> · Live repo: <strong>{live_answered}</strong></span>'
            f'<span style="color:var(--proposal-primary); font-weight:600;">Gaps / Unanswered: {unresolved_count}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with log_col2:
        log_filter = st.selectbox(
            "Filter questions",
            ["All entries", "Gaps only (unanswered)", "Handbook answers", "Live GitHub answers"],
            label_visibility="collapsed",
            key="log_filter_select",
        )

    # Filter records
    filtered_rows = rows
    if log_filter == "Gaps only (unanswered)":
        filtered_rows = [r for r in rows if r["resolved"] == 0]
    elif log_filter == "Handbook answers":
        filtered_rows = [r for r in rows if r["answered_from"] == "handbook"]
    elif log_filter == "Live GitHub answers":
        filtered_rows = [r for r in rows if r["answered_from"] == "live"]

    # Gaps in the handbook section
    unresolved = [r for r in filtered_rows if r["resolved"] == 0]
    if unresolved:
        st.markdown(
            '<div class="section-label" style="color:var(--proposal-primary); margin-top:1rem; margin-bottom:0.75rem;">'
            'Gaps in the handbook'
            '</div>',
            unsafe_allow_html=True,
        )
        for r in unresolved:
            st.markdown(
                f"""
                <div style="background:var(--bg-surface); border:1px solid var(--border-hairline); border-left:3px solid var(--proposal-primary); border-radius:var(--radius-lg); padding:12px 16px; margin-bottom:8px; box-shadow:var(--shadow-subtle);">
                    <div style="font-weight:600; font-size:14px; color:var(--text-ink);">{html.escape(r['question'])}</div>
                    <div style="font-size:12px; color:var(--text-muted); margin-top:4px;">Asked by {html.escape(r['display_name'] or r['user_id'])} · source: none (flagged for documentation update)</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # Resolved questions
    resolved_rows = [r for r in filtered_rows if r["resolved"] == 1]
    if resolved_rows:
        st.markdown(
            '<div class="section-label" style="margin-top:1.5rem; margin-bottom:0.75rem;">'
            'Resolved questions'
            '</div>',
            unsafe_allow_html=True,
        )
        for r in resolved_rows:
            source_badge = "Handbook RAG" if r["answered_from"] == "handbook" else "Live GitHub API"
            st.markdown(
                f"""
                <div style="background:var(--bg-surface); border:1px solid var(--border-hairline); border-radius:var(--radius-lg); padding:12px 16px; margin-bottom:8px; box-shadow:var(--shadow-subtle);">
                    <div style="font-weight:600; font-size:14px; color:var(--text-ink);">{html.escape(r['question'])}</div>
                    <div style="font-size:12px; color:var(--text-muted); margin-top:4px;">
                        Asked by {html.escape(r['display_name'] or r['user_id'])} · answered via <span style="font-family:var(--font-mono); color:var(--accent-primary); font-weight:600;">{source_badge}</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown(
        '<div style="font-size:12px; color:var(--text-muted); margin-top:1.5rem;">'
        'Note: Includes sample entries to reflect team onboarding activity and persistent audit records.'
        '</div>',
        unsafe_allow_html=True,
    )


def render_lead_oversight_view(agent: Agent, current_user_id: str) -> None:
    """Render the Team Lead & Review Oversight dashboard."""
    from mcp_server.tools.local_escalation_tools import generate_smart_escalation, get_cohort_progress
    from mcp_server.tools.live_review_tools import check_pr_preflight
    from mcp_server.tools.local_doctor_tools import diagnose_local_environment

    st.markdown(
        """
        <div style="margin-bottom:1.25rem;">
            <div style="font-family:var(--font-serif); font-size:24px; font-weight:600; color:var(--text-ink); margin-bottom:4px;">Lead &amp; Senior Review Oversight</div>
            <div style="font-size:14px; color:var(--text-secondary);">Audit developer readiness, evaluate PR pre-flight compliance, and monitor cohort velocity.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 1. Cohort Velocity Section
    st.markdown('<div class="section-label">COHORT PROGRESS &amp; BOTTLENECKS</div>', unsafe_allow_html=True)
    cohort_data = get_cohort_progress()
    st.markdown(render_cohort_table_html(cohort_data), unsafe_allow_html=True)

    # 2. Two-column tools section: PR Preflight & Environment Doctor
    col_pr, col_doc = st.columns([1, 1], gap="medium")

    with col_pr:
        st.markdown('<div class="section-label">AUTOMATED PR PRE-FLIGHT AUDIT</div>', unsafe_allow_html=True)
        st.markdown(
            '<div style="font-size:13px; color:var(--text-muted); margin-bottom:8px;">'
            'Verify PR template completeness, test coverage, and security isolation before requesting senior maintainer time.'
            '</div>',
            unsafe_allow_html=True,
        )
        pr_num_input = st.number_input("GitHub PR Number (optional)", min_value=1, max_value=99999, value=101, step=1)
        pr_title_input = st.text_input("PR Title / Intent", value="Add AST visitor for match expressions")

        if st.button("Run PR Pre-Flight Audit", key="btn_run_preflight"):
            with st.spinner("Auditing PR changeset against repository security policy..."):
                preflight_res = check_pr_preflight(pr_number=int(pr_num_input), title=pr_title_input)
                st.session_state.last_preflight = preflight_res

        if st.session_state.get("last_preflight"):
            st.markdown(render_preflight_card_html(st.session_state.last_preflight), unsafe_allow_html=True)

    with col_doc:
        st.markdown('<div class="section-label">LOCAL ENVIRONMENT DOCTOR</div>', unsafe_allow_html=True)
        st.markdown(
            '<div style="font-size:13px; color:var(--text-muted); margin-bottom:8px;">'
            'Audit local developer machine toolchain (Python, Rust, Git, virtualenv) against project standards.'
            '</div>',
            unsafe_allow_html=True,
        )
        if st.button("Run Environment Audit", key="btn_run_doctor"):
            with st.spinner("Checking local compilers, PATH dependencies, and active environment..."):
                doc_res = diagnose_local_environment()
                st.session_state.last_doctor = doc_res

        if st.session_state.get("last_doctor"):
            st.markdown(render_doctor_report_html(st.session_state.last_doctor), unsafe_allow_html=True)

    # 3. Smart Escalations Section
    st.markdown('<div class="section-label" style="margin-top:1.5rem;">SMART SENIOR ESCALATION GENERATOR</div>', unsafe_allow_html=True)
    st.markdown(
        '<div style="font-size:13px; color:var(--text-muted); margin-bottom:8px;">'
        'Generate structured, zero-effort escalation summaries with code owners attached for Slack or 1-on-1s.'
        '</div>',
        unsafe_allow_html=True,
    )

    esc_q = st.text_input("Escalation Question or Blocker", value="Missing native dependency libclang during cargo build")
    esc_path = st.text_input("Repository Path Context", value="crates/ruff_python_parser")

    if st.button("Generate Senior Help Packet", key="btn_gen_escalation"):
        esc_res = generate_smart_escalation(
            user_id=current_user_id,
            question=esc_q,
            steps_attempted=["Checked setup guide in docs/contributing.md", "Attempted cargo build -p ruff_python_parser"],
            path_context=esc_path,
        )
        st.markdown(
            f"""
            <div style="background:var(--bg-surface); border:1px solid var(--border-hairline); border-radius:var(--radius-lg); padding:16px; margin-top:10px; box-shadow:var(--shadow-subtle);">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                    <span style="font-family:var(--font-serif); font-size:16px; font-weight:600; color:var(--text-ink);">Ready-to-Send Senior Escalation Packet</span>
                    <span style="font-family:var(--font-mono); font-size:11px; padding:2px 8px; border-radius:var(--radius-sm); background:var(--accent-tint); color:var(--accent-primary); font-weight:600;">Slack &amp; Teams Compatible</span>
                </div>
                <div style="font-family:var(--font-mono); font-size:12px; white-space:pre-wrap; background:var(--bg-card); padding:12px; border-radius:var(--radius-md); border:1px solid var(--border-hairline); color:var(--text-ink);">{html.escape(esc_res.escalation_packet_markdown)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_system_logs_view() -> None:
    """Render the centralized System Logs & Security Audit Trail view."""
    from logging_config import LOG_FILE_PATH, get_audit_records, read_recent_logs

    st.markdown(
        """
        <div style="margin-bottom:1.25rem;">
            <div style="font-family:var(--font-serif); font-size:24px; font-weight:600; color:var(--text-ink); margin-bottom:4px;">System Logs &amp; Audit Trail</div>
            <div style="font-size:14px; color:var(--text-secondary);">Real-time runtime logs, ReAct execution traces, LLM failover events, and cryptographic tool audit records.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_app_logs, tab_audit_logs = st.tabs(["Application Activity Logs", "MCP Security Audit Trail"])

    with tab_app_logs:
        col_ctrl1, col_ctrl2, col_ctrl3, col_ctrl4 = st.columns([2, 2, 1, 1], gap="small")
        with col_ctrl1:
            level_sel = st.selectbox("Log Level Filter", ["ALL", "INFO", "WARNING", "ERROR"], index=0)
        with col_ctrl2:
            lines_sel = st.selectbox("Lines to Display", [50, 100, 200, 500], index=1)
        with col_ctrl3:
            st.markdown('<div style="height:28px;"></div>', unsafe_allow_html=True)
            if st.button("Refresh", key="btn_refresh_logs"):
                st.rerun()
        with col_ctrl4:
            st.markdown('<div style="height:28px;"></div>', unsafe_allow_html=True)
            raw_text = ""
            if LOG_FILE_PATH.exists():
                try:
                    with open(LOG_FILE_PATH, "r", encoding="utf-8", errors="replace") as f:
                        raw_text = f.read()
                except Exception:
                    raw_text = "Failed to read log file."
            st.download_button(
                label="Download",
                data=raw_text,
                file_name="onboarding.log",
                mime="text/plain",
                key="btn_download_logs",
            )

        log_lines = read_recent_logs(max_lines=lines_sel, level_filter=level_sel)
        if log_lines:
            # Colorize lines
            formatted_lines = []
            for line in log_lines:
                escaped = html.escape(line)
                if "[ERROR]" in line:
                    formatted_lines.append(f'<span style="color:var(--proposal-primary); font-weight:600;">{escaped}</span>')
                elif "[WARNING]" in line:
                    formatted_lines.append(f'<span style="color:#d97706; font-weight:600;">{escaped}</span>')
                elif "[INFO]" in line:
                    formatted_lines.append(f'<span style="color:var(--text-ink);">{escaped}</span>')
                else:
                    formatted_lines.append(f'<span style="color:var(--text-muted);">{escaped}</span>')

            content_html = "<br/>".join(formatted_lines)
            st.markdown(
                f"""
                <div style="background:var(--bg-card); border:1px solid var(--border-hairline); border-radius:var(--radius-lg); padding:16px; font-family:var(--font-mono); font-size:12px; line-height:1.6; max-height:550px; overflow-y:auto; box-shadow:var(--shadow-subtle);">
                    {content_html}
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                """
                <div style="background:var(--bg-surface); border:1px solid var(--border-hairline); border-radius:var(--radius-lg); padding:24px; text-align:center; color:var(--text-muted); font-size:13px;">
                    No log records match the selected filter. Perform an action in the Ask or Lead view to generate runtime logs.
                </div>
                """,
                unsafe_allow_html=True,
            )

    with tab_audit_logs:
        st.markdown(
            '<div style="font-size:13px; color:var(--text-muted); margin-bottom:12px;">'
            'Immutable ledger recording every MCP tool execution. Adheres to zero-payload security policy: '
            'stores deterministic SHA-256 hash of arguments without persisting sensitive user data or API keys.'
            '</div>',
            unsafe_allow_html=True,
        )

        audit_records = get_audit_records(limit=100)
        if audit_records:
            # Summary chips
            total_calls = len(audit_records)
            total_redactions = sum(r["redactions"] for r in audit_records)
            errors_count = sum(1 for r in audit_records if r["status"] in ("error", "blocked"))

            st.markdown(
                f"""
                <div style="display:flex; gap:16px; margin-bottom:14px;">
                    <div style="background:var(--bg-surface); border:1px solid var(--border-hairline); border-radius:var(--radius-md); padding:8px 14px;">
                        <span style="font-family:var(--font-mono); font-size:11px; color:var(--text-muted); text-transform:uppercase;">Audited Calls</span>
                        <div style="font-family:var(--font-mono); font-size:16px; font-weight:600; color:var(--text-ink);">{total_calls}</div>
                    </div>
                    <div style="background:var(--bg-surface); border:1px solid var(--border-hairline); border-radius:var(--radius-md); padding:8px 14px;">
                        <span style="font-family:var(--font-mono); font-size:11px; color:var(--text-muted); text-transform:uppercase;">Tokens Redacted</span>
                        <div style="font-family:var(--font-mono); font-size:16px; font-weight:600; color:var(--accent-primary);">{total_redactions}</div>
                    </div>
                    <div style="background:var(--bg-surface); border:1px solid var(--border-hairline); border-radius:var(--radius-md); padding:8px 14px;">
                        <span style="font-family:var(--font-mono); font-size:11px; color:var(--text-muted); text-transform:uppercase;">Blocked / Errors</span>
                        <div style="font-family:var(--font-mono); font-size:16px; font-weight:600; color:{'var(--proposal-primary)' if errors_count else 'var(--text-muted)'};">{errors_count}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            rows_html = []
            for r in audit_records:
                status_color = "var(--accent-primary)" if r["status"] == "success" else ("var(--proposal-primary)" if r["status"] in ("error", "blocked") else "var(--text-muted)")
                short_sha = r["args_sha256"][:12] + "..."
                rows_html.append(
                    f"""
                    <tr style="border-bottom:1px solid var(--border-hairline); font-size:12px;">
                        <td style="padding:8px 10px; font-family:var(--font-mono); color:var(--text-muted);">{html.escape(r['ts'][:19].replace('T', ' '))}</td>
                        <td style="padding:8px 10px; font-family:var(--font-mono); font-weight:600; color:var(--text-ink);">{html.escape(r['tool'])}</td>
                        <td style="padding:8px 10px; font-family:var(--font-mono); font-size:11px; font-weight:600; color:{status_color}; text-transform:uppercase;">{html.escape(r['status'])}</td>
                        <td style="padding:8px 10px; font-family:var(--font-mono);">{r['bytes_returned']:,} B</td>
                        <td style="padding:8px 10px; font-family:var(--font-mono); color:{'var(--accent-primary)' if r['redactions'] else 'var(--text-muted)'};">{r['redactions']}</td>
                        <td style="padding:8px 10px; font-family:var(--font-mono); color:var(--text-muted); font-size:11px;" title="{html.escape(r['args_sha256'])}">{short_sha}</td>
                    </tr>
                    """
                )

            st.markdown(
                f"""
                <div style="background:var(--bg-surface); border:1px solid var(--border-hairline); border-radius:var(--radius-lg); padding:16px; box-shadow:var(--shadow-subtle);">
                    <table style="width:100%; border-collapse:collapse; text-align:left;">
                        <thead>
                            <tr style="border-bottom:2px solid var(--border-hairline); font-size:11px; font-family:var(--font-mono); color:var(--text-muted); text-transform:uppercase;">
                                <th style="padding:6px 10px;">Timestamp (UTC)</th>
                                <th style="padding:6px 10px;">Tool Name</th>
                                <th style="padding:6px 10px;">Status</th>
                                <th style="padding:6px 10px;">Bytes</th>
                                <th style="padding:6px 10px;">Redactions</th>
                                <th style="padding:6px 10px;">Arguments SHA-256</th>
                            </tr>
                        </thead>
                        <tbody>
                            {''.join(rows_html)}
                        </tbody>
                    </table>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                """
                <div style="background:var(--bg-surface); border:1px solid var(--border-hairline); border-radius:var(--radius-lg); padding:24px; text-align:center; color:var(--text-muted); font-size:13px;">
                    Zero audit records logged yet. Tools invoked by the agent will appear here automatically.
                </div>
                """,
                unsafe_allow_html=True,
            )
