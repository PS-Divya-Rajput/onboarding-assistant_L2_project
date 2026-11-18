"""Smart Escalation Packet and Cohort Oversight tools for Onboarding assistant.

Provides structured escalation summaries for senior engineers/leads and aggregates
cohort onboarding velocity analytics across all developers.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from mcp_server.db import get_db_connection
from mcp_server.privacy import audit_tool_call, sanitize_untrusted_text
from mcp_server.schemas import (
    CohortMemberProgress,
    CohortProgressResult,
    SmartEscalationResult,
    SourceRef,
    ToolError,
)
from mcp_server.tools.live_owner_tools import find_code_owners


def generate_smart_escalation(
    user_id: str,
    question: str,
    steps_attempted: Optional[List[str]] = None,
    path_context: Optional[str] = None,
) -> SmartEscalationResult:
    """Generate a structured, zero-effort Senior Escalation Packet for Slack or GitHub."""
    clean_user = user_id.strip()
    clean_question = sanitize_untrusted_text(question)
    attempts = list(steps_attempted or ["Checked repository handbook and setup guides."])

    # 1. Fetch user information
    display_name = clean_user
    user_role = "Developer"
    with get_db_connection() as conn:
        row = conn.execute("SELECT display_name, role FROM users WHERE id = ?", (clean_user,)).fetchone()
        if row:
            display_name = row["display_name"]
            user_role = row["role"]

    # 2. Identify relevant code owners
    target_path = path_context or "crates"
    owners_res = find_code_owners(path=target_path)
    owners = owners_res.owners or ["@core-maintainers"]

    # 3. Format markdown escalation packet
    mentions_str = " ".join(owners)
    attempts_str = "\n".join(f"- {a}" for a in attempts)
    escalation_md = f"""### Senior Escalation Packet
**To**: {mentions_str}
**From**: {display_name} ({user_role})
**Topic**: {clean_question}

#### Context & Diagnostics:
- **Target Area**: `{target_path}`
- **Steps Attempted**:
{attempts_str}
- **Assistance Requested**: Clarification on expected configuration or architectural guidance for `{target_path}`.
"""

    slack_payload = {
        "text": f"Onboarding Escalation from {display_name}: {clean_question}",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Onboarding Escalation for {mentions_str}*\n*From*: {display_name} ({user_role})\n*Topic*: {clean_question}",
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Path*: `{target_path}`\n*Steps Attempted*:\n{attempts_str}",
                },
            },
        ],
    }

    res = SmartEscalationResult(
        developer_name=display_name,
        developer_role=user_role,
        topic=clean_question,
        owners=owners,
        escalation_packet_markdown=escalation_md,
        slack_payload=slack_payload,
        source_refs=[
            SourceRef(
                id="ESCALATION-PKG",
                kind="local",
                label=f"Escalation Packet ({display_name})",
                url=None,
            )
        ],
    )

    audit_tool_call(
        tool_name="generate_smart_escalation",
        args={"user_id": clean_user, "topic": clean_question},
        status="success",
        payload_obj=res,
        redaction_count=0,
    )
    return res


def get_cohort_progress() -> CohortProgressResult:
    """Aggregate onboarding velocity, completion percentages, and bottlenecks for team leads."""
    cohort_list: List[CohortMemberProgress] = []
    total_pct_sum = 0.0
    stalled_count = 0
    bottleneck_candidates: Dict[str, int] = {}

    with get_db_connection() as conn:
        users = conn.execute("SELECT id, display_name, role FROM users ORDER BY id ASC").fetchall()
        for u in users:
            uid = u["id"]
            d_name = u["display_name"]
            role = u["role"]

            # Count completed tasks
            done_row = conn.execute(
                "SELECT COUNT(*) as cnt FROM user_progress WHERE user_id = ? AND status = 'done'",
                (uid,),
            ).fetchone()
            done_cnt = done_row["cnt"] if done_row else 0
            pct = round((done_cnt / 12.0) * 100, 1)
            total_pct_sum += pct

            # Get current/next task
            next_row = conn.execute(
                """
                SELECT t.title, t.ordinal
                FROM tasks t
                LEFT JOIN user_progress up ON t.id = up.task_id AND up.user_id = ?
                WHERE up.status IS NULL OR up.status != 'done'
                ORDER BY t.ordinal ASC
                LIMIT 1
                """,
                (uid,),
            ).fetchone()

            curr_milestone = f"Step {next_row['ordinal']}: {next_row['title']}" if next_row else "All 12 Completed"
            is_stalled = done_cnt < 4

            if is_stalled:
                stalled_count += 1
            if next_row:
                b_name = f"Step {next_row['ordinal']:02d}: {next_row['title']}"
                bottleneck_candidates[b_name] = bottleneck_candidates.get(b_name, 0) + 1

            cohort_list.append(
                CohortMemberProgress(
                    user_id=uid,
                    display_name=d_name,
                    role=role,
                    done_count=done_cnt,
                    total_count=12,
                    progress_pct=pct,
                    current_milestone=curr_milestone,
                    stalled=is_stalled,
                )
            )

    avg_pct = round(total_pct_sum / max(len(cohort_list), 1), 1)
    sorted_bottlenecks = sorted(bottleneck_candidates.items(), key=lambda x: x[1], reverse=True)
    top_bottlenecks = [b[0] for b in sorted_bottlenecks[:3]]

    res = CohortProgressResult(
        cohort=cohort_list,
        average_completion_pct=avg_pct,
        stalled_count=stalled_count,
        top_bottlenecks=top_bottlenecks,
        source_refs=[
            SourceRef(
                id="COHORT-METRICS",
                kind="local",
                label="Cohort Onboarding Metrics",
                url=None,
            )
        ],
    )

    audit_tool_call(
        tool_name="get_cohort_progress",
        args={},
        status="success",
        payload_obj=res,
        redaction_count=0,
    )
    return res

