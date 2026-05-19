"""Async wrapper for AIAgent — non-invasive asyncio facade.

This module provides ``AsyncAgentWrapper``, a thin async wrapper around the
synchronous ``AIAgent`` class from ``run_agent``.  It does **not** rewrite any
of the synchronous core; instead it delegates to ``AIAgent`` inside
``asyncio.to_thread`` (or ``loop.run_in_executor`` on Python < 3.9) and adds
an async tool-execution helper that runs multiple tool calls concurrently via
``asyncio.gather``.

Typical usage::

    from run_agent import AIAgent
    from agent.async_core import AsyncAgentWrapper

    agent = AIAgent(base_url="...", model="...")
    async_agent = AsyncAgentWrapper(agent)

    result = await async_agent.async_run([
        {"role": "user", "content": "What is 2+2?"}
    ])
"""

from __future__ import annotations

import asyncio
import sys
from typing import Any, Dict, List, Optional, Callable

# Lazy import to avoid pulling run_agent (and its heavy deps) at import time
# unless the user actually instantiates AsyncAgentWrapper.
_AIAgent = None


def _get_ai_agent_cls():
    global _AIAgent
    if _AIAgent is None:
        from run_agent import AIAgent as _cls
        _AIAgent = _cls
    return _AIAgent


class AsyncAgentWrapper:
    """Async facade for a synchronous ``AIAgent`` instance.

    All blocking ``AIAgent`` methods are executed in the default
    ``ThreadPoolExecutor`` via ``asyncio.to_thread`` (or a compatibility
    shim on older Pythons).  Tool calls can be dispatched concurrently with
    ``async_execute_tools``.

    Attributes:
        agent: The underlying synchronous ``AIAgent`` instance.
    """

    def __init__(self, agent: Any) -> None:
        """Wrap an existing ``AIAgent`` instance.

        Args:
            agent: An instantiated ``AIAgent`` (from ``run_agent``).
        """
        self.agent = agent

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _to_thread(func: Callable, *args, **kwargs):
        """Run *func* in a thread and return an awaitable.

        Uses ``asyncio.to_thread`` on Python >= 3.9, falling back to
        ``loop.run_in_executor`` on older versions.
        """
        if sys.version_info >= (3, 9):
            return asyncio.to_thread(func, *args, **kwargs)
        loop = asyncio.get_event_loop()
        return loop.run_in_executor(None, func, *args, **kwargs)

    # ------------------------------------------------------------------
    # Async versions of AIAgent public methods
    # ------------------------------------------------------------------

    async def async_run(
        self,
        messages: List[Dict[str, Any]],
        system_message: Optional[str] = None,
        stream_callback: Optional[Callable[[str], None]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Async version of ``AIAgent.run_conversation``.

        Args:
            messages: OpenAI-style message list.  The last user message is
                extracted and passed as *user_message*; any preceding items
                become *conversation_history*.
            system_message: Optional system prompt override.
            stream_callback: Optional async or sync callback for streaming
                deltas.  If provided, it is wrapped so that it can be called
                from the worker thread safely.
            **kwargs: Extra keyword arguments forwarded to
                ``run_conversation``.

        Returns:
            Dict with at least ``final_response`` and ``messages`` keys.
        """
        if not messages:
            raise ValueError("messages must not be empty")

        # Extract the last user message and treat everything before it as history
        last_user_msg = None
        for msg in reversed(messages):
            if msg.get("role") == "user":
                last_user_msg = msg.get("content", "")
                break

        if last_user_msg is None:
            raise ValueError("messages must contain at least one user message")

        conversation_history = messages[:-1] if len(messages) > 1 else None

        # run_conversation expects a sync callback; wrap an async one so it
        # can be invoked safely from the worker thread.
        wrapped_callback: Optional[Callable[[str], None]] = None
        if stream_callback is not None:
            if asyncio.iscoroutinefunction(stream_callback):
                def _sync_wrapper(delta: str) -> None:
                    try:
                        loop = asyncio.get_running_loop()
                    except RuntimeError:
                        # No loop in this thread — fire-and-forget via the
                        # main event loop if we can reach it.
                        loop = None

                    if loop is not None:
                        loop.call_soon_threadsafe(
                            lambda: asyncio.create_task(stream_callback(delta))
                        )
                    else:
                        # Best-effort: call directly (may block)
                        asyncio.run(stream_callback(delta))

                wrapped_callback = _sync_wrapper
            else:
                wrapped_callback = stream_callback

        result = await self._to_thread(
            self.agent.run_conversation,
            user_message=last_user_msg,
            system_message=system_message,
            conversation_history=conversation_history,
            stream_callback=wrapped_callback,
            **kwargs,
        )
        return result

    async def async_chat(
        self,
        message: str,
        stream_callback: Optional[Callable[[str], None]] = None,
        **kwargs: Any,
    ) -> str:
        """Async version of ``AIAgent.chat``.

        Args:
            message: User message string.
            stream_callback: Optional streaming delta callback.
            **kwargs: Forwarded to ``run_conversation``.

        Returns:
            The final assistant response string.
        """
        wrapped_callback: Optional[Callable[[str], None]] = None
        if stream_callback is not None and asyncio.iscoroutinefunction(stream_callback):
            def _sync_wrapper(delta: str) -> None:
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    loop = None
                if loop is not None:
                    loop.call_soon_threadsafe(
                        lambda: asyncio.create_task(stream_callback(delta))
                    )
                else:
                    asyncio.run(stream_callback(delta))

            wrapped_callback = _sync_wrapper
        else:
            wrapped_callback = stream_callback

        return await self._to_thread(
            self.agent.chat,
            message,
            stream_callback=wrapped_callback,
            **kwargs,
        )

    # ------------------------------------------------------------------
    # Concurrent tool execution
    # ------------------------------------------------------------------

    async def async_execute_tools(
        self,
        tool_calls: List[Dict[str, Any]],
        task_id: Optional[str] = None,
        **kwargs: Any,
    ) -> List[Dict[str, Any]]:
        """Execute multiple tool calls concurrently.

        Each item in *tool_calls* should be a dict with at least:

        - ``name`` (str): The tool/function name.
        - ``arguments`` (dict): The arguments to pass.
        - ``id`` (str, optional): The tool-call ID for correlation.

        Args:
            tool_calls: List of tool-call descriptors.
            task_id: Optional task ID forwarded to the underlying tool
                dispatcher.
            **kwargs: Extra keyword arguments forwarded to each tool
                invocation.

        Returns:
            A list of result dicts, one per input tool call, in the same
            order.  Each result dict contains:

            - ``tool_call_id`` (str): The ID from the input (or a generated
              fallback).
            - ``name`` (str): The tool name.
            - ``result`` (Any): The raw return value from the tool.
            - ``error`` (str, optional): Populated if the tool raised an
              exception.
        """
        async def _run_one(tc: Dict[str, Any]) -> Dict[str, Any]:
            name = tc.get("name", tc.get("function", ""))
            arguments = tc.get("arguments", tc.get("args", {}))
            tc_id = tc.get("id", tc.get("tool_call_id", ""))

            try:
                # Prefer the agent's internal _invoke_tool if available
                # (handles agent-level tools like todo, memory, etc.).
                if hasattr(self.agent, "_invoke_tool"):
                    result = await self._to_thread(
                        self.agent._invoke_tool,
                        function_name=name,
                        function_args=arguments,
                        effective_task_id=task_id or "",
                        tool_call_id=tc_id,
                        **kwargs,
                    )
                else:
                    # Fall back to the module-level handle_function_call
                    from model_tools import handle_function_call as _hfc
                    result = await self._to_thread(
                        _hfc,
                        function_name=name,
                        function_args=arguments,
                        task_id=task_id,
                        tool_call_id=tc_id,
                        **kwargs,
                    )
                return {
                    "tool_call_id": tc_id,
                    "name": name,
                    "result": result,
                }
            except Exception as exc:
                return {
                    "tool_call_id": tc_id,
                    "name": name,
                    "result": None,
                    "error": str(exc),
                }

        if not tool_calls:
            return []

        results = await asyncio.gather(*(_run_one(tc) for tc in tool_calls))
        return list(results)

    # ------------------------------------------------------------------
    # Passthrough helpers (no thread hop needed — simple attribute access)
    # ------------------------------------------------------------------

    @property
    def session_id(self) -> str:
        """Passthrough to the wrapped agent's ``session_id``."""
        return self.agent.session_id

    def __getattr__(self, name: str) -> Any:
        """Forward any unknown attribute access to the wrapped agent."""
        return getattr(self.agent, name)
