"""adaptive_tools — Oracle-driven dynamic tool selection for local models.

Problem: loading all 40 tools (15.7k tokens) on every request wastes context
and prefill time on local models like Qwopus. This module selects a small
relevant subset per turn using the ToolOracle, plus an always-on core tier
and a ``discover_tools`` escape hatch.

Architecture:
    - Core tier: ~8 always-loaded tools (file, terminal, code, web basics).
    - Oracle picks: ToolOracle.predict_tools() adds 5-8 task-relevant tools.
    - discover_tools: meta-tool the model calls to load any missing tool.
    - Session persistence: once loaded, a tool stays for the whole session.

Gated via config ``adaptive_tools: true`` (default true for local providers).
When disabled, returns the full ``agent.tools`` list unchanged.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------
# Core tier — always loaded regardless of oracle prediction.
# These cover basic capability so the agent never loses file/shell/code/web
# access even if the oracle has no data for a task type (cold start).
# --------------------------------------------------------------------------
CORE_TOOL_NAMES: frozenset = frozenset({
    "read_file",
    "write_file",
    "patch",
    "search_files",
    "terminal",
    "execute_code",
    "web_search",
    "web_extract",
    "clarify",
    "todo",
    "skills_list",
    "skill_view",
})

# How many tools the oracle should predict per turn (on top of core).
ORACLE_PICK_LIMIT = 8

# Cold-start fallback: if the oracle returns nothing, load these frequently-
# useful tools in addition to core. Covers common task types when there's
# no usage history yet.
COLD_START_TOOL_NAMES: frozenset = frozenset({
    "memory",
    "delegate_task",
    "session_search",
    "code_intelligence",
    "working_memory",
    "context_stash",
    "background_check",
    "process",
})


def _build_index(all_tools: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Build a name -> tool-definition lookup from the full tool list."""
    index = {}
    for tool in all_tools:
        fn = tool.get("function", tool)
        name = fn.get("name")
        if name:
            index[name] = tool
    return index


def _tool_search_terms(tool: Dict[str, Any]) -> str:
    """Extract a lowercase search string (name + description) from a tool def."""
    fn = tool.get("function", tool)
    name = fn.get("name", "")
    desc = fn.get("description", "")
    return f"{name} {desc}".lower()


def select_tools_for_turn(
    agent: Any,
    user_message: str = "",
    *,
    force_refresh: bool = False,
) -> Optional[List[Dict[str, Any]]]:
    """Select a relevant subset of tools for the current turn.

    Returns the active tool list (core + oracle picks + session-persisted +
    discover_tools). Falls back to ``agent.tools`` (full list) if adaptive
    loading is disabled or anything goes wrong — never returns None when
    agent.tools is populated.

    Args:
        agent: The agent object. Must have ``.tools`` (full list) and
            optionally ``.tool_oracle`` / ``.config``.
        user_message: The current user message, for oracle prediction.
        force_refresh: Re-run oracle prediction even if we have a cached set.
    """
    full_tools = getattr(agent, "tools", None)
    if not full_tools:
        return None

    # Config gate — disabled means use the full list (cloud models, etc.)
    cfg = getattr(agent, "config", None) or {}
    if isinstance(cfg, dict):
        adaptive_enabled = cfg.get("adaptive_tools", True)
    else:
        adaptive_enabled = getattr(cfg, "adaptive_tools", True) if cfg else True

    # Auto-disable for cloud providers (large context, latency doesn't matter).
    # We detect "local" by checking if the base_url points at localhost/127.
    if adaptive_enabled:
        base_url = ""
        if isinstance(cfg, dict):
            model_cfg = cfg.get("model", {})
            base_url = model_cfg.get("base_url", "") if isinstance(model_cfg, dict) else ""
        if not base_url:
            base_url = getattr(agent, "base_url", "") or ""
        # If it's a cloud URL (not localhost), disable adaptive unless explicitly on.
        is_local = any(x in base_url for x in ("localhost", "127.0.0.1", "0.0.0.0", "spark-85e8"))
        explicit = isinstance(cfg, dict) and "adaptive_tools" in cfg
        if not is_local and not explicit:
            adaptive_enabled = False

    if not adaptive_enabled:
        return full_tools

    try:
        return _select_adaptive(agent, full_tools, user_message, force_refresh)
    except Exception as e:
        logger.debug("adaptive_tools: selection failed (%s), falling back to full set", e)
        return full_tools


