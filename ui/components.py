"""HTML and component renderers for Onboarding assistant Streamlit UI.

Directly reflects the Google Stitch MCP 'Warm Editorial Dev' design system.
Enforces zero-emoji policy, strict HTML escaping, and editorial design tokens.
"""

from __future__ import annotations

import html
from typing import Any, Dict, List, Optional
from mcp_server.schemas import SourceRef, TaskProgress, WritePreview


def render_header_html(target_repo: str, last_provider: str = "Gemini") -> str:
    """Render top application header with wordmark, repo chip, and provider indicator."""
    is_fallback = "Groq" in last_provider
    status_text = "Groq · Fallback active" if is_fallback else "Gemini · Ready"
    dot_class = "status-dot fallback" if is_fallback else "status-dot"

    return f"""
    <div class="header-container">
        <div style="display:flex; align-items:center;">
            <span class="wordmark">Onboarding assistant</span>
            <span class="repo-chip">{html.escape(target_repo)} / main</span>
        </div>
        <div class="model-status-line">
            <span class="{dot_class}"></span>{html.escape(status_text)}
        </div>
    </div>
    """


def render_welcome_hero_html(target_repo: str) -> str:
    """Render a welcoming hero banner with guidance on assistant capabilities."""
    return f"""
    <div class="welcome-hero">
        <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:16px;">
            <div>
                <span class="hero-tag">Grounded Onboarding Copilot</span>
                <div class="hero-title">Astral Ruff Onboarding Copilot: Verified Guidance</div>
                <div class="hero-sub">
                    Ask questions about codebase architecture, linter rules, compiler diagnostics, and crate boundaries with zero hallucination. Every response is cited from official repository documentation and live repository state.
                </div>
            </div>
            <div style="background:var(--bg-surface-low); border:1px solid var(--border-hairline); border-radius:var(--radius); padding:8px 14px; text-align:center; min-width:105px;">
                <div style="font-family:var(--font-serif); font-size:20px; font-weight:600; color:var(--accent-primary);">1.84+</div>
                <div style="font-family:var(--font-mono); font-size:10px; color:var(--text-muted); text-transform:uppercase; letter-spacing:0.05em;">Rust MSRV</div>
            </div>
        </div>
    </div>
    """


def render_persona_card_html(name: str, role: str, stage: str = "Onboarding Track") -> str:
    """Render the active persona profile card in the sidebar."""
    # Extract 2-letter initials
    initials = "".join([part[0] for part in name.split()[:2]]).upper() if name else "DEV"

    return f"""
    <div class="persona-card">
        <div class="persona-header-row">
            <div class="persona-avatar">{html.escape(initials)}</div>
            <div style="overflow:hidden;">
                <div class="persona-name">{html.escape(name)}</div>
                <div class="persona-role">{html.escape(role)}</div>
            </div>
        </div>
        <div class="persona-meta-row">
            <span>Role: <strong class="persona-role-highlight">{html.escape(role.split('(')[0].strip())}</strong></span>
            <span class="persona-badge">{html.escape(stage)}</span>
        </div>
    </div>
    """


def render_user_query_html(question: str) -> str:
    """Render a cleanly styled user query card."""
    return f"""
    <div class="user-query-container">
        <div class="user-query-tag">You asked</div>
        <div class="user-query-text">{html.escape(question)}</div>
    </div>
    """


def render_segmented_progress_html(done_count: int, total_count: int) -> str:
    """Render a segmented progress bar of small blocks with percentage."""
    total = max(total_count, 1)
    percent = int((done_count / total) * 100)
    segments_html = []
    for i in range(total):
        cls = "progress-segment filled" if i < done_count else "progress-segment"
        segments_html.append(f'<div class="{cls}"></div>')

    joined_segments = "".join(segments_html)
    return f"""
    <div class="progress-container">
        <div class="progress-header">
            <span>Onboarding Progress</span>
            <span class="progress-percent-label">{percent}% ({done_count}/{total})</span>
        </div>
        <div class="segmented-bar">
            {joined_segments}
        </div>
        <div class="progress-text">
            <span>{done_count} of {total} steps completed</span>
            <span>{total - done_count} remaining</span>
        </div>
    </div>
    """


