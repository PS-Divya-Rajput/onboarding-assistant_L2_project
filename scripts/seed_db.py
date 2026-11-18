"""Database seeding script for Onboarding assistant.

Derives 12 realistic onboarding tasks directly from Ruff's CONTRIBUTING.md.
Creates 3 clearly labelled simulated sample users at different onboarding stages.
Populates simulated historical question logs so the UI views render realistic content.
"""

from __future__ import annotations

import datetime
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mcp_server.db import get_db_connection, init_db

# Fixture notice: These sample users and question logs represent simulated onboarding state.
TASKS_FIXTURE = [
    (1, "Fork and clone repository", "Fork astral-sh/ruff on GitHub and clone your fork locally.", "CONTRIBUTING.md"),
    (2, "Install Rust toolchain", "Install official Rust toolchain via rustup for compiling the Rust workspace.", "CONTRIBUTING.md"),
    (3, "Install uv package manager", "Install Astral's uv to run Python utility commands and manage dev dependencies.", "CONTRIBUTING.md"),
    (4, "Build Ruff locally", "Compile and run Ruff locally using 'cargo run -p ruff -- check <file> --no-cache'.", "CONTRIBUTING.md"),
    (5, "Run the test suite", "Execute the workspace test suite using nextest or 'RUFF_UPDATE_SCHEMA=1 cargo test'.", "CONTRIBUTING.md"),
    (6, "Install git validation hooks", "Install pre-commit checks with 'uv run --only-dev --locked prek install'.", "CONTRIBUTING.md"),
    (7, "Inspect snapshot tests", "Understand snapshot testing and review snapshots with 'cargo insta review'.", "CONTRIBUTING.md"),
    (8, "Explore crate architecture", "Review the separation between ruff_linter, ruff_formatter, and ruff_python_parser.", "authored/glossary.md"),
    (9, "Review code ownership", "Identify module code owners using CODEOWNERS and understand who to ask.", "authored/who_to_ask.md"),
    (10, "Select a good first issue", "Locate an unassigned issue with newcomer labels that has no active open PR.", "CONTRIBUTING.md"),
    (11, "Run pre-PR validation checks", "Verify clippy ('CARGO_BUILD_WARNINGS=deny'), tests, and formatting pass cleanly.", "CONTRIBUTING.md"),
    (12, "Open a Pull Request", "Submit a PR adhering to .github/PULL_REQUEST_TEMPLATE.md and tag the proper rule.", ".github/PULL_REQUEST_TEMPLATE.md"),
]

USERS_FIXTURE = [
    ("user_ravi", "Ravi Patel", "Junior Contributor", "2026-10-30"),
    ("user_elena", "Elena Rostova", "Backend Engineer", "2026-10-18"),
    ("user_marcus", "Marcus Chen", "Systems Programmer", "2026-10-01"),
]

# Progress mapping for sample users at 3 distinct stages:
# Ravi: just started (2 done, 1 in_progress, 9 todo) -> 2 of 12
# Elena: mid-way (6 done, 1 in_progress, 5 todo) -> 6 of 12
# Marcus: nearly done (11 done, 1 in_progress) -> 11 of 12
PROGRESS_FIXTURE = {
    "user_ravi": {1: "done", 2: "done", 3: "in_progress", 4: "todo", 5: "todo", 6: "todo", 7: "todo", 8: "todo", 9: "todo", 10: "todo", 11: "todo", 12: "todo"},
    "user_elena": {1: "done", 2: "done", 3: "done", 4: "done", 5: "done", 6: "done", 7: "in_progress", 8: "todo", 9: "todo", 10: "todo", 11: "todo", 12: "todo"},
    "user_marcus": {1: "done", 2: "done", 3: "done", 4: "done", 5: "done", 6: "done", 7: "done", 8: "done", 9: "done", 10: "done", 11: "done", 12: "in_progress"},
}

QUESTION_LOG_FIXTURE = [
    ("user_ravi", "How do I install the prerequisites to build Ruff?", "handbook", 1, "2026-10-30T10:14:00Z"),
    ("user_ravi", "What command runs the local ruff binary against a test file?", "handbook", 1, "2026-10-30T14:32:00Z"),
    ("user_ravi", "Does Ruff have a Discord channel or Slack workspace?", "none", 0, "2026-10-30T16:20:00Z"),
    ("user_elena", "How do I review and accept changed insta snapshots?", "handbook", 1, "2026-10-21T09:40:00Z"),
    ("user_elena", "Where is the parser code located and who owns it?", "live", 1, "2026-10-22T11:15:00Z"),
    ("user_elena", "What is the policy on adding third-party crate dependencies?", "none", 0, "2026-10-24T15:00:00Z"),
    ("user_elena", "What clippy flags are required before submitting a PR?", "handbook", 1, "2026-10-26T13:45:00Z"),
    ("user_marcus", "Are there good first issues available without open PRs right now?", "live", 1, "2026-10-15T08:30:00Z"),
    ("user_marcus", "How does Ruff benchmark performance against CPython?", "handbook", 1, "2026-10-25T17:10:00Z"),
    ("user_marcus", "What are the criteria for merging an unsafe auto-fix?", "none", 0, "2026-10-28T12:05:00Z"),
]


def seed_database(db_path: Path | str | None = None) -> int:
    print("--- [Onboarding assistant] Database Seeding ---")
    init_db(db_path)
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    with get_db_connection(db_path) as conn:
        # 1. Clear existing fixtures for idempotency
        conn.execute("DELETE FROM user_progress;")
        conn.execute("DELETE FROM tasks;")
        conn.execute("DELETE FROM question_log;")
        conn.execute("DELETE FROM users;")

        # 2. Seed Tasks
        for ordinal, title, description, handbook_ref in TASKS_FIXTURE:
            conn.execute(
                """
                INSERT INTO tasks (ordinal, title, description, handbook_ref)
                VALUES (?, ?, ?, ?)
                """,
                (ordinal, title, description, handbook_ref),
            )
        print(f"Seeded {len(TASKS_FIXTURE)} onboarding tasks.")

        # 3. Seed Users
        for user_id, display_name, role, start_date in USERS_FIXTURE:
            conn.execute(
                """
                INSERT INTO users (id, display_name, role, start_date)
                VALUES (?, ?, ?, ?)
                """,
                (user_id, display_name, role, start_date),
            )
        print(f"Seeded {len(USERS_FIXTURE)} sample users.")

        # 4. Seed User Progress
        for user_id, task_statuses in PROGRESS_FIXTURE.items():
            for task_id, status in task_statuses.items():
                conn.execute(
                    """
                    INSERT INTO user_progress (user_id, task_id, status, updated_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (user_id, task_id, status, now_iso),
                )
        print("Seeded user progress checkpoints.")

        # 5. Seed Historical Question Log
        for user_id, question, answered_from, resolved, created_at in QUESTION_LOG_FIXTURE:
            conn.execute(
                """
                INSERT INTO question_log (user_id, question, answered_from, resolved, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (user_id, question, answered_from, resolved, created_at),
            )
        print(f"Seeded {len(QUESTION_LOG_FIXTURE)} historical question log entries.")

        conn.commit()

    print("SUCCESS: Database seeding complete.")
    return 0


if __name__ == "__main__":
    sys.exit(seed_database())

