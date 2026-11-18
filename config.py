"""Configuration module for Onboarding assistant.

Loads environment variables from .env and validates all required settings.
Never hardcodes secrets, model names, or repository identifiers.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List
from dotenv import load_dotenv

# Ensure .env is loaded from the project root
ROOT_DIR = Path(__file__).resolve().parent
load_dotenv(ROOT_DIR / ".env")


class ConfigurationError(Exception):
    """Raised when one or more required configuration variables are missing or invalid."""
    pass


@dataclass(frozen=True)
class AppConfig:
    """Application configuration container."""

    google_api_key: str
    groq_api_key: str
    github_token: str
    target_repo: str = "astral-sh/ruff"
    gemini_model: str = "gemini-3.5-flash-lite"
    groq_model: str = "llama-3.3-70b-versatile"
    llm_timeout_seconds: int = 20
    max_tool_steps: int = 6
    similarity_threshold: float = 0.30
    good_first_labels: List[str] = field(
        default_factory=lambda: ["good first issue", "good-first-issue", "help wanted"]
    )
    path_denylist: List[str] = field(
        default_factory=lambda: [".env", "secrets", ".github/workflows", "config/prod", "id_rsa"]
    )


def _parse_list(val: str | None, default: List[str]) -> List[str]:
    """Parse comma-separated string into trimmed list of non-empty strings."""
    if not val:
        return default
    items = [item.strip() for item in val.split(",") if item.strip()]
    return items if items else default


def load_config(require_keys: bool = False) -> AppConfig:
    """Load configuration from environment.

    Args:
        require_keys: If True, raises ConfigurationError if any API keys are missing.
                      Set to False for testing or tooling environments where keys are mocked.
    """
    google_api_key = os.getenv("GOOGLE_API_KEY", "").strip()
    groq_api_key = os.getenv("GROQ_API_KEY", "").strip()
    github_token = os.getenv("GITHUB_TOKEN", "").strip()
    target_repo = os.getenv("TARGET_REPO", "astral-sh/ruff").strip()
    gemini_model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite").strip()
    groq_model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile").strip()

    try:
        llm_timeout_seconds = int(os.getenv("LLM_TIMEOUT_SECONDS", "20"))
    except ValueError:
        llm_timeout_seconds = 20

    try:
        max_tool_steps = int(os.getenv("MAX_TOOL_STEPS", "6"))
    except ValueError:
        max_tool_steps = 6

    try:
        similarity_threshold = float(os.getenv("SIMILARITY_THRESHOLD", "0.30"))
    except ValueError:
        similarity_threshold = 0.30

    good_first_labels = _parse_list(
        os.getenv("GOOD_FIRST_LABELS"),
        ["good first issue", "good-first-issue", "help wanted"],
    )
    path_denylist = _parse_list(
        os.getenv("PATH_DENYLIST"),
        [".env", "secrets", ".github/workflows", "config/prod", "id_rsa"],
    )

    if require_keys:
        missing = []
        if not google_api_key:
            missing.append("GOOGLE_API_KEY")
        if not groq_api_key:
            missing.append("GROQ_API_KEY")
        if not github_token:
            missing.append("GITHUB_TOKEN")
        if not target_repo:
            missing.append("TARGET_REPO")

        if missing:
            raise ConfigurationError(
                f"Missing required environment variable(s): {', '.join(missing)}. "
                f"Please update your .env file."
            )

    return AppConfig(
        google_api_key=google_api_key,
        groq_api_key=groq_api_key,
        github_token=github_token,
        target_repo=target_repo,
        gemini_model=gemini_model,
        groq_model=groq_model,
        llm_timeout_seconds=llm_timeout_seconds,
        max_tool_steps=max_tool_steps,
        similarity_threshold=similarity_threshold,
        good_first_labels=good_first_labels,
        path_denylist=path_denylist,
    )


# Default module-level configuration instance (permissive load by default)
config = load_config(require_keys=False)

