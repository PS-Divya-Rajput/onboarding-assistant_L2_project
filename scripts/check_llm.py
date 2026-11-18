"""Live smoke test script for Gemini primary and Groq fallback LLM providers.

Verifies model connectivity, trivial text generation, and forced tool-calling.

Usage (PowerShell):
    .\\venv\\Scripts\\python.exe scripts\\check_llm.py

Usage (bash):
    ./venv/bin/python scripts/check_llm.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import config
from agent.llm_provider import LLMMessage, LLMProvider

DUMMY_TOOL = {
    "name": "get_current_status",
    "description": "Fetch the current status indicator of the system.",
    "parameters": {
        "type": "object",
        "properties": {
            "component": {
                "type": "string",
                "description": "Name of the component, e.g. 'compiler'",
            }
        },
        "required": ["component"],
    },
}


def test_gemini() -> bool:
    print(f"\n--- Testing Gemini Primary Provider (Model: {config.gemini_model}) ---")
    if not config.google_api_key:
        print("FAILED: GOOGLE_API_KEY is not set in environment or .env.")
        return False

    provider = LLMProvider(gemini_model=config.gemini_model)

    # 1. Trivial test call
    print("1. Executing trivial text completion...", end=" ")
    try:
        messages = [LLMMessage(role="user", content="Reply with exactly 'OK' and nothing else.")]
        res = provider._call_gemini(messages, tools=[], system="You are a concise test responder.")
        print(f"PASS (Response: '{res.content.strip() if res.content else ''}')")
    except Exception as exc:
        print(f"FAILED ({type(exc).__name__}: {exc})")
        return False

    # 2. Forced tool call
    print("2. Executing forced tool call...", end=" ")
    try:
        import time
        messages = [
            LLMMessage(
                role="user",
                content="Please check the current status for the 'compiler' component using get_current_status.",
            )
        ]
        res = None
        for attempt in range(2):
            try:
                res = provider._call_gemini(messages, tools=[DUMMY_TOOL], system="Always call get_current_status.")
                break
            except Exception as exc:
                if attempt == 0 and ("503" in str(exc) or "UNAVAILABLE" in str(exc)):
                    time.sleep(2)
                    continue
                raise
        if res and res.tool_calls and res.tool_calls[0]["name"] == "get_current_status":
            print(f"PASS (Called: {res.tool_calls[0]['name']} with args: {res.tool_calls[0]['args']})")
        else:
            print(f"FAILED (Model did not call tool: text='{res.content if res else None}')")
            return False
    except Exception as exc:
        print(f"FAILED ({type(exc).__name__}: {exc})")
        return False

    print("Gemini verification: ALL PASS")
    return True


def test_groq() -> bool:
    print(f"\n--- Testing Groq Fallback Provider (Model: {config.groq_model}) ---")
    if not config.groq_api_key:
        print("FAILED: GROQ_API_KEY is not set in environment or .env.")
        return False

    provider = LLMProvider(groq_model=config.groq_model, timeout_seconds=15)

    # 1. Trivial test call
    print("1. Executing trivial text completion...", end=" ")
    try:
        messages = [LLMMessage(role="user", content="Reply with exactly 'OK' and nothing else.")]
        res = provider._call_groq(messages, tools=[], system="You are a concise test responder.")
        print(f"PASS (Response: '{res.content.strip() if res.content else ''}')")
    except Exception as exc:
        print(f"FAILED ({type(exc).__name__}: {exc})")
        return False

    # 2. Forced tool call
    print("2. Executing forced tool call...", end=" ")
    try:
        messages = [
            LLMMessage(
                role="user",
                content="Please check the current status for the 'compiler' component using get_current_status.",
            )
        ]
        res = provider._call_groq(messages, tools=[DUMMY_TOOL], system="Always call get_current_status.")
        if res.tool_calls and res.tool_calls[0]["name"] == "get_current_status":
            print(f"PASS (Called: {res.tool_calls[0]['name']} with args: {res.tool_calls[0]['args']})")
        else:
            print(f"FAILED (Model did not call tool: text='{res.content}')")
            return False
    except Exception as exc:
        print(f"FAILED ({type(exc).__name__}: {exc})")
        return False

    print("Groq verification: ALL PASS")
    return True


def main() -> int:
    print("=== [Onboarding assistant] LLM Provider Smoke Test ===")
    gemini_ok = test_gemini()
    groq_ok = test_groq()

    print("\n=== Summary ===")
    print(f"Gemini: {'PASS' if gemini_ok else 'FAIL'}")
    print(f"Groq:   {'PASS' if groq_ok else 'FAIL'}")

    # Return 0 if at least one works or both work
    if gemini_ok or groq_ok:
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())

