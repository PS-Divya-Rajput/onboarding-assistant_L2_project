"""Unified LLM Provider abstraction with Gemini primary, Groq fallback, and circuit breaker.

Features:
- Provider-neutral internal message representation.
- Robust failover from Gemini to Groq on timeouts, 429 rate limits, 5xx, or 401/403/404 config errors.
- 60-second circuit breaker skipping Gemini after a failure to avoid compound latency.
- Real client-side timeout cancellation.
- Full error logging without masking root causes.
"""

from __future__ import annotations

import json
import logging
import sys
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional

from config import config

logger = logging.getLogger("onboarding_assistant.llm")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


class LLMUnavailable(Exception):
    """Raised when both primary (Gemini) and fallback (Groq) LLM providers fail."""
    pass


@dataclass
class LLMMessage:
    """Provider-neutral conversation message."""
    role: Literal["system", "user", "assistant", "tool"]
    content: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None
    name: Optional[str] = None


@dataclass
class LLMResponse:
    """Provider-neutral response container."""
    content: Optional[str] = None
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    provider_used: str = "Gemini"


class CircuitBreaker:
    """Tracks provider failures and enforces a 60-second cooldown period."""

    def __init__(self, cooldown_seconds: float = 60.0):
        self.cooldown_seconds = cooldown_seconds
        self.last_failure_time: float = 0.0

    def is_tripped(self) -> bool:
        if self.last_failure_time <= 0.0:
            return False
        return (time.time() - self.last_failure_time) < self.cooldown_seconds

    def record_failure(self) -> None:
        self.last_failure_time = time.time()

    def record_success(self) -> None:
        self.last_failure_time = 0.0


# Module-level Gemini circuit breaker
gemini_circuit_breaker = CircuitBreaker(cooldown_seconds=60.0)


