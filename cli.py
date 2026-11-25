"""Onboarding Assistant — Developer & Senior CLI Entrypoint.

Enables terminal-first interaction, IDE integration, local diagnostics,
and automated PR pre-flight checks without opening a browser.
"""

from __future__ import annotations

import argparse
import sys
from typing import Optional

from config import config
from agent.agent import Agent
from agent.events import (
    FinalAnswerEvent,
    ProposalRequestedEvent,
    ToolCallEvent,
    ToolResultEvent,
)
from agent.mcp_bridge import get_mcp_bridge
from mcp_server.db import get_db_connection, init_db
from mcp_server.tools.live_review_tools import check_pr_preflight
from mcp_server.tools.local_doctor_tools import diagnose_local_environment
from mcp_server.tools.local_escalation_tools import get_cohort_progress
from mcp_server.tools.local_progress_tools import get_onboarding_progress


def cmd_ask(question: str, user_id: str) -> None:
    """Ask an onboarding question from the terminal."""
    init_db()
    bridge = get_mcp_bridge()
    agent = Agent(bridge=bridge)

    print(f"\n[Onboarding Assistant: {config.target_repo}]")
    print(f"User: {user_id}")
    print(f"Question: {question}\n" + "-" * 60)

    for event in agent.run(question=question, user_id=user_id):
        if isinstance(event, ToolCallEvent):
            print(f"-> Calling Tool [{event.kind}]: {event.name}(...)")
        elif isinstance(event, ToolResultEvent):
            status = "OK" if event.ok else "ERR"
            print(f"   [{status}] {event.summary} ({event.duration_ms}ms)")
        elif isinstance(event, ProposalRequestedEvent):
            print(f"\n[PROPOSAL GENERATED] {event.proposal.preview.description}")
            print("Run with Streamlit UI or approval tool to apply.")
        elif isinstance(event, FinalAnswerEvent):
            print("\n" + "=" * 60)
            print(event.markdown)
            print("=" * 60)
            if event.sources:
                print("\nSources:")
                for s in event.sources:
                    print(f"  [{s.id}] {s.label} ({s.url or 'local'})")
            print(f"\n[Completed in {event.elapsed_s}s using {event.provider_used}]")


def cmd_doctor() -> None:
    """Run local environment doctor audit."""
    res = diagnose_local_environment()
    print("\n=== Local Environment Doctor Audit ===")
    print(f"OS Platform: {res.os_platform}")
    print(f"Overall Status: {'PASSED' if res.all_passed else 'WARNINGS / REMEDIES REQUIRED'}\n")
    print(f"{'Check':<25} | {'Status':<6} | {'Found':<28} | {'Required':<20}")
    print("-" * 88)
    for c in res.checks:
        stat = c.status.upper()
        found = c.found or "none"
        print(f"{c.name:<25} | {stat:<6} | {found:<28} | {c.required:<20}")
        if c.remedy:
            print(f"   -> Remedy: {c.remedy}")

    if res.recommendations:
        print("\nActionable Recommendations:")
        for r in res.recommendations:
            print(f"  * {r}")
    print()


def cmd_preflight(pr_num: Optional[int], title: Optional[str]) -> None:
    """Run automated PR pre-flight check."""
    res = check_pr_preflight(pr_number=pr_num, title=title or "")
    print(f"\n=== PR Pre-Flight Audit: {res.pr_title} ===")
    print(f"Readiness: {'READY FOR SENIOR REVIEW' if res.ready_for_review else 'ACTION REQUIRED BEFORE REVIEW'}\n")

    for c in res.checks:
        mark = "[PASS]" if c.passed else "[FAIL]"
        print(f"{mark} {c.rule}: {c.detail}")
        if c.recommendation:
            print(f"       Recommendation: {c.recommendation}")

    if res.sensitive_paths_touched:
        print(f"\n[ALERT] Restricted Paths Touched: {', '.join(res.sensitive_paths_touched)}")

    print("\nSenior Reviewer Checklist:")
    for item in res.senior_review_checklist:
        print(f"  [ ] {item}")
    print()


def cmd_progress(user_id: str) -> None:
    """Display onboarding milestone progress for a user."""
    init_db()
    res = get_onboarding_progress(user_id=user_id)
    print(f"\n=== Onboarding Milestone Progress ({user_id}) ===")
    print(f"Completed: {res.done_count} / {res.total_count} tasks\n")

    for t in res.tasks:
        mark = "[x]" if t.status == "done" else "[ ]"
        print(f"{mark} Step {t.ordinal:02d}: {t.title} ({t.status})")

    if res.next_suggested_task:
        nxt = res.next_suggested_task
        print(f"\nNext Recommended Step: Step {nxt.ordinal:02d}: '{nxt.title}'")
    print()


