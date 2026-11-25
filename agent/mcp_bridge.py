"""Thread-safe synchronous bridge over the asynchronous Model Context Protocol (MCP) client.

Runs a single long-lived background thread hosting an asyncio event loop (Proactor policy on Windows).
Connects to the MCP server subprocess over stdio, caches schemas, strips hidden parameters,
and exposes thread-safe synchronous call_tool and list_tools methods.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional
from mcp import StdioServerParameters
from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client
from logging_config import get_logger

logger = get_logger("onboarding_assistant.bridge")

HIDDEN_PARAMETERS = {"dry_run", "user_id", "repo"}


class MCPBridge:
    """Manages an async MCP client session running inside a dedicated background thread."""

    def __init__(self, server_script: Optional[str] = None):
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._session: Optional[ClientSession] = None
        self._session_ready = threading.Event()
        self._shutdown_event = threading.Event()
        self._server_script = server_script or "mcp_server.server"
        self._cached_tools: Optional[List[Dict[str, Any]]] = None
        self._start_background_thread()

    def _start_background_thread(self) -> None:
        """Initialize background thread and start the asyncio loop."""
        self._thread = threading.Thread(target=self._run_loop, name="MCPBridgeThread", daemon=True)
        self._thread.start()
        # Wait for the session to be fully initialized
        if not self._session_ready.wait(timeout=25.0):
            raise RuntimeError("Timed out waiting for MCP background client to initialize.")

    def _run_loop(self) -> None:
        """Target for the background worker thread."""
        if sys.platform == "win32":
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)

        try:
            self._loop.run_until_complete(self._async_session_runner())
        except Exception as exc:
            logger.error(f"Error in MCPBridge background event loop: {type(exc).__name__}: {exc}")
        finally:
            self._loop.close()

    async def _async_session_runner(self) -> None:
        """Run stdio client session inside the background thread."""
        server_params = StdioServerParameters(
            command=sys.executable,
            args=["-m", self._server_script],
            env={**os.environ, "PYTHONUNBUFFERED": "1", "PYTHONIOENCODING": "utf-8"},
        )
        logger.info(f"Starting MCP server subprocess '{self._server_script}' over stdio...")

        try:
            async with stdio_client(server_params) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    self._session = session
                    self._session_ready.set()
                    logger.info("MCP ClientSession initialized successfully.")

                    # Keep running until shutdown signal is received
                    while not self._shutdown_event.is_set():
                        await asyncio.sleep(0.1)
        except Exception as exc:
            logger.error(f"MCP Session Runner encountered error: {type(exc).__name__}: {exc}")
            self._session_ready.set()  # Avoid blocking waiters

    def list_tools(self) -> List[Dict[str, Any]]:
        """Return tool declarations for the LLM with hidden parameters stripped."""
        if self._cached_tools is not None:
            return self._cached_tools

        if not self._loop or not self._session:
            raise RuntimeError("MCP Bridge session is not ready.")

        logger.info("Listing MCP tools from server...")
        future = asyncio.run_coroutine_threadsafe(self._session.list_tools(), self._loop)
        mcp_tools_res = future.result(timeout=15.0)

        cleaned_tools: List[Dict[str, Any]] = []
        for tool in mcp_tools_res.tools:
            raw_schema = tool.input_schema if hasattr(tool, "input_schema") and tool.input_schema else {}
            properties = dict(raw_schema.get("properties", {}))
            required = list(raw_schema.get("required", []))

            # Strip hidden parameters (dry_run, user_id, repo) from model visibility
            for hidden in HIDDEN_PARAMETERS:
                properties.pop(hidden, None)
                if hidden in required:
                    required.remove(hidden)

            sanitized_schema = {
                "type": "object",
                "properties": properties,
            }
            if required:
                sanitized_schema["required"] = required

            cleaned_tools.append({
                "name": tool.name,
                "description": tool.description or "",
                "parameters": sanitized_schema,
            })

        self._cached_tools = cleaned_tools
        logger.info(f"Successfully loaded and cached {len(cleaned_tools)} MCP tools.")
        return self._cached_tools

    def call_tool(self, name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronously execute a tool through the MCP client session."""
        if not self._loop or not self._session:
            raise RuntimeError("MCP Bridge session is not active.")

        logger.info(f"Bridge executing MCP tool: '{name}'")
        # Timeout increased to 120s to accommodate model loading on cold start
        future = asyncio.run_coroutine_threadsafe(
            self._session.call_tool(name=name, arguments=args),
            self._loop,
        )
        res = future.result(timeout=120.0)

        # Parse structured content or text JSON
        if hasattr(res, "structured_content") and res.structured_content:
            return res.structured_content

        if hasattr(res, "content") and res.content:
            for item in res.content:
                if hasattr(item, "text") and item.text:
                    try:
                        return json.loads(item.text)
                    except Exception:
                        return {"result": item.text}

        return {"result": str(res)}

    def close(self) -> None:
        """Cleanly terminate the client session and background thread."""
        self._shutdown_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3.0)


# Global singleton bridge instance
_bridge_instance: Optional[MCPBridge] = None
_bridge_lock = threading.Lock()


def get_mcp_bridge() -> MCPBridge:
    """Return singleton MCPBridge instance."""
    global _bridge_instance
    with _bridge_lock:
        if _bridge_instance is None:
            _bridge_instance = MCPBridge()
        return _bridge_instance

