"""Unit tests for MCP server live tools using respx to mock GitHub REST API."""

import base64
import pytest
import respx
import httpx
from config import config
from mcp_server.tools.live_repo_tools import get_repo_overview, get_directory_listing
from mcp_server.tools.live_issue_tools import list_good_first_issues, get_recent_prs
from mcp_server.tools.live_owner_tools import find_code_owners
from mcp_server.github_client import github_client


@pytest.fixture(autouse=True)
def clear_client_cache():
    """Clear github_client in-memory cache between test runs."""
    github_client._cache.clear()


@respx.mock
def test_get_repo_overview():
    """Test get_repo_overview correctly parses metadata, languages, and README."""
    target = config.target_repo

    # Mock repos/{target}
    respx.get(f"https://api.github.com/repos/{target}").respond(
        status_code=200,
        json={
            "description": "An extremely fast Python linter and code formatter.",
            "topics": ["python", "linter", "formatter"],
            "default_branch": "main",
            "license": {"name": "MIT License"},
        },
    )

    # Mock languages
    respx.get(f"https://api.github.com/repos/{target}/languages").respond(
        status_code=200,
        json={"Rust": 950000, "Python": 50000},
    )

    # Mock contents
    respx.get(f"https://api.github.com/repos/{target}/contents").respond(
        status_code=200,
        json=[
            {"name": "CONTRIBUTING.md", "type": "file"},
            {"name": "README.md", "type": "file"},
            {"name": "SECURITY.md", "type": "file"},
            {"name": ".github", "type": "dir"},
        ],
    )

    # Mock readme
    b64_readme = base64.b64encode(b"# Ruff\nFast Python linter.").decode("utf-8")
    respx.get(f"https://api.github.com/repos/{target}/readme").respond(
        status_code=200,
        json={"content": b64_readme, "encoding": "base64"},
    )

    overview = get_repo_overview()
    assert overview.error is None
    assert overview.description == "An extremely fast Python linter and code formatter."
    assert "Rust" in overview.primary_languages
    assert overview.has_contributing is True
    assert overview.has_security is True
    assert overview.readme_excerpt is not None
    assert "Fast Python linter" in overview.readme_excerpt
    assert len(overview.source_refs) >= 1
    assert overview.source_refs[0].kind == "live"


@respx.mock
def test_get_directory_listing_allowed_and_denied():
    """Test directory listing returns metadata only and blocks denied paths."""
    target = config.target_repo

    # Test denied path
    blocked_res = get_directory_listing(".env")
    assert blocked_res.error is not None
    assert blocked_res.error.code == "path_blocked"

    # Test allowed directory
    respx.get(f"https://api.github.com/repos/{target}/contents/crates").respond(
        status_code=200,
        json=[
            {"name": "ruff", "type": "dir", "size": 0},
            {"name": "ruff_python_parser", "type": "dir", "size": 0},
            {"name": "Cargo.toml", "type": "file", "size": 2048},
        ],
    )

    res = get_directory_listing("crates")
    assert res.error is None
    assert len(res.entries) == 3
    assert res.entries[0].name == "ruff"
    assert res.entries[0].type == "dir"
    assert res.entries[2].size == 2048
    # Proves no file contents are returned
    assert not hasattr(res.entries[2], "content")