def render_sources_footer_html(sources: List[SourceRef]) -> str:
    """Render grounded source citation chips with links."""
    if not sources:
        return ""

    chips_html = []
    seen_ids = set()

    for s in sources:
        if s.id in seen_ids:
            continue
        seen_ids.add(s.id)

        kind_class = "live" if s.kind == "live" else "local"
        label = html.escape(s.label)
        chip_content = f"{html.escape(s.id)} · {label}"

        if s.url:
            chips_html.append(
                f'<a class="source-chip {kind_class}" href="{html.escape(s.url)}" target="_blank" rel="noopener noreferrer">{chip_content} ↗</a>'
            )
        else:
            chips_html.append(
                f'<span class="source-chip {kind_class}">{chip_content}</span>'
            )

    return f"""
    <div class="sources-footer">
        <div style="font-family:var(--font-mono); font-size:10px; font-weight:600; text-transform:uppercase; color:var(--text-muted); width:100%; margin-bottom:4px;">Grounded Sources</div>
        {''.join(chips_html)}
    </div>
    """


def render_trace_summary_html(
    steps: int,
    handbook_count: int,
    live_count: int,
    provider: str,
    elapsed_s: float,
    trace_rows: List[Dict[str, Any]],
) -> str:
    """Render collapsible execution trace using native details element."""
    summary_text = (
        f"Execution Trace: {steps} steps · {handbook_count} handbook · {live_count} live index · "
        f"{html.escape(provider)} · {elapsed_s:.1f} s"
    )

    rows_html = []
    for idx, row in enumerate(trace_rows, start=1):
        num_str = f"STEP {idx}"
        tool_name = html.escape(row.get("name", ""))
        kind = html.escape(row.get("kind", ""))
        dur = f"{row.get('duration_ms', 0) / 1000:.2f} s"
        summary = html.escape(row.get("summary", ""))

        rows_html.append(
            f"""
            <div class="trace-row">
                <span><strong style="color:var(--accent-primary);">{num_str}:</strong>&nbsp;&nbsp;<code>{tool_name}</code>&nbsp;&nbsp;<span style="color:var(--text-muted);">({kind})</span></span>
                <span><span style="color:var(--text-muted); margin-right:12px;">{summary}</span>{dur}</span>
            </div>
            """
        )

    return f"""
    <details class="trace-details">
        <summary>{summary_text}</summary>
        <div style="margin-top:6px;">
            {''.join(rows_html)}
        </div>
    </details>
    """


def render_proposal_card_html(preview: WritePreview) -> str:
    """Render human-in-the-loop write proposal card matching Stitch amber styling."""
    return f"""
    <div class="proposal-card">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
            <div class="proposal-title">Action Required · Human-in-the-Loop Proposal</div>
            <span style="font-family:var(--font-mono); font-size:10px; color:var(--proposal-primary); background:var(--proposal-badge); padding:2px 6px; border-radius:var(--radius-sm); font-weight:600;">Safe Dry-Run</span>
        </div>
        <div class="proposal-body"><strong>Proposed state update:</strong> {html.escape(preview.description)}</div>
    </div>
    """


def render_step_row_html(task: TaskProgress, is_next: bool = False) -> str:
    """Render an onboarding checklist path step row."""
    status_class = task.status
    badge_label = "completed" if task.status == "done" else ("next milestone" if is_next else "todo")
    badge_class = "done" if task.status == "done" else ("next" if is_next else "todo")

    return f"""
    <div class="step-row {status_class}">
        <div class="step-header">
            <div>
                <span style="font-family:var(--font-mono); font-size:12px; font-weight:600; color:var(--accent-primary); margin-right:8px;">{task.ordinal:02d}</span>
                <span class="step-title">{html.escape(task.title)}</span>
            </div>
            <span class="step-badge {badge_class}">{badge_label}</span>
        </div>
        <div style="font-size:13px; color:var(--text-secondary); margin-top:6px; line-height:1.5;">
            {html.escape(task.description)}
            {f'<div style="margin-top:4px; font-family:var(--font-mono); font-size:11px; color:var(--accent-primary);">Handbook Reference: {html.escape(task.handbook_ref)}</div>' if task.handbook_ref else ''}
        </div>
    </div>
    """


