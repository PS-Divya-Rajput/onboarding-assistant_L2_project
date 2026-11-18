"""Local progress tracking, checklist inspection, and write tools for Onboarding assistant.

Enforces human-in-the-loop write authorization protocol:
Write operations default to dry_run=True, returning a detailed preview without modifying
the database until explicitly applied by human action in the UI.
"""

from __future__ import annotations

import datetime
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional
from mcp_server.db import get_db_connection
from mcp_server.privacy import audit_tool_call
from mcp_server.schemas import (
    LogQuestionResult,
    MarkTaskDoneResult,
    OnboardingProgressResult,
    SourceRef,
    TaskProgress,
    ToolError,
    WritePreview,
)


def get_onboarding_progress(user_id: str, db_path: Path | str | None = None) -> OnboardingProgressResult:
    """Retrieve the checklist of onboarding steps, completion counts, and the next suggested step for a user."""
    clean_user = user_id.strip()

    source_refs = [
        SourceRef(
            id="S1",
            kind="local",
            label=f"Onboarding Checklist ({clean_user})",
            url=None,
        )
    ]

    try:
        with get_db_connection(db_path) as conn:
            user_row = conn.execute("SELECT id, display_name FROM users WHERE id = ?", (clean_user,)).fetchone()
            if not user_row:
                res = OnboardingProgressResult(
                    user_id=clean_user,
                    error=ToolError(code="user_not_found", message=f"User '{clean_user}' not found in database."),
                    source_refs=source_refs,
                )
                audit_tool_call("get_onboarding_progress", {"user_id": user_id}, "error", res, 0)
                return res

            query = """
                SELECT t.id, t.ordinal, t.title, t.description, t.handbook_ref,
                       COALESCE(up.status, 'todo') AS status
                FROM tasks t
                LEFT JOIN user_progress up ON t.id = up.task_id AND up.user_id = ?
                ORDER BY t.ordinal ASC
            """
            rows = conn.execute(query, (clean_user,)).fetchall()

            tasks: List[TaskProgress] = []
            done_count = 0
            next_suggested: Optional[TaskProgress] = None

            for r in rows:
                status_val = r["status"]
                if status_val not in ("todo", "in_progress", "done"):
                    status_val = "todo"
                if status_val == "done":
                    done_count += 1

                task_obj = TaskProgress(
                    id=r["id"],
                    ordinal=r["ordinal"],
                    title=r["title"],
                    description=r["description"],
                    handbook_ref=r["handbook_ref"],
                    status=status_val,
                )
                tasks.append(task_obj)

                # Next suggested task is the first non-done task
                if next_suggested is None and status_val in ("in_progress", "todo"):
                    next_suggested = task_obj

            res = OnboardingProgressResult(
                user_id=clean_user,
                tasks=tasks,
                done_count=done_count,
                total_count=len(tasks),
                next_suggested_task=next_suggested,
                source_refs=source_refs,
            )
            audit_tool_call("get_onboarding_progress", {"user_id": user_id}, "success", res, 0)
            return res

    except Exception as exc:
        res = OnboardingProgressResult(
            user_id=clean_user,
            error=ToolError(code="db_error", message=f"Database query error: {type(exc).__name__}: {exc}"),
            source_refs=source_refs,
        )
        audit_tool_call("get_onboarding_progress", {"user_id": user_id}, "error", res, 0)
        return res