class LLMProvider:
    """Manages LLM requests, provider-specific conversions, and failover orchestration."""

    def __init__(
        self,
        gemini_model: Optional[str] = None,
        groq_model: Optional[str] = None,
        timeout_seconds: Optional[int] = None,
    ):
        self.gemini_model = gemini_model or config.gemini_model
        self.groq_model = groq_model or config.groq_model
        self.timeout_seconds = timeout_seconds or config.llm_timeout_seconds

    # --------------------------------------------------------------------------
    # Gemini Adapter
    # --------------------------------------------------------------------------
    def _call_gemini(
        self,
        messages: List[LLMMessage],
        tools: List[Dict[str, Any]],
        system: Optional[str] = None,
    ) -> LLMResponse:
        from google import genai
        from google.genai import types

        client_kwargs: Dict[str, Any] = {"api_key": config.google_api_key}
        if self.timeout_seconds and self.timeout_seconds >= 60:
            client_kwargs["http_options"] = types.HttpOptions(timeout=float(self.timeout_seconds))
        client = genai.Client(**client_kwargs)

        # 1. Build tool declarations
        sdk_tools = []
        if tools:
            func_decls = []
            for t in tools:
                func_decls.append(
                    types.FunctionDeclaration(
                        name=t["name"],
                        description=t.get("description", ""),
                        parameters=t.get("parameters", {}),
                    )
                )
            sdk_tools.append(types.Tool(function_declarations=func_decls))

        config_params: Dict[str, Any] = {
            "temperature": 0.2,
        }
        if system:
            config_params["system_instruction"] = system
        if sdk_tools:
            config_params["tools"] = sdk_tools

        gen_config = types.GenerateContentConfig(**config_params)

        # 2. Convert internal messages to Gemini Content objects
        contents: List[types.Content] = []
        for msg in messages:
            if msg.role == "system":
                continue  # Handled via system_instruction
            elif msg.role == "user":
                contents.append(
                    types.Content(role="user", parts=[types.Part.from_text(text=msg.content or "")])
                )
            elif msg.role == "assistant":
                parts: List[types.Part] = []
                if msg.content:
                    parts.append(types.Part.from_text(text=msg.content))
                if msg.tool_calls:
                    for tc in msg.tool_calls:
                        p_kwargs: Dict[str, Any] = {
                            "function_call": types.FunctionCall(
                                name=tc["name"],
                                args=tc.get("args", {}),
                            )
                        }
                        if tc.get("thought_signature"):
                            p_kwargs["thought_signature"] = tc["thought_signature"]
                        parts.append(types.Part(**p_kwargs))
                if parts:
                    contents.append(types.Content(role="model", parts=parts))
            elif msg.role == "tool":
                resp_payload = {}
                if msg.content:
                    try:
                        resp_payload = json.loads(msg.content)
                    except Exception:
                        resp_payload = {"result": msg.content}
                contents.append(
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_function_response(
                                name=msg.name or "unknown_tool",
                                response=resp_payload,
                            )
                        ],
                    )
                )

        models_to_try = [self.gemini_model]
        for backup in ["gemini-3.5-flash-lite", "gemini-3-flash-preview", "gemini-3.5-flash"]:
            if backup not in models_to_try:
                models_to_try.append(backup)

        last_exc = None
        response = None
        for m_name in models_to_try:
            try:
                response = client.models.generate_content(
                    model=m_name,
                    contents=contents,
                    config=gen_config,
                )
                break
            except Exception as exc:
                last_exc = exc
                exc_str = str(exc)
                if any(err in exc_str for err in ["429", "RESOURCE_EXHAUSTED", "503", "UNAVAILABLE", "high demand"]):
                    logger.warning(f"Gemini model {m_name} returned rate/load error ({type(exc).__name__}), trying next candidate model...")
                    continue
                else:
                    raise

        if response is None and last_exc:
            raise last_exc

        # 3. Extract text content and tool calls
        final_text = ""
        tool_calls: List[Dict[str, Any]] = []

        if response.text:
            final_text = response.text

        # Check candidates parts for function calls and thought signatures
        if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
            for idx, part in enumerate(response.candidates[0].content.parts):
                if part.function_call:
                    fc = part.function_call
                    tool_calls.append({
                        "id": getattr(fc, "id", None) or f"call_{idx}_{fc.name}",
                        "name": fc.name,
                        "args": dict(fc.args) if fc.args else {},
                        "thought_signature": getattr(part, "thought_signature", None),
                    })
        elif hasattr(response, "function_calls") and response.function_calls:
            for idx, fc in enumerate(response.function_calls):
                tool_calls.append({
                    "id": f"call_{idx}_{fc.name}",
                    "name": fc.name,
                    "args": dict(fc.args) if fc.args else {},
                })

        return LLMResponse(content=final_text if final_text else None, tool_calls=tool_calls, provider_used="Gemini")

    # --------------------------------------------------------------------------
    # Groq Adapter
    # --------------------------------------------------------------------------
    def _call_groq(
        self,
        messages: List[LLMMessage],
        tools: List[Dict[str, Any]],
        system: Optional[str] = None,
        is_retry: bool = False,
    ) -> LLMResponse:
        from groq import Groq

        if not config.groq_api_key:
            raise ValueError("Groq API key not configured in .env")

        client = Groq(api_key=config.groq_api_key, timeout=float(self.timeout_seconds))

        # 1. Convert messages to OpenAI compatible dicts
        groq_messages: List[Dict[str, Any]] = []
        if system:
            groq_messages.append({"role": "system", "content": system})

        for msg in messages:
            if msg.role == "system":
                groq_messages.append({"role": "system", "content": msg.content or ""})
            elif msg.role == "user":
                groq_messages.append({"role": "user", "content": msg.content or ""})
            elif msg.role == "assistant":
                item: Dict[str, Any] = {"role": "assistant"}
                if msg.content:
                    item["content"] = msg.content
                if msg.tool_calls:
                    item["tool_calls"] = [
                        {
                            "id": tc.get("id", f"call_{tc['name']}"),
                            "type": "function",
                            "function": {
                                "name": tc["name"],
                                "arguments": json.dumps(tc.get("args", {})),
                            },
                        }
                        for tc in msg.tool_calls
                    ]
                groq_messages.append(item)
            elif msg.role == "tool":
                groq_messages.append({
                    "role": "tool",
                    "tool_call_id": msg.tool_call_id or f"call_{msg.name}",
                    "name": msg.name or "tool",
                    "content": msg.content or "{}",
                })

        # 2. Convert tools to OpenAI format
        groq_tools = None
        if tools:
            groq_tools = [
                {
                    "type": "function",
                    "function": {
                        "name": t["name"],
                        "description": t.get("description", ""),
                        "parameters": t.get("parameters", {"type": "object", "properties": {}}),
                    },
                }
                for t in tools
            ]

        try:
            kwargs: Dict[str, Any] = {
                "model": self.groq_model,
                "messages": groq_messages,
                "temperature": 0.2,
            }
            if groq_tools:
                kwargs["tools"] = groq_tools

            response = client.chat.completions.create(**kwargs)
            choice = response.choices[0].message

            tool_calls = []
            if choice.tool_calls:
                for tc in choice.tool_calls:
                    try:
                        args = json.loads(tc.function.arguments) if tc.function.arguments else {}
                    except Exception:
                        args = {}
                    tool_calls.append({
                        "id": tc.id,
                        "name": tc.function.name,
                        "args": args,
                    })

            return LLMResponse(content=choice.content, tool_calls=tool_calls, provider_used="Groq")

        except Exception as exc:
            exc_str = str(exc)
            # Handle tool_use_failed 400 (malformed tool call) with one retry
            if not is_retry and ("tool_use_failed" in exc_str or "bad request" in exc_str.lower()):
                logger.warning("Groq tool call formatting issue detected. Retrying with format instruction...")
                reminder = LLMMessage(
                    role="user",
                    content="Please emit tool calls with strictly valid JSON arguments adhering to the schema.",
                )
                return self._call_groq(messages + [reminder], tools, system=system, is_retry=True)
            raise

    # --------------------------------------------------------------------------
    # Master Chat Method with Failover & Circuit Breaker
    # --------------------------------------------------------------------------
    def chat(
        self,
        messages: List[LLMMessage],
        tools: List[Dict[str, Any]],
        system: Optional[str] = None,
    ) -> LLMResponse:
        """Execute chat completion with primary Gemini provider and failover to Groq."""
        gemini_error: Optional[Exception] = None

        # 1. Attempt Gemini if circuit breaker is not tripped
        if not gemini_circuit_breaker.is_tripped():
            for attempt in range(2):
                try:
                    res = self._call_gemini(messages, tools, system=system)
                    gemini_circuit_breaker.record_success()
                    return res
                except Exception as exc:
                    gemini_error = exc
                    exc_name = type(exc).__name__
                    exc_msg = str(exc)
                    if attempt == 0 and ("503" in exc_msg or "UNAVAILABLE" in exc_msg or "high demand" in exc_msg):
                        time.sleep(1.5)
                        continue
                    gemini_circuit_breaker.record_failure()

                    # Check for configuration errors (401/403/404)
                    if any(code in exc_msg for code in ["401", "403", "404", "PERMISSION_DENIED", "NOT_FOUND", "not configured"]):
                        logger.error(f"CONFIG ERROR in Gemini configuration: {exc_name}: {exc_msg}")
                    else:
                        logger.warning(f"Gemini call failed ({exc_name}: {exc_msg}). Circuit breaker tripped for 60s. Failing over to Groq.")
                    break
        else:
            if gemini_circuit_breaker.is_tripped():
                logger.info("Gemini circuit breaker active. Routing directly to Groq fallback.")

        # 2. Attempt Groq fallback
        try:
            res = self._call_groq(messages, tools, system=system)
            return res
        except Exception as groq_error:
            logger.error(f"Groq fallback failed ({type(groq_error).__name__}: {groq_error})")
            error_details = (
                f"Gemini error: {type(gemini_error).__name__ if gemini_error else 'Circuit breaker tripped'} ({gemini_error or 'cooldown'}); "
                f"Groq error: {type(groq_error).__name__} ({groq_error})"
            )
            raise LLMUnavailable(f"Both LLM providers failed. {error_details}") from groq_error