def render_cohort_table_html(cohort_res: Any) -> str:
    """Render cohort velocity matrix for team leads."""
    rows = []
    for m in cohort_res.cohort:
        status_color = "var(--text-muted)" if not m.stalled else "var(--proposal-primary)"
        status_label = "On Track" if not m.stalled else "Stalled (< 4 steps)"
        rows.append(
            f"""
            <tr style="border-bottom:1px solid var(--border-hairline); font-size:13px;">
                <td style="padding:10px 12px; font-weight:600; color:var(--text-ink);">{html.escape(m.display_name)}</td>
                <td style="padding:10px 12px; color:var(--text-muted); font-family:var(--font-mono); font-size:12px;">{html.escape(m.role)}</td>
                <td style="padding:10px 12px; font-family:var(--font-mono); font-weight:600; color:var(--accent-primary);">{m.done_count} / 12 ({m.progress_pct}%)</td>
                <td style="padding:10px 12px; color:var(--text-ink);">{html.escape(m.current_milestone or 'Completed')}</td>
                <td style="padding:10px 12px; color:{status_color}; font-weight:600; font-size:11px; text-transform:uppercase;">{status_label}</td>
            </tr>
            """
        )

    bottlenecks_html = ""
    if cohort_res.top_bottlenecks:
        items = "".join(f"<li style='margin-bottom:4px;'>{html.escape(b)}</li>" for b in cohort_res.top_bottlenecks)
        bottlenecks_html = f"""
        <div style="margin-top:14px; padding:12px; background:var(--bg-card); border:1px solid var(--border-hairline); border-radius:var(--radius-md);">
            <div style="font-weight:600; font-size:12px; text-transform:uppercase; color:var(--text-muted); margin-bottom:6px;">Top Cohort Bottlenecks</div>
            <ul style="margin:0; padding-left:18px; font-size:13px; color:var(--text-ink);">{items}</ul>
        </div>
        """

    return f"""
    <div style="background:var(--bg-surface); border:1px solid var(--border-hairline); border-radius:var(--radius-lg); padding:16px; margin-bottom:16px; box-shadow:var(--shadow-subtle);">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
            <div>
                <span style="font-family:var(--font-serif); font-size:18px; font-weight:600; color:var(--text-ink);">Cohort Onboarding Velocity</span>
                <span style="margin-left:12px; font-family:var(--font-mono); font-size:12px; color:var(--text-muted);">Avg Completion: {cohort_res.average_completion_pct}%</span>
            </div>
            <span style="font-family:var(--font-mono); font-size:11px; padding:3px 8px; border-radius:var(--radius-sm); background:var(--accent-tint); color:var(--accent-primary); font-weight:600;">Team Lead Oversight</span>
        </div>
        <table style="width:100%; border-collapse:collapse; text-align:left;">
            <thead>
                <tr style="border-bottom:2px solid var(--border-hairline); font-size:11px; font-family:var(--font-mono); color:var(--text-muted); text-transform:uppercase;">
                    <th style="padding:8px 12px;">Developer</th>
                    <th style="padding:8px 12px;">Role</th>
                    <th style="padding:8px 12px;">Milestones</th>
                    <th style="padding:8px 12px;">Current Step</th>
                    <th style="padding:8px 12px;">Status</th>
                </tr>
            </thead>
            <tbody>
                {''.join(rows)}
            </tbody>
        </table>
        {bottlenecks_html}
    </div>
    """


def render_preflight_card_html(preflight_res: Any) -> str:
    """Render automated PR pre-flight check card."""
    is_ready = preflight_res.ready_for_review
    badge_bg = "var(--accent-tint)" if is_ready else "var(--proposal-badge)"
    badge_color = "var(--accent-primary)" if is_ready else "var(--proposal-primary)"
    status_text = "READY FOR SENIOR REVIEW" if is_ready else "ACTION REQUIRED BEFORE REVIEW"

    checks_html = []
    for c in preflight_res.checks:
        icon = "[PASS]" if c.passed else "[FAIL]"
        color = "var(--accent-primary)" if c.passed else "var(--proposal-primary)"
        checks_html.append(
            f"""
            <div style="display:flex; justify-content:space-between; align-items:flex-start; padding:8px 0; border-bottom:1px solid var(--border-hairline); font-size:13px;">
                <div>
                    <span style="font-family:var(--font-mono); font-size:11px; font-weight:600; color:{color}; margin-right:8px;">{icon}</span>
                    <strong style="color:var(--text-ink);">{html.escape(c.rule)}:</strong>
                    <span style="color:var(--text-secondary); margin-left:6px;">{html.escape(c.detail)}</span>
                    {f'<div style="font-size:12px; color:var(--proposal-primary); margin-top:2px; margin-left:22px;">Recommendation: {html.escape(c.recommendation)}</div>' if c.recommendation else ''}
                </div>
            </div>
            """
        )

    checklist_items = "".join(f"<li style='margin-bottom:3px;'>{html.escape(item)}</li>" for item in preflight_res.senior_review_checklist)

    return f"""
    <div style="background:var(--bg-surface); border:1px solid var(--border-hairline); border-radius:var(--radius-lg); padding:16px; margin-bottom:16px; box-shadow:var(--shadow-subtle);">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
            <div>
                <span style="font-family:var(--font-serif); font-size:17px; font-weight:600; color:var(--text-ink);">{html.escape(preflight_res.pr_title or 'PR Pre-Flight Audit')}</span>
            </div>
            <span style="font-family:var(--font-mono); font-size:11px; padding:3px 8px; border-radius:var(--radius-sm); background:{badge_bg}; color:{badge_color}; font-weight:600;">{status_text}</span>
        </div>
        <div style="margin-top:8px;">
            {''.join(checks_html)}
        </div>
        <div style="margin-top:14px; padding:10px 12px; background:var(--bg-card); border:1px solid var(--border-hairline); border-radius:var(--radius-md);">
            <div style="font-weight:600; font-size:11px; font-family:var(--font-mono); text-transform:uppercase; color:var(--text-muted); margin-bottom:4px;">Senior Reviewer Verification Checklist</div>
            <ul style="margin:0; padding-left:18px; font-size:12px; color:var(--text-ink);">{checklist_items}</ul>
        </div>
    </div>
    """


