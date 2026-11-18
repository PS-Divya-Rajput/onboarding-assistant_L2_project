"""Script to check environment keys and verify GitHub token access and rate limit.

Usage (PowerShell):
    .\\venv\\Scripts\\python.exe scripts\\check_env.py

Usage (bash):
    ./venv/bin/python scripts/check_env.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx
from config import load_config, ConfigurationError


def main() -> int:
    print("--- [Onboarding assistant] Environment Verification ---")
    try:
        cfg = load_config(require_keys=True)
    except ConfigurationError as e:
        print(f"FAILED: {e}")
        return 1

    print(f"Target Repo:  {cfg.target_repo}")
    print(f"Gemini Model: {cfg.gemini_model}")
    print(f"Groq Model:   {cfg.groq_model}")

    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "Authorization": f"Bearer {cfg.github_token}",
        "User-Agent": "Onboarding-Assistant-CheckEnv",
    }

    try:
        with httpx.Client(timeout=10.0) as client:
            # 1. Check rate limit
            rl_resp = client.get("https://api.github.com/rate_limit", headers=headers)
            if rl_resp.status_code != 200:
                print(f"FAILED: GitHub /rate_limit returned HTTP {rl_resp.status_code}: {rl_resp.text}")
                return 1
            rl_data = rl_resp.json()
            core_limit = rl_data.get("resources", {}).get("core", {})
            limit = core_limit.get("limit")
            remaining = core_limit.get("remaining")
            reset_ts = core_limit.get("reset")
            print(f"GitHub Core Rate Limit: {remaining}/{limit} (resets at UNIX {reset_ts})")

            # 2. Check TARGET_REPO
            repo_resp = client.get(f"https://api.github.com/repos/{cfg.target_repo}", headers=headers)
            if repo_resp.status_code != 200:
                print(f"FAILED: GitHub /repos/{cfg.target_repo} returned HTTP {repo_resp.status_code}: {repo_resp.text}")
                return 1
            repo_data = repo_resp.json()
            full_name = repo_data.get("full_name")
            stars = repo_data.get("stargazers_count")
            desc = repo_data.get("description", "")
            print(f"Target Repo verified: {full_name} ({stars} stars) - {desc}")

    except Exception as exc:
        print(f"FAILED: Network or verification error: {type(exc).__name__}: {exc}")
        return 1

    print("SUCCESS: All environment variables, API keys, and GitHub access verified.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

