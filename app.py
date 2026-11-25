"""Onboarding assistant — Streamlit application entrypoint.

Connects the editorial UI to the ReAct agent, MCP server, and SQLite persistence.
Enforces zero-emoji policy, human-in-the-loop write approval, and editorial design tokens.
"""

from __future__ import annotations

import json
from pathlib import Path
import importlib
import streamlit as st

from config import config
from agent.agent import Agent
from agent.mcp_bridge import MCPBridge, get_mcp_bridge
from mcp_server.db import get_db_connection, init_db

import ui.theme
import ui.components
import ui.views
importlib.reload(ui.theme)
importlib.reload(ui.components)
importlib.reload(ui.views)

from logging_config import setup_logging
setup_logging()

from ui.components import render_header_html, render_segmented_progress_html
from ui.theme import get_css
from ui.views import (
    render_ask_view,
    render_lead_oversight_view,
    render_path_view,
    render_question_log_view,
)

# 1. Page Configuration (Strictly no page icon / emoji)
st.set_page_config(
    page_title="Onboarding assistant",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

# 2. Inject Editorial CSS Theme
st.markdown(get_css(), unsafe_allow_html=True)


# 3. Cache MCP Bridge and Agent as application singletons
@st.cache_resource
def initialize_agent() -> Agent:
    """Initialize singleton Agent with long-lived background MCPBridge client."""
    init_db()
    bridge = get_mcp_bridge()
    return Agent(bridge=bridge)


agent = initialize_agent()


# 4. Load Handbook Summary
SUMMARY_PATH = Path(__file__).resolve().parent / "data" / "handbook" / "ingest_summary.json"
handbook_info_str = "13 documents, 277 sections, ingested 1 Nov 2026"
if SUMMARY_PATH.exists():
    try:
        with open(SUMMARY_PATH, "r", encoding="utf-8") as f:
            s_data = json.load(f)
            handbook_info_str = f"{s_data.get('documents', 13)} documents, {s_data.get('chunks', 277)} sections, ingested {s_data.get('ingest_date', '1 Nov 2026')}"
    except Exception:
        pass


# 5. Fetch sample users for Sidebar selector
with get_db_connection() as conn:
    user_rows = conn.execute("SELECT id, display_name, role FROM users ORDER BY id ASC").fetchall()
    users_map = {r["id"]: f"{r['display_name']} ({r['role']})" for r in user_rows}

if not users_map:
    users_map = {
        "user_ravi": "Ravi Patel (Junior Contributor)",
        "user_elena": "Elena Rostova (Backend Engineer)",
        "user_marcus": "Marcus Chen (Systems Programmer)",
    }

# Track last provider in session state
if "last_provider_used" not in st.session_state:
    st.session_state.last_provider_used = "Gemini"


# 6. Sidebar
with st.sidebar:
    import html

    # Workspace Identity
    st.markdown(
        f"""
        <div class="sidebar-workspace-header">
            <div class="sidebar-workspace-brand">
                <div class="sidebar-workspace-logo">R</div>
                <div>
                    <div class="sidebar-workspace-title">{html.escape(config.target_repo)}</div>
                    <div class="sidebar-workspace-sub">Onboarding Workspace</div>
                </div>
            </div>
            <span class="sidebar-branch-pill">main</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="sidebar-label">DEVELOPER PERSONA</div>', unsafe_allow_html=True)
    selected_user_id = st.selectbox(
        label="Select developer persona",
        options=list(users_map.keys()),
        format_func=lambda uid: users_map.get(uid, uid),
        label_visibility="collapsed",
    )

    # Active persona details
    active_user_info = next((r for r in user_rows if r["id"] == selected_user_id), None)
    if active_user_info:
        user_name = active_user_info["display_name"]
        user_role = active_user_info["role"]
        from ui.components import render_persona_card_html
        st.markdown(render_persona_card_html(user_name, user_role, stage="Onboarding Track"), unsafe_allow_html=True)

    # User Progress Segmented Bar
    st.markdown('<div class="sidebar-label">MILESTONE PROGRESS</div>', unsafe_allow_html=True)
    with get_db_connection() as conn:
        done_count_row = conn.execute(
            "SELECT COUNT(*) as cnt FROM user_progress WHERE user_id = ? AND status = 'done'",
            (selected_user_id,),
        ).fetchone()
        done_count = done_count_row["cnt"] if done_count_row else 0

        next_task_row = conn.execute(
            """
            SELECT t.id, t.ordinal, t.title
            FROM tasks t
            LEFT JOIN user_progress up ON t.id = up.task_id AND up.user_id = ?
            WHERE up.status IS NULL OR up.status != 'done'
            ORDER BY t.ordinal ASC
            LIMIT 1
            """,
            (selected_user_id,),
        ).fetchone()

    st.markdown(render_segmented_progress_html(done_count=done_count, total_count=12), unsafe_allow_html=True)

    if next_task_row:
        st.markdown(
            f"""
            <div class="sidebar-next-card">
                <div class="sidebar-next-card-header">
                    <span class="sidebar-next-tag">Next Milestone</span>
                    <span class="sidebar-next-step">Step {next_task_row['ordinal']:02d}</span>
                </div>
                <div class="sidebar-next-title">{html.escape(next_task_row['title'])}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Ask about next step", key="btn_ask_step"):
            st.session_state.prefill_query = f"How do I complete step {next_task_row['ordinal']}: '{next_task_row['title']}'?"
            st.session_state.active_tab = "Ask"
            st.rerun()

    # Handbook Provenance
    st.markdown('<div class="sidebar-label">KNOWLEDGE BASE</div>', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="sidebar-telemetry-card">
            <div class="sidebar-telemetry-header">
                <span class="sidebar-telemetry-title">Documentation Ingested</span>
                <span class="sidebar-telemetry-dot"></span>
            </div>
            <div class="sidebar-telemetry-body">{html.escape(handbook_info_str)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Privacy Guarantee
    st.markdown('<div class="sidebar-label">DATA GOVERNANCE</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="sidebar-telemetry-card">
            <div class="sidebar-telemetry-header">
                <span class="sidebar-telemetry-title">Zero Source Code Leakage</span>
                <span class="sidebar-telemetry-shield">AST ONLY</span>
            </div>
            <div class="sidebar-telemetry-body">Grounded on public repository docs &amp; AST only. Never inspects raw source code.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# 7. Main Header
st.markdown(
    render_header_html(
        target_repo=config.target_repo,
        last_provider=st.session_state.last_provider_used,
    ),
    unsafe_allow_html=True,
)


# 8. Top Navigation Tabs
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "Ask"

nav_options = ["Ask", "Path", "Lead oversight", "Question log"]
active_index = nav_options.index(st.session_state.active_tab) if st.session_state.active_tab in nav_options else 0

nav_selection = st.radio(
    label="Navigation",
    options=nav_options,
    index=active_index,
    label_visibility="collapsed",
    horizontal=True,
)
st.session_state.active_tab = nav_selection


# 9. View Dispatch
if nav_selection == "Ask":
    render_ask_view(agent=agent, current_user_id=selected_user_id)
elif nav_selection == "Path":
    render_path_view(agent=agent, current_user_id=selected_user_id)
elif nav_selection == "Lead oversight":
    render_lead_oversight_view(agent=agent, current_user_id=selected_user_id)
elif nav_selection == "Question log":
    render_question_log_view(current_user_id=selected_user_id)