def mark_task_done(
    user_id: str,
    task_id: int,
    dry_run: bool = True,
    db_path: Path | str | None = None,
) -> MarkTaskDoneResult:
    """Mark an onboarding checklist task as completed.

    Defaults to dry_run=True, returning an action preview for user confirmation.
    Only writes changes when dry_run is explicitly False.
    """
    clean_user = user_id.strip()
    source_refs = [
        SourceRef(
            id="S1",
            kind="local",
            label="SQLite Progress Store",
            url=None,
        )
    ]

    try:
        with get_db_connection(db_path) as conn:
            user_row = conn.execute("SELECT id, display_name FROM users WHERE id = ?", (clean_user,)).fetchone()
            if not user_row:
                res = MarkTaskDoneResult(
                    task_id=task_id,
                    dry_run=dry_run,
                    error=ToolError(code="user_not_found", message=f"User '{clean_user}' not found."),
                    source_refs=source_refs,
                )
                audit_tool_call("mark_task_done", {"user_id": user_id, "task_id": task_id, "dry_run": dry_run}, "error", res, 0)
                return res

            task_row = conn.execute("SELECT id, ordinal, title FROM tasks WHERE id = ?", (task_id,)).fetchone()
            if not task_row:
                res = MarkTaskDoneResult(
                    task_id=task_id,
                    dry_run=dry_run,
                    error=ToolError(code="task_not_found", message=f"Task ID {task_id} does not exist."),
                    source_refs=source_refs,
                )
                audit_tool_call("mark_task_done", {"user_id": user_id, "task_id": task_id, "dry_run": dry_run}, "error", res, 0)
                return res

            # Check current status
            curr_row = conn.execute(
                "SELECT status FROM user_progress WHERE user_id = ? AND task_id = ?",
                (clean_user, task_id),
            ).fetchone()
            old_status = curr_row["status"] if curr_row else "todo"

            preview = WritePreview(
                action="mark_task_done",
                user_id=clean_user,
                description=f'Mark step {task_row["ordinal"]} "{task_row["title"]}" as done for {user_row["display_name"]}',
                changes={"task_id": task_id, "old_status": old_status, "new_status": "done"},
            )

            # If dry_run, return proposal preview without modifying DB
            if dry_run:
                res = MarkTaskDoneResult(
                    success=True,
                    dry_run=True,
                    task_id=task_id,
                    preview=preview,
                    source_refs=source_refs,
                )
                audit_tool_call("mark_task_done", {"user_id": user_id, "task_id": task_id, "dry_run": dry_run}, "preview", res, 0)
                return res

            # Apply write
            now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
            conn.execute(
                """
                INSERT INTO user_progress (user_id, task_id, status, updated_at)
                VALUES (?, ?, 'done', ?)
                ON CONFLICT(user_id, task_id) DO UPDATE SET status = 'done', updated_at = excluded.updated_at
                """,
                (clean_user, task_id, now_iso),
            )
            conn.commit()

            res = MarkTaskDoneResult(
                success=True,
                dry_run=False,
                task_id=task_id,
                preview=preview,
                source_refs=source_refs,
            )
            audit_tool_call("mark_task_done", {"user_id": user_id, "task_id": task_id, "dry_run": dry_run}, "applied", res, 0)
            return res

    except Exception as exc:
        res = MarkTaskDoneResult(
            task_id=task_id,
            dry_run=dry_run,
            error=ToolError(code="db_error", message=f"Failed to update task progress: {type(exc).__name__}: {exc}"),
            source_refs=source_refs,
        )
        audit_tool_call("mark_task_done", {"user_id": user_id, "task_id": task_id, "dry_run": dry_run}, "error", res, 0)
        return res


def log_question(
    user_id: str,
    question: str,
    answered_from: Literal["handbook", "live", "none"],
    resolved: bool,
    dry_run: bool = True,
    db_path: Path | str | None = None,
) -> LogQuestionResult:
    """Log an onboarding question, resolution status, and knowledge source.

    Defaults to dry_run=True for human confirmation before persisting to the database.
    """
    clean_user = user_id.strip()
    clean_q = question.strip()
    source_refs = [
        SourceRef(
            id="S1",
            kind="local",
            label="SQLite Question Log",
            url=None,
        )
    ]

    try:
        with get_db_connection(db_path) as conn:
            user_row = conn.execute("SELECT id, display_name FROM users WHERE id = ?", (clean_user,)).fetchone()
            display_name = user_row["display_name"] if user_row else clean_user

            source_label = "handbook documentation" if answered_from == "handbook" else ("live GitHub API" if answered_from == "live" else "unanswered")
            status_label = "resolved" if resolved else "unresolved (gap)"

            preview = WritePreview(
                action="log_question",
                user_id=clean_user,
                description=f'Log question "{clean_q}" for {display_name} ({source_label}, {status_label})',
                changes={
                    "question": clean_q,
                    "answered_from": answered_from,
                    "resolved": resolved,
                },
            )

            if dry_run:
                res = LogQuestionResult(
                    success=True,
                    dry_run=True,
                    question=clean_q,
                    preview=preview,
                    source_refs=source_refs,
                )
                audit_tool_call("log_question", {"user_id": user_id, "question": question, "dry_run": dry_run}, "preview", res, 0)
                return res

            now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
            cursor = conn.execute(
                """
                INSERT INTO question_log (user_id, question, answered_from, resolved, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (clean_user, clean_q, answered_from, 1 if resolved else 0, now_iso),
            )
            conn.commit()
            new_id = cursor.lastrowid

            res = LogQuestionResult(
                success=True,
                dry_run=False,
                question=clean_q,
                preview=preview,
                question_id=new_id,
                source_refs=source_refs,
            )
            audit_tool_call("log_question", {"user_id": user_id, "question": question, "dry_run": dry_run}, "applied", res, 0)
            return res

    except Exception as exc:
        res = LogQuestionResult(
            success=False,
            dry_run=dry_run,
            question=clean_q,
            error=ToolError(code="db_error", message=f"Failed to log question: {type(exc).__name__}: {exc}"),
            source_refs=source_refs,
        )
        audit_tool_call("log_question", {"user_id": user_id, "question": question, "dry_run": dry_run}, "error", res, 0)
        return res

