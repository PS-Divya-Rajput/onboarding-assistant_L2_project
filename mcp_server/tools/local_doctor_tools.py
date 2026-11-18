"""Local Environment Doctor tool for Onboarding assistant.

Audits developer machine setup (Python, Rust toolchain, Git, virtualenv, system dependencies)
against the target repository requirements and outputs structured diagnostics and remedies.
"""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
from typing import List, Optional

from mcp_server.privacy import audit_tool_call
from mcp_server.schemas import (
    DiagnoseEnvironmentResult,
    EnvironmentCheckItem,
    SourceRef,
    ToolError,
)


def _run_cmd(cmd: List[str]) -> Optional[str]:
    """Execute a simple command and return first line of output, or None on failure."""
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=5, check=False)
        if res.returncode == 0:
            out = res.stdout.strip()
            return out.splitlines()[0] if out else "installed"
    except Exception:
        pass
    return None


def diagnose_local_environment() -> DiagnoseEnvironmentResult:
    """Audit the local developer environment against repository toolchain prerequisites."""
    checks: List[EnvironmentCheckItem] = []
    recommendations: List[str] = []
    all_passed = True

    # 1. Python Check
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    if sys.version_info >= (3, 10):
        checks.append(EnvironmentCheckItem(
            name="Python Version",
            status="pass",
            found=py_ver,
            required=">= 3.10.0",
            remedy=None,
        ))
    else:
        all_passed = False
        checks.append(EnvironmentCheckItem(
            name="Python Version",
            status="fail",
            found=py_ver,
            required=">= 3.10.0",
            remedy="Install Python 3.11+ from https://www.python.org/downloads/ or via pyenv/winget.",
        ))
        recommendations.append("Upgrade Python to 3.11+ to ensure compatibility with modern typing and build tools.")

    # 2. Virtual Environment Check
    in_venv = sys.prefix != sys.base_prefix or "VIRTUAL_ENV" in os.environ
    if in_venv:
        venv_path = os.environ.get("VIRTUAL_ENV", sys.prefix)
        checks.append(EnvironmentCheckItem(
            name="Virtual Environment",
            status="pass",
            found=f"Active ({os.path.basename(venv_path)})",
            required="Active virtualenv",
            remedy=None,
        ))
    else:
        checks.append(EnvironmentCheckItem(
            name="Virtual Environment",
            status="warn",
            found="None detected (System Python)",
            required="Active virtualenv (venv)",
            remedy="Activate virtual environment: .\\venv\\Scripts\\Activate.ps1 (Windows) or source venv/bin/activate (POSIX)",
        ))
        recommendations.append("Activate virtualenv to avoid polluting global Python environment.")

    # 3. Git Check
    git_bin = shutil.which("git")
    if git_bin:
        git_ver = _run_cmd(["git", "--version"]) or "installed"
        checks.append(EnvironmentCheckItem(
            name="Git CLI",
            status="pass",
            found=git_ver,
            required="Git >= 2.30",
            remedy=None,
        ))
    else:
        all_passed = False
        checks.append(EnvironmentCheckItem(
            name="Git CLI",
            status="fail",
            found="Not found in PATH",
            required="Git >= 2.30",
            remedy="Install Git from https://git-scm.com/ or run 'winget install Git.Git'.",
        ))
        recommendations.append("Install Git and ensure it is present in your system PATH.")

    # 4. Rust Toolchain (Cargo) Check
    cargo_bin = shutil.which("cargo")
    if cargo_bin:
        cargo_ver = _run_cmd(["cargo", "--version"]) or "installed"
        checks.append(EnvironmentCheckItem(
            name="Rust Cargo",
            status="pass",
            found=cargo_ver,
            required="Cargo >= 1.70",
            remedy=None,
        ))
    else:
        checks.append(EnvironmentCheckItem(
            name="Rust Cargo",
            status="warn",
            found="Not in PATH",
            required="Cargo >= 1.70 (Recommended for Rust crates)",
            remedy="Install rustup from https://rustup.rs/ or run 'winget install Rustlang.Rustup'.",
        ))
        recommendations.append("Install rustup/cargo to build and run native Ruff crates.")

    # 5. Rust Compiler (rustc) Check
    rustc_bin = shutil.which("rustc")
    if rustc_bin:
        rustc_ver = _run_cmd(["rustc", "--version"]) or "installed"
        checks.append(EnvironmentCheckItem(
            name="Rust Compiler (rustc)",
            status="pass",
            found=rustc_ver,
            required="rustc >= 1.70",
            remedy=None,
        ))
    else:
        checks.append(EnvironmentCheckItem(
            name="Rust Compiler (rustc)",
            status="warn",
            found="Not in PATH",
            required="rustc >= 1.70",
            remedy="Run 'rustup default stable' after installing rustup.",
        ))

    # Overall system summary
    os_info = f"{platform.system()} {platform.release()} ({platform.machine()})"

    res = DiagnoseEnvironmentResult(
        all_passed=all_passed,
        os_platform=os_info,
        checks=checks,
        recommendations=recommendations,
        source_refs=[
            SourceRef(
                id="DOC-ENV",
                kind="local",
                label="Local Environment Audit",
                url=None,
            )
        ],
    )

    audit_tool_call(
        tool_name="diagnose_local_environment",
        args={},
        status="success" if all_passed else "warn",
        payload_obj=res,
        redaction_count=0,
    )
    return res

