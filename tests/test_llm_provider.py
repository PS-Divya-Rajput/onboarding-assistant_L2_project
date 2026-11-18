"""Unit tests for LLM provider failover, circuit breaker, and error propagation."""

import pytest
from unittest.mock import MagicMock, patch
from agent.llm_provider import (
    CircuitBreaker,
    LLMMessage,
    LLMProvider,
    LLMResponse,
    LLMUnavailable,
    gemini_circuit_breaker,
)


@pytest.fixture(autouse=True)
def reset_circuit_breaker():
    """Reset circuit breaker state before each test."""
    gemini_circuit_breaker.record_success()


def test_gemini_success():
    """Test successful Gemini invocation without failover."""
    provider = LLMProvider()
    expected_resp = LLMResponse(content="Gemini says hello", tool_calls=[], provider_used="Gemini")

    with patch.object(provider, "_call_gemini", return_value=expected_resp) as mock_gemini:
        with patch.object(provider, "_call_groq") as mock_groq:
            resp = provider.chat([LLMMessage(role="user", content="hello")], tools=[])
            assert resp.content == "Gemini says hello"
            assert resp.provider_used == "Gemini"
            mock_gemini.assert_called_once()
            mock_groq.assert_not_called()


@pytest.mark.parametrize("error_cls,error_msg", [
    (Exception, "429 Quota Exceeded"),
    (TimeoutError, "Request timed out after 20 seconds"),
    (Exception, "500 Internal Server Error"),
    (Exception, "404 Model not found"),
])
def test_gemini_failover_to_groq(error_cls, error_msg):
    """Test that Gemini raising 429, timeout, 500, or 404 cleanly fails over to Groq."""
    provider = LLMProvider()
    groq_resp = LLMResponse(content="Groq answer", tool_calls=[], provider_used="Groq")

    with patch.object(provider, "_call_gemini", side_effect=error_cls(error_msg)):
        with patch.object(provider, "_call_groq", return_value=groq_resp) as mock_groq:
            resp = provider.chat([LLMMessage(role="user", content="setup")], tools=[])
            assert resp.content == "Groq answer"
            assert resp.provider_used == "Groq"
            mock_groq.assert_called_once()


def test_circuit_breaker_skips_gemini_on_subsequent_call():
    """Test that after a Gemini failure, circuit breaker trips and skips Gemini for 60s."""
    provider = LLMProvider()
    groq_resp = LLMResponse(content="Groq fast answer", tool_calls=[], provider_used="Groq")

    # 1. First call fails on Gemini -> trips circuit breaker
    with patch.object(provider, "_call_gemini", side_effect=Exception("500 Internal Server Error")) as mock_gemini:
        with patch.object(provider, "_call_groq", return_value=groq_resp):
            resp1 = provider.chat([LLMMessage(role="user", content="first")], tools=[])
            assert resp1.provider_used == "Groq"
            assert mock_gemini.call_count == 1
            assert gemini_circuit_breaker.is_tripped() is True

    # 2. Second call should NOT call Gemini at all
    with patch.object(provider, "_call_gemini") as mock_gemini2:
        with patch.object(provider, "_call_groq", return_value=groq_resp) as mock_groq2:
            resp2 = provider.chat([LLMMessage(role="user", content="second")], tools=[])
            assert resp2.provider_used == "Groq"
            mock_gemini2.assert_not_called()
            mock_groq2.assert_called_once()


def test_both_providers_fail_raises_llm_unavailable():
    """Test that when both Gemini and Groq fail, LLMUnavailable is raised with both error causes."""
    provider = LLMProvider()

    with patch.object(provider, "_call_gemini", side_effect=Exception("Gemini quota 429")):
        with patch.object(provider, "_call_groq", side_effect=Exception("Groq rate limit 429")):
            with pytest.raises(LLMUnavailable) as exc_info:
                provider.chat([LLMMessage(role="user", content="hi")], tools=[])

            err_text = str(exc_info.value)
            assert "Both LLM providers failed" in err_text
            assert "Gemini" in err_text
            assert "Groq" in err_text