def _select_adaptive(
    agent: Any,
    full_tools: List[Dict[str, Any]],
    user_message: str,
    force_refresh: bool,
) -> List[Dict[str, Any]]:
    """Core selection logic. Assumes adaptive is enabled."""

    index = _build_index(full_tools)

    # Session-persisted set: tools that have been loaded this session.
    # Starts empty, grows as oracle/discover add tools.
    if not hasattr(agent, "_adaptive_active_names"):
        agent._adaptive_active_names = set()
    active_names: set = agent._adaptive_active_names

    # On the very first call (or force_refresh), run oracle prediction.
    if not active_names or force_refresh:
        # Seed with core tier — always available.
        active_names.update(n for n in CORE_TOOL_NAMES if n in index)

        # Oracle prediction: add task-relevant tools.
        oracle = getattr(agent, "tool_oracle", None)
        predicted: List[str] = []
        if oracle and user_message:
            try:
                result = oracle.predict_tools(user_message, limit=ORACLE_PICK_LIMIT)
                primary = result.get("primary", "")
                alts = result.get("alternatives", [])
                if primary:
                    predicted.append(primary)
                predicted.extend(alts)
            except Exception as e:
                logger.debug("adaptive_tools: oracle prediction failed (%s)", e)

        # Cold-start fallback: if oracle returned nothing useful, add the
        # cold-start set so the agent has reasonable coverage.
        predicted_valid = [p for p in predicted if p in index]
        if not predicted_valid:
            for name in COLD_START_TOOL_NAMES:
                if name in index:
                    predicted_valid.append(name)

        active_names.update(predicted_valid)

    # Always include discover_tools so the model can load anything we missed.
    if "discover_tools" in index:
        active_names.add("discover_tools")

    # Build the output list from the active names, preserving original order.
    selected = [index[name] for name in active_names if name in index]

    logger.debug(
        "adaptive_tools: selected %d/%d tools (core+oracle+persisted+discover)",
        len(selected), len(full_tools),
    )
    return selected


# --------------------------------------------------------------------------
# discover_tools — the meta-tool the model calls to find + load tools.
# Registered into the tool registry so it appears in the active set.
# --------------------------------------------------------------------------

DISCOVER_TOOLS_SCHEMA = {
    "type": "function",
    "function": {
        "name": "discover_tools",
        "description": (
            "Find and load tools you don't currently have. If a task needs a "
            "tool that isn't in your current set (e.g. browser, image generation, "
            "kanban, discord, vision), call this with a search query. Returns "
            "matching tool names and descriptions; the matching tools become "
            "available for all subsequent turns in this session. Example: "
            "discover_tools('browser web page navigate') loads browser tools."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query describing the capability you need (e.g. 'browse web page', 'generate image', 'manage tasks board').",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max tools to load (default 5).",
                    "default": 5,
                },
            },
            "required": ["query"],
        },
    },
}


def handle_discover_tools(
    agent: Any,
    query: str,
    limit: int = 5,
) -> str:
    """Handler for the discover_tools tool call.

    Searches the full tool registry by query, adds matching tools to the
    session's active set, and returns their names + descriptions so the model
    knows what just became available.
    """
    full_tools = getattr(agent, "tools", []) or []
    index = _build_index(full_tools)

    q = (query or "").lower()
    terms = q.split()

    # Score each tool by how many query terms appear in its name+description.
    scored = []
    for name, tool in index.items():
        if name == "discover_tools":
            continue  # don't recommend the meta-tool itself
        searchable = _tool_search_terms(tool)
        score = sum(1 for t in terms if t in searchable)
        # Exact name match is a strong signal.
        if q in name.lower():
            score += 5
        if score > 0:
            scored.append((score, name, tool))

    scored.sort(key=lambda x: -x[0])
    matches = scored[:limit]

    if not matches:
        return (
            f"No tools found matching '{query}'. Available toolsets: "
            + ", ".join(sorted({t.get("function", t).get("name", "").split("_")[0] for t in full_tools}))
            + ". Try a broader search term."
        )

    # Add matched tools to the session active set.
    if not hasattr(agent, "_adaptive_active_names"):
        agent._adaptive_active_names = set()
    loaded = []
    for _, name, _ in matches:
        agent._adaptive_active_names.add(name)
        loaded.append(name)

    # Build a readable response listing what was loaded.
    lines = [f"Loaded {len(loaded)} tool(s) for this session:"]
    for _, name, tool in matches:
        fn = tool.get("function", tool)
        desc = (fn.get("description", "") or "")[:120].replace("\n", " ")
        lines.append(f"  • {name}: {desc}")
    lines.append("\nThese tools are now available. Use them in your next response.")
    return "\n".join(lines)


def register_discover_tools(registry: Any) -> None:
    """Register the discover_tools meta-tool in the tool registry.

    Called during agent init so the tool is available for execution when
    the model calls it. The schema is added to the active set separately
    by select_tools_for_turn().
    """
    try:
        registry.register(
            name="discover_tools",
            toolset="cognitive",
            schema=DISCOVER_TOOLS_SCHEMA["function"],
            handler=lambda agent, **kw: handle_discover_tools(agent, **kw),
            check_fn=lambda: True,
            requires_env=None,
            is_async=False,
            description=DISCOVER_TOOLS_SCHEMA["function"]["description"],
            emoji="🔍",
        )
        logger.debug("adaptive_tools: registered discover_tools meta-tool")
    except Exception as e:
        # Already registered is fine; other errors are non-fatal.
        logger.debug("adaptive_tools: discover_tools registration (%s)", e)


def inject_discover_schema(tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Ensure the discover_tools schema is in the active tool list.

    If adaptive tools built its set from the registry but discover_tools
    wasn't in the original full list (because it's a synthetic meta-tool),
    this adds it. Called by select_tools_for_turn after building the set.
    """
    names = {t.get("function", t).get("name") for t in tools}
    if "discover_tools" not in names:
        return tools + [DISCOVER_TOOLS_SCHEMA]
    return tools
