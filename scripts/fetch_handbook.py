"""Fetch real documentation files from TARGET_REPO on GitHub and construct the onboarding handbook.

Pins each document to the current commit SHA and injects provenance front matter.
Exits non-zero if fewer than 5 documents are successfully retrieved.
"""

from __future__ import annotations

import base64
import datetime
import json
import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx
from config import config

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
HANDBOOK_DIR = DATA_DIR / "handbook"
SOURCES_JSON = DATA_DIR / "handbook_sources.json"
SOURCES_MD = HANDBOOK_DIR / "SOURCES.md"


def get_headers() -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "Onboarding-Assistant-HandbookFetcher/0.1.0",
    }
    if config.github_token:
        headers["Authorization"] = f"Bearer {config.github_token}"
    return headers


def fetch_handbook() -> int:
    print(f"--- Fetching Handbook Docs from {config.target_repo} ---")
    HANDBOOK_DIR.mkdir(parents=True, exist_ok=True)

    if not SOURCES_JSON.exists():
        print(f"ERROR: {SOURCES_JSON} not found!")
        return 1

    with open(SOURCES_JSON, "r", encoding="utf-8") as f:
        paths_to_fetch = json.load(f)

    headers = get_headers()
    client = httpx.Client(timeout=15.0, headers=headers)

    # 1. Fetch repo metadata (default branch, license, commit SHA)
    try:
        repo_resp = client.get(f"https://api.github.com/repos/{config.target_repo}")
        if repo_resp.status_code != 200:
            print(f"ERROR: Could not query repository metadata: {repo_resp.status_code} {repo_resp.text}")
            return 1
        repo_data = repo_resp.json()
        default_branch = repo_data.get("default_branch", "main")
        license_name = (repo_data.get("license") or {}).get("spdx_id") or "MIT"

        commit_resp = client.get(f"https://api.github.com/repos/{config.target_repo}/commits/{default_branch}")
        commit_sha = commit_resp.json().get("sha", default_branch) if commit_resp.status_code == 200 else default_branch
        print(f"Target: {config.target_repo} (branch: {default_branch}, sha: {commit_sha[:8]}, license: {license_name})")

        # Explore docs/ folder to inform developer of available docs
        docs_resp = client.get(f"https://api.github.com/repos/{config.target_repo}/contents/docs")
        if docs_resp.status_code == 200 and isinstance(docs_resp.json(), list):
            available_docs = [item.get("name") for item in docs_resp.json() if item.get("type") == "file"]
            print(f"Available files in docs/: {', '.join(available_docs[:10])}...")
    except Exception as exc:
        print(f"ERROR: Network failure communicating with GitHub API: {exc}")
        return 1

    today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    fetched_records = []

    for rel_path in paths_to_fetch:
        print(f"Fetching: {rel_path}...", end=" ")
        resp = client.get(f"https://api.github.com/repos/{config.target_repo}/contents/{rel_path}")
        if resp.status_code != 200:
            print(f"[SKIP] HTTP {resp.status_code}")
            continue

        item = resp.json()
        if not isinstance(item, dict) or item.get("type") != "file":
            print("[SKIP] Not a file")
            continue

        raw_b64 = item.get("content", "")
        try:
            content_text = base64.b64decode(raw_b64).decode("utf-8", errors="replace")
        except Exception as e:
            print(f"[ERROR] Decoding failed: {e}")
            continue

        # Strip existing leading front matter if present
        if content_text.startswith("---"):
            parts = content_text.split("---", 2)
            if len(parts) >= 3:
                content_text = parts[2].lstrip()

        permalink = f"https://github.com/{config.target_repo}/blob/{commit_sha}/{rel_path}"
        front_matter = (
            f"---\n"
            f"source_url: {permalink}\n"
            f"license: {license_name}\n"
            f"retrieved: {today}\n"
            f"origin: repo_docs\n"
            f"---\n\n"
        )
        full_content = front_matter + content_text

        out_path = HANDBOOK_DIR / rel_path
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as out_f:
            out_f.write(full_content)

        fetched_records.append({
            "path": rel_path,
            "url": permalink,
            "license": license_name,
            "date": today,
            "size": len(content_text),
        })
        print(f"[OK] ({len(content_text)} chars)")

    # Write SOURCES.md
    with open(SOURCES_MD, "w", encoding="utf-8") as f:
        f.write("# Handbook Sources and Provenance\n\n")
        f.write(f"Repository: `{config.target_repo}`  \n")
        f.write(f"Retrieved: {today}  \n")
        f.write(f"Commit SHA: `{commit_sha}`  \n\n")
        f.write("| Document | License | Retrieved | Source Permalink |\n")
        f.write("|---|---|---|---|\n")
        for rec in fetched_records:
            f.write(f"| `{rec['path']}` | {rec['license']} | {rec['date']} | [{rec['path']}]({rec['url']}) |\n")

    print(f"\nFetched {len(fetched_records)} documents into {HANDBOOK_DIR}")
    print(f"Provenance manifest written to {SOURCES_MD}")

    if len(fetched_records) < 5:
        print(f"FAILED: Expected at least 5 documents, fetched {len(fetched_records)}.")
        return 1

    print("SUCCESS: Handbook documents fetched successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(fetch_handbook())