def cmd_cohort() -> None:
    """Display cohort velocity and bottlenecks for senior leads."""
    init_db()
    res = get_cohort_progress()
    print("\n=== Cohort Onboarding Velocity (Lead Oversight) ===")
    print(f"Cohort Average Completion: {res.average_completion_pct}%")
    print(f"Developers Stalled (< 4 steps): {res.stalled_count}\n")
    print(f"{'User ID':<15} | {'Name':<20} | {'Role':<22} | {'Progress':<10} | {'Current Milestone'}")
    print("-" * 95)
    for m in res.cohort:
        prog_str = f"{m.done_count}/12 ({m.progress_pct}%)"
        print(f"{m.user_id:<15} | {m.display_name:<20} | {m.role:<22} | {prog_str:<10} | {m.current_milestone}")

    if res.top_bottlenecks:
        print("\nTop Cohort Bottlenecks:")
        for b in res.top_bottlenecks:
            print(f"  * {b}")
    print()


def cmd_server() -> None:
    """Run the MCP server over stdio for external IDEs (Cursor, VS Code, Claude Code)."""
    from mcp_server.server import main as run_server
    run_server()


def cmd_logs(lines: int = 50, level: Optional[str] = None) -> None:
    """Stream recent application logs from disk."""
    from logging_config import read_recent_logs
    log_lines = read_recent_logs(max_lines=lines, level_filter=level)
    print(f"\n=== Onboarding Assistant Logs (Last {lines} lines, filter={level or 'ALL'}) ===")
    if not log_lines:
        print("No log entries found.")
    else:
        for line in log_lines:
            print(line)
    print()


def cmd_audit(limit: int = 25) -> None:
    """Display recent MCP security and privacy audit entries."""
    from logging_config import get_audit_records
    records = get_audit_records(limit=limit)
    print(f"\n=== MCP Security & Audit Trail (Latest {limit} entries) ===")
    if not records:
        print("No audit records found in SQLite.")
    else:
        print(f"{'Timestamp (UTC)':<20} | {'Tool Name':<28} | {'Status':<10} | {'Bytes':<8} | {'Redactions':<10} | {'Arguments SHA-256'}")
        print("-" * 105)
        for r in records:
            short_ts = r['ts'][:19].replace('T', ' ')
            short_sha = r['args_sha256'][:16] + "..."
            print(f"{short_ts:<20} | {r['tool']:<28} | {r['status']:<10} | {r['bytes_returned']:<8} | {r['redactions']:<10} | {short_sha}")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="onboard",
        description="Onboarding Assistant — Developer CLI & IDE Integration",
    )
    subparsers = parser.add_subparsers(dest="subcommand", help="Available commands")

    # Ask
    p_ask = subparsers.add_parser("ask", help="Ask an onboarding question")
    p_ask.add_argument("question", help="The question to ask")
    p_ask.add_argument("--user", default="user_ravi", help="User ID persona")

    # Doctor
    subparsers.add_parser("doctor", help="Audit local environment (Python, Rust, Git, virtualenv)")

    # Preflight
    p_pref = subparsers.add_parser("preflight", help="Run PR pre-flight check")
    p_pref.add_argument("--pr", type=int, default=None, help="PR number on GitHub")
    p_pref.add_argument("--title", default="", help="PR title to validate")

    # Progress
    p_prog = subparsers.add_parser("progress", help="Show onboarding milestone progress")
    p_prog.add_argument("--user", default="user_ravi", help="User ID")

    # Cohort
    subparsers.add_parser("cohort", help="Show cohort onboarding analytics (Lead view)")

    # Server
    subparsers.add_parser("server", help="Run MCP server over stdio (for Cursor, VS Code, Claude Code)")

    # Logs
    p_logs = subparsers.add_parser("logs", help="Stream recent application activity logs")
    p_logs.add_argument("--lines", type=int, default=50, help="Number of lines to show")
    p_logs.add_argument("--level", default=None, help="Filter level: INFO, WARNING, ERROR")

    # Audit
    p_audit = subparsers.add_parser("audit", help="Display MCP tool execution audit records")
    p_audit.add_argument("--limit", type=int, default=25, help="Number of records to show")

    args = parser.parse_args()

    if args.subcommand == "ask":
        cmd_ask(question=args.question, user_id=args.user)
    elif args.subcommand == "doctor":
        cmd_doctor()
    elif args.subcommand == "preflight":
        cmd_preflight(pr_num=args.pr, title=args.title)
    elif args.subcommand == "progress":
        cmd_progress(user_id=args.user)
    elif args.subcommand == "cohort":
        cmd_cohort()
    elif args.subcommand == "server":
        cmd_server()
    elif args.subcommand == "logs":
        cmd_logs(lines=args.lines, level=args.level)
    elif args.subcommand == "audit":
        cmd_audit(limit=args.limit)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