@respx.mock
def test_list_good_first_issues_and_pr_exclusion():
    """Test good-first issues filtering, excluding issues with active pull requests and dropping PRs."""
    target = config.target_repo

    # 1. Mock pulls to simulate an open PR referencing issue #42
    respx.get(f"https://api.github.com/repos/{target}/pulls").respond(
        status_code=200,
        json=[
            {
                "number": 100,
                "title": "Fixes #42 - parsing error",
                "body": "Resolves issue #42 with updated AST check",
            }
        ],
    )

    # 2. Mock issues query
    respx.get(f"https://api.github.com/repos/{target}/issues").respond(
        status_code=200,
        json=[
            {
                "number": 42,
                "title": "Bug in type annotation parser",
                "labels": [{"name": "good first issue"}],
                "assignees": [],
                "comments": 2,
                "html_url": f"https://github.com/{target}/issues/42",
            },
            {
                # Issue #55 has no open PR and is unassigned
                "number": 55,
                "title": "Docs: Clarify config options",
                "labels": [{"name": "good first issue"}],
                "assignees": [],
                "comments": 0,
                "html_url": f"https://github.com/{target}/issues/55",
            },
            {
                # Item with pull_request key must be dropped (GitHub API pitfall)
                "number": 99,
                "title": "A PR that sneaked into issues endpoint",
                "pull_request": {"url": "https://..."},
                "labels": [{"name": "good first issue"}],
                "assignees": [],
            },
        ],
    )

    result = list_good_first_issues(limit=5, exclude_with_open_pr=True)
    assert result.error is None
    # Issue #42 must be excluded because PR #100 references it
    # Issue #99 must be dropped because it is a PR
    # Only #55 should remain
    issue_numbers = [iss.number for iss in result.issues]
    assert 55 in issue_numbers
    assert 42 not in issue_numbers
    assert 99 not in issue_numbers


@respx.mock
def test_find_code_owners_codeowners_file():
    """Test CODEOWNERS parsing with gitignore style and last-matching-rule semantics."""
    target = config.target_repo

    codeowners_content = """
    # Fallback owner
    * @core-team

    # Specific crate owner (last matching rule wins)
    crates/ruff_python_parser/ @parser-team
    """
    b64_codeowners = base64.b64encode(codeowners_content.encode("utf-8")).decode("utf-8")

    respx.get(f"https://api.github.com/repos/{target}/contents/.github/CODEOWNERS").respond(
        status_code=200,
        json={"content": b64_codeowners},
    )

    # Query path matching specific rule
    res = find_code_owners("crates/ruff_python_parser/src/main.rs")
    assert res.error is None
    assert res.method == "codeowners"
    assert "@parser-team" in res.owners
    assert res.rule == "crates/ruff_python_parser/"

    # Query general path matching wildcard rule
    res_root = find_code_owners("README.md")
    assert res_root.error is None
    assert res_root.method == "codeowners"
    assert "@core-team" in res_root.owners


@respx.mock
def test_find_code_owners_inferred_fallback():
    """Test fallback to inferred ownership from 90-day commits when CODEOWNERS is absent."""
    target = config.target_repo

    # 404 on CODEOWNERS files
    for path in [".github/CODEOWNERS", "CODEOWNERS", "docs/CODEOWNERS"]:
        respx.get(f"https://api.github.com/repos/{target}/contents/{path}").respond(status_code=404)

    # Mock commits API
    respx.get(f"https://api.github.com/repos/{target}/commits").respond(
        status_code=200,
        json=[
            {"author": {"login": "alice"}},
            {"author": {"login": "alice"}},
            {"author": {"login": "bob"}},
            {"author": {"login": "dependabot[bot]"}},  # bot must be ignored
            {"author": {"login": "charlie"}},
        ],
    )

    res = find_code_owners("crates/ruff")
    assert res.error is None
    assert res.method == "inferred"
    assert "alice" in res.owners
    assert "bob" in res.owners
    assert "charlie" in res.owners
    assert "dependabot[bot]" not in res.owners
    assert "heuristic" in res.note.lower()


@respx.mock
def test_get_recent_prs():
    """Test recent PRs endpoint returns metadata only."""
    target = config.target_repo

    respx.get(f"https://api.github.com/repos/{target}/pulls").respond(
        status_code=200,
        json=[
            {
                "number": 101,
                "title": "feat: add rule SIM101",
                "user": {"login": "contributor_one"},
                "labels": [{"name": "enhancement"}],
                "state": "open",
                "created_at": "2026-10-30T10:00:00Z",
                "html_url": f"https://github.com/{target}/pull/101",
            }
        ],
    )

    result = get_recent_prs(state="open", limit=5)
    assert result.error is None
    assert len(result.prs) == 1
    assert result.prs[0].number == 101
    assert result.prs[0].author == "contributor_one"
    assert result.prs[0].state == "open"