def render_doctor_report_html(doc_res: Any) -> str:
    """Render local environment doctor report card."""
    is_ok = doc_res.all_passed
    badge_bg = "var(--accent-tint)" if is_ok else "var(--proposal-badge)"
    badge_color = "var(--accent-primary)" if is_ok else "var(--proposal-primary)"
    badge_text = "ALL PREREQUISITES MET" if is_ok else "REMEDIES RECOMMENDED"

    rows = []
    for c in doc_res.checks:
        stat_color = "var(--accent-primary)" if c.status == "pass" else ("var(--proposal-primary)" if c.status == "fail" else "var(--text-muted)")
        rows.append(
            f"""
            <tr style="border-bottom:1px solid var(--border-hairline); font-size:13px;">
                <td style="padding:8px 10px; font-weight:600; color:var(--text-ink);">{html.escape(c.name)}</td>
                <td style="padding:8px 10px; font-family:var(--font-mono); font-size:11px; font-weight:600; color:{stat_color}; text-transform:uppercase;">{c.status}</td>
                <td style="padding:8px 10px; font-family:var(--font-mono); font-size:12px; color:var(--text-ink);">{html.escape(c.found or 'none')}</td>
                <td style="padding:8px 10px; font-family:var(--font-mono); font-size:12px; color:var(--text-muted);">{html.escape(c.required)}</td>
            </tr>
            {f'<tr><td colspan="4" style="padding:4px 10px 8px 10px; font-size:12px; color:var(--proposal-primary); background:var(--bg-card);">Remedy: <code>{html.escape(c.remedy)}</code></td></tr>' if c.remedy else ''}
            """
        )

    return f"""
    <div style="background:var(--bg-surface); border:1px solid var(--border-hairline); border-radius:var(--radius-lg); padding:16px; margin-bottom:16px; box-shadow:var(--shadow-subtle);">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
            <div>
                <span style="font-family:var(--font-serif); font-size:17px; font-weight:600; color:var(--text-ink);">Local Environment Doctor</span>
                <span style="margin-left:12px; font-family:var(--font-mono); font-size:12px; color:var(--text-muted);">{html.escape(doc_res.os_platform)}</span>
            </div>
            <span style="font-family:var(--font-mono); font-size:11px; padding:3px 8px; border-radius:var(--radius-sm); background:{badge_bg}; color:{badge_color}; font-weight:600;">{badge_text}</span>
        </div>
        <table style="width:100%; border-collapse:collapse; text-align:left; margin-top:8px;">
            <thead>
                <tr style="border-bottom:2px solid var(--border-hairline); font-size:11px; font-family:var(--font-mono); color:var(--text-muted); text-transform:uppercase;">
                    <th style="padding:6px 10px;">Tool / Dependency</th>
                    <th style="padding:6px 10px;">Status</th>
                    <th style="padding:6px 10px;">Detected</th>
                    <th style="padding:6px 10px;">Target</th>
                </tr>
            </thead>
            <tbody>
                {''.join(rows)}
            </tbody>
        </table>
    </div>
    """
