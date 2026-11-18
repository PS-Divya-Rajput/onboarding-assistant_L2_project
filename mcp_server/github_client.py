"""GitHub REST API client with in-memory TTL caching, rate-limit awareness, and robust error handling.

Complies with GitHub API v2022-11-28 specification.
"""

from __future__ import annotations

import time
from typing import Any, Dict, Optional, Tuple
import httpx
from config import config

GITHUB_API_BASE = "https://api.github.com"
CACHE_TTL_SECONDS = 300  # 5 minutes


class GitHubClient:
    """HTTP client for GitHub REST API with caching and rate limit tracking."""

    def __init__(self, token: Optional[str] = None, timeout: float = 10.0):
        self.token = token or config.github_token
        self.timeout = timeout
        self._cache: Dict[str, Tuple[float, int, Any, Dict[str, str]]] = {}

    def _build_headers(self) -> Dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "Onboarding-Assistant-MCP/0.1.0",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _cache_key(self, endpoint: str, params: Optional[Dict[str, Any]]) -> str:
        param_str = ""
        if params:
            param_str = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
        return f"{endpoint}?{param_str}"

    def get(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None, use_cache: bool = True
    ) -> Tuple[int, Any, Dict[str, str]]:
        """Perform a GET request to GitHub API.

        Returns:
            Tuple of (status_code, json_or_text_data, headers_dict)
        """
        cache_key = self._cache_key(endpoint, params)
        now = time.time()

        if use_cache and cache_key in self._cache:
            cached_time, status, data, headers = self._cache[cache_key]
            if now - cached_time < CACHE_TTL_SECONDS:
                return status, data, headers

        url = f"{GITHUB_API_BASE.rstrip('/')}/{endpoint.lstrip('/')}"
        req_headers = self._build_headers()

        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.get(url, headers=req_headers, params=params)
                status_code = resp.status_code
                resp_headers = dict(resp.headers)

                # Check rate limits from response headers
                remaining = resp_headers.get("x-ratelimit-remaining")
                reset_time = resp_headers.get("x-ratelimit-reset", "0")

                if (status_code == 403 and remaining == "0") or status_code == 429:
                    error_payload = {
                        "error": {
                            "code": "rate_limited",
                            "message": f"GitHub API rate limit exhausted. Resets at UNIX {reset_time}.",
                            "reset_time": reset_time,
                            "retryable": True,
                        }
                    }
                    return 429, error_payload, resp_headers

                try:
                    data = resp.json()
                except Exception:
                    data = resp.text

                if status_code < 400:
                    self._cache[cache_key] = (now, status_code, data, resp_headers)

                return status_code, data, resp_headers

        except httpx.TimeoutException as exc:
            return 408, {"error": {"code": "timeout", "message": f"GitHub API request timed out: {exc}", "retryable": True}}, {}
        except httpx.RequestError as exc:
            return 503, {"error": {"code": "network_error", "message": f"GitHub API network error: {exc}", "retryable": True}}, {}
        except Exception as exc:
            return 500, {"error": {"code": "internal_error", "message": f"Unexpected error: {type(exc).__name__}: {exc}", "retryable": False}}, {}


# Global default client
github_client = GitHubClient()

