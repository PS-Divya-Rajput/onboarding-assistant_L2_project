"""Interactive Build Error & Compiler Diagnostic tool for Onboarding assistant.

Parses build, compiler, linker, and test failure logs, cross-referencing repository handbook
documentation and known resolved issues to suggest immediate actionable remedies.
"""

from __future__ import annotations

import re
from typing import List

from mcp_server.privacy import audit_tool_call, redact_string
from mcp_server.schemas import BuildErrorDiagnosticResult, SourceRef
from mcp_server.tools.live_owner_tools import find_code_owners
from mcp_server.tools.local_handbook_tools import search_onboarding_docs

# Common build error signature regexes
ERROR_SIGNATURES = [
    ("rust_borrow_checker", re.compile(r"error\[E(0382|0502|0499|0597|0506)\]", re.IGNORECASE)),
    ("rust_missing_crate", re.compile(r"error\[E0432\]|unresolved import `([^`]+)`", re.IGNORECASE)),
    ("rust_type_mismatch", re.compile(r"error\[E0308\]|mismatched types", re.IGNORECASE)),
    ("linker_missing_lib", re.compile(r"cannot find -l|lld-link: error|LINK : fatal error", re.IGNORECASE)),
    ("python_import_error", re.compile(r"ModuleNotFoundError: No module named ['\"]([^'\"]+)['\"]", re.IGNORECASE)),
    ("cargo_target_missing", re.compile(r"target `([^`]+)` not found|can't find `([^`]+)` in", re.IGNORECASE)),
    ("test_assertion_failure", re.compile(r"assertion `left == right` failed|FAILED tests/", re.IGNORECASE)),
]


def diagnose_build_error(error_log: str) -> BuildErrorDiagnosticResult:
    """Analyze compiler or test error logs and generate remediation guidance."""
    clean_log, _ = redact_string(error_log or "")
    first_lines = "\n".join(clean_log.splitlines()[:10])

    detected_type = "general_build_failure"
    summary = "Build or runtime error detected."
    root_cause = "General build toolchain discrepancy or test failure."
    suggested_fixes: List[str] = []
    relevant_docs: List[str] = []
    who_to_ask: List[str] = []

    # Detect signatures
    for err_type, pattern in ERROR_SIGNATURES:
        match = pattern.search(clean_log)
        if match:
            detected_type = err_type
            if err_type == "rust_borrow_checker":
                summary = "Rust Borrow Checker / Ownership Violation"
                root_cause = "A value was moved or borrowed simultaneously as mutable and immutable."
                suggested_fixes = [
                    "Check if cloning (.clone()) or referencing (&T) satisfies the lifetime requirement.",
                    "Review Rust ownership semantics in docs/contributing.md.",
                    "Run 'cargo check --workspace' to see detailed rustc explain notes for error codes.",
                ]
            elif err_type == "rust_missing_crate":
                imported = match.group(1) if match.groups() else "module"
                summary = f"Unresolved Import / Missing Crate: `{imported}`"
                root_cause = f"The crate dependency `{imported}` is not defined in Cargo.toml or not within the workspace."
                suggested_fixes = [
                    "Verify the crate is declared under [dependencies] in the relevant crate's Cargo.toml.",
                    "Run 'cargo check --all-targets' after updating Cargo.lock.",
                ]
            elif err_type == "linker_missing_lib":
                summary = "Native Linker / System Library Failure"
                root_cause = "A required C/C++ or system dynamic library is missing from the local OS."
                suggested_fixes = [
                    "Windows: Ensure Microsoft Visual C++ Build Tools or Windows SDK is installed.",
                    "Linux: Install build-essential / pkg-config / libssl-dev.",
                    "macOS: Run 'xcode-select --install'.",
                ]
            elif err_type == "python_import_error":
                mod = match.group(1) if match.groups() else "package"
                summary = f"Python Dependency Missing: `{mod}`"
                root_cause = f"The package `{mod}` is not installed in the active virtual environment."
                suggested_fixes = [
                    f"Ensure virtualenv is activated and run: pip install -e . or pip install {mod}.",
                    "Run 'python scripts/check_env.py' to verify project dependencies.",
                ]
            elif err_type == "test_assertion_failure":
                summary = "Test Suite Assertion Mismatch"
                root_cause = "Code modifications caused unit or integration test assertions to fail."
                suggested_fixes = [
                    "Run the single failing test in isolation with debug output: cargo test <test_name> -- --nocapture",
                    "Update test snapshots or fixtures if intentional API changes were made: cargo insta review / cargo test -p ruff_linter",
                ]
            break

    # Search docs for matching keywords
    search_query = f"{detected_type.replace('_', ' ')} setup build"
    docs_res = search_onboarding_docs(query=search_query, top_k=2)
    for m in docs_res.matches:
        relevant_docs.append(f"{m.file} > {m.heading_path}")

    # Identify owners for core crates
    owners_res = find_code_owners(path="crates")
    who_to_ask = list(owners_res.owners)

    res = BuildErrorDiagnosticResult(
        error_type=detected_type,
        summary=summary,
        root_cause=root_cause,
        suggested_fixes=suggested_fixes or ["Inspect compiler output above and run cargo check."],
        relevant_docs=relevant_docs,
        who_to_ask=who_to_ask,
        source_refs=[
            SourceRef(
                id="DIAG-LOG",
                kind="local",
                label=f"Diagnostic: {summary}",
                url=None,
            )
        ],
    )

    audit_tool_call(
        tool_name="diagnose_build_error",
        args={"error_type": detected_type},
        status="success",
        payload_obj=res,
        redaction_count=0,
    )
    return res

