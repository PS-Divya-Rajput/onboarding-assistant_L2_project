"""Unit tests for Phase 3: Handbook parsing, RAG vector search, progress tracking, and write-tool dry_run enforcement."""

import sqlite3
from pathlib import Path
import pytest
from scripts.ingest_handbook import chunk_markdown_file, parse_front_matter
from mcp_server.tools.local_handbook_tools import search_onboarding_docs
from mcp_server.tools.local_progress_tools import (
    get_onboarding_progress,
    log_question,
    mark_task_done,
)
from mcp_server.server import resource_read_handbook_doc
from mcp_server.db import init_db
from scripts.seed_db import seed_database


def test_front_matter_validation_and_rejection(tmp_path: Path):
    """Test that markdown files lacking front matter fail loudly with ValueError."""
    bad_file = tmp_path / "bad_doc.md"
    bad_file.write_text("# Title without front matter\nSome content.", encoding="utf-8")

    with pytest.raises(ValueError, match="Missing front matter"):
        parse_front_matter(bad_file.read_text(encoding="utf-8"), bad_file)


def test_markdown_hierarchical_chunking(tmp_path: Path):
    """Test markdown chunking generates proper hierarchical heading paths."""
    sample_md = (
        "---\n"
        "source_url: https://github.com/example/repo/doc.md\n"
        "origin: repo_docs\n"
        "---\n\n"
        "# Getting Started\n"
        "Introduction text that is long enough to meet minimum characters requirement for testing.\n\n"
        "## Installation\n"
        "Detailed step-by-step instructions on setting up the developer environment and installing prerequisites.\n\n"
        "### Prerequisites\n"
        "Rust and uv are required. Run cargo build to verify your local configuration."
    )
    doc_path = tmp_path / "doc.md"
    doc_path.write_text(sample_md, encoding="utf-8")

    chunks = chunk_markdown_file(doc_path, "doc.md")
    assert len(chunks) >= 1

    # Check heading path hierarchy
    heading_paths = [c["heading_path"] for c in chunks]
    assert any("Getting Started" in hp for hp in heading_paths)
    assert any("Installation" in hp or "Prerequisites" in hp for hp in heading_paths)


def test_search_onboarding_docs_semantic_match():
    """Test RAG search retrieves relevant chunks from real ingested handbook."""
    res = search_onboarding_docs("How do I run tests in Ruff?")
    assert res.error is None
    assert len(res.matches) > 0
    assert res.coverage in ("high", "low")

    # Best match should discuss testing or nextest or cargo test
    top_text = (res.matches[0].text + " " + res.matches[0].heading_path).lower()
    assert any(term in top_text for term in ["test", "cargo", "nextest", "suite"])
    assert res.matches[0].similarity >= 0.30
    assert len(res.source_refs) >= 1
    assert res.source_refs[0].kind == "local"


def test_search_onboarding_docs_unanswerable_query():
    """Test that queries unrelated to the repo return coverage: 'none' and empty matches."""
    res = search_onboarding_docs("How do I make chocolate chip cookies with almond flour?")
    # Must drop weak matches below threshold and report coverage: none
    assert res.coverage == "none"
    assert len(res.matches) == 0


def test_get_onboarding_progress_seeded_users():
    """Test checklist retrieval for seeded sample users at different stages."""
    # Ravi: just started (2 done, next suggested is task 3)
    ravi_progress = get_onboarding_progress("user_ravi")
    assert ravi_progress.error is None
    assert ravi_progress.done_count == 2
    assert ravi_progress.total_count == 12
    assert ravi_progress.next_suggested_task is not None
    assert ravi_progress.next_suggested_task.id == 3

    # Marcus: nearly done (11 done, next suggested is task 12)
    marcus_progress = get_onboarding_progress("user_marcus")
    assert marcus_progress.done_count == 11
    assert marcus_progress.next_suggested_task.id == 12


def test_write_tools_dry_run_safety(tmp_path: Path):
    """Test that write tools default to dry_run=True, returning proposals without modifying DB."""
    test_db = tmp_path / "test_write.db"
    seed_database(test_db)

    # 1. Test mark_task_done with dry_run=True (default)
    dry_res = mark_task_done("user_ravi", task_id=3, dry_run=True, db_path=test_db)
    assert dry_res.dry_run is True
    assert dry_res.preview is not None
    assert "Mark step 3" in dry_res.preview.description

    # Verify task 3 in DB is NOT changed to done
    progress = get_onboarding_progress("user_ravi", db_path=test_db)
    task3 = next(t for t in progress.tasks if t.id == 3)
    assert task3.status == "in_progress"  # still in_progress, NOT done!

    # 2. Test mark_task_done with dry_run=False (Apply clicked)
    applied_res = mark_task_done("user_ravi", task_id=3, dry_run=False, db_path=test_db)
    assert applied_res.dry_run is False
    assert applied_res.success is True

    # Verify task 3 in DB IS now done
    progress_after = get_onboarding_progress("user_ravi", db_path=test_db)
    task3_after = next(t for t in progress_after.tasks if t.id == 3)
    assert task3_after.status == "done"
    assert progress_after.done_count == 3


def test_log_question_dry_run_safety(tmp_path: Path):
    """Test log_question dry_run safety vs applied persistence."""
    test_db = tmp_path / "test_qlog.db"
    seed_database(test_db)

    # 1. Dry run
    dry_res = log_question(
        user_id="user_elena",
        question="Where is AST visitor implemented?",
        answered_from="handbook",
        resolved=True,
        dry_run=True,
        db_path=test_db,
    )
    assert dry_res.dry_run is True
    assert dry_res.preview is not None
    assert dry_res.question_id is None

    # 2. Applied
    applied_res = log_question(
        user_id="user_elena",
        question="Where is AST visitor implemented?",
        answered_from="handbook",
        resolved=True,
        dry_run=False,
        db_path=test_db,
    )
    assert applied_res.dry_run is False
    assert applied_res.question_id is not None
    assert applied_res.question_id > 10


def test_resource_read_handbook_doc():
    """Test MCP resource reading for handbook documents."""
    # Allowed resource
    content = resource_read_handbook_doc("README.md")
    assert "Ruff" in content
    assert len(content) > 100

    # Denied or non-existent path
    denied = resource_read_handbook_doc(".env")
    assert "Access Denied" in denied

    missing = resource_read_handbook_doc("non_existent_doc.md")
    assert "Not Found" in missing

