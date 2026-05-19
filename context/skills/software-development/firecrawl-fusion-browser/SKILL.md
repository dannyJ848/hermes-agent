---
name: firecrawl-fusion-browser
version: 1.0
created: 2026-04-05
description: Build and maintain the Firecrawl + Browserbase fusion browser provider for Hermes Agent
---

# Firecrawl Fusion Browser Provider

## Architecture

Two systems fused into one unstoppable web extraction engine:

- **Firecrawl** handles the "what" — AI-powered scrape, search, extract, interact
- **Browserbase** handles the "where from" — residential IPs, stealth fingerprinting, anti-bot

### Layer Stack

| Layer | System | Use Case |
|-------|--------|----------|
| L1 | Firecrawl Direct | Fast scraping, search, markdown extraction |
| L2 | Firecrawl Interact | Dynamic/JS pages, prompt + code execution |
| L3 | Browserbase Stealth | Fallback when Firecrawl is blocked (Cloudflare, etc.) |
| L4 | Browserbase HTML → Firecrawl Extract | Stealth fetch raw HTML, then AI-extract |

## Key Files

| File | Purpose |
|------|---------|
| `tools/browser_providers/firecrawl_fusion.py` | Provider class (~450 lines) |
| `tools/browser_tool.py` | Provider registry (`_PROVIDER_REGISTRY`) |
| `tools/web_tools.py` | `web_interact` tool (appended at end) |
| `~/.hermes/config.yaml` | `browser.cloud_provider: firecrawl-fusion` |

## Building a Hermes Browser Provider

### 1. Implement CloudBrowserProvider

```python
from tools.browser_providers.base import CloudBrowserProvider

class MyProvider(CloudBrowserProvider):
    def provider_name(self) -> str:
        return "My-Provider"

    def is_configured(self) -> bool:
        # Check API keys, dependencies
        return True

    def create_session(self, task_id: str) -> Dict[str, object]:
        return {
            "session_name": f"my-provider-{task_id}",
            "bb_session_id": f"mp-{task_id}",  # Legacy key name
            "cdp_url": "my-provider://session",
        }

    def close_session(self, session_id: str) -> bool:  # MUST return bool
        return True

    def emergency_cleanup(self, session_id: str) -> None:  # REQUIRED abstract
        pass  # Best-effort, must not raise
```

### 2. Register in `_PROVIDER_REGISTRY`

In `tools/browser_tool.py`:

```python
_PROVIDER_REGISTRY: Dict[str, type] = {
    "browserbase": BrowserbaseProvider,
    "browser-use": BrowserUseProvider,
    "firecrawl-fusion": __import__(
        "tools.browser_providers.firecrawl_fusion",
        fromlist=["FirecrawlFusionProvider"]
    ).FirecrawlFusionProvider,
}
```

### 3. Add config entry

In `~/.hermes/config.yaml`:

```yaml
browser:
  cloud_provider: firecrawl-fusion
```

### 4. Add web tool (if needed)

Register in `tools/web_tools.py` using `registry.register()` with schema, handler, check_fn, requires_env.

## Firecrawl Interact API Pattern

The Interact API requires a two-step process:

```
1. Scrape URL → get scrape_id (session handle)
2. Interact(scrape_id, prompt=...) → execute action
3. Optionally continue with more interactions
4. Stop session when done
```

### Key Methods

```python
from firecrawl import Firecrawl
app = Firecrawl(api_key="...")

# Start session
result = app.scrape(url, formats=["markdown"])
scrape_id = result.metadata.scrape_id

# Natural language interaction
response = app.interact(scrape_id, prompt="Click the submit button")

# Code execution (Playwright/Python/Bash)
response = app.interact(scrape_id, code="agent-browser snapshot -i", language="bash")

# Response fields
output = response.output           # AI description of result
live_view_url = response.live_view_url  # Real-time browser view
interactive_url = response.interactive_live_view_url  # Interactive view
stdout = response.stdout           # Code execution output

# Stop session
app.stop_interaction(scrape_id)
```

## Pitfalls & Lessons Learned

1. **SearchData.web not .data**: Firecrawl 4.22 SDK returns `SearchData` with `.web` attribute (list of `SearchResultWeb`), NOT `.data`. Always check both.

2. **emergency_cleanup is required**: `CloudBrowserProvider` has an abstract `emergency_cleanup` method. Missing it causes `TypeError: Can't instantiate abstract class`.

3. **close_session must return bool**: The base class contract expects `-> bool`, not `-> None`. Returning None works at runtime but violates the interface.

4. **Provider registration uses dynamic import**: The `_PROVIDER_REGISTRY` dict uses `__import__()` with `fromlist` to avoid circular imports at module load time.

5. **Pydantic Document model**: Firecrawl 4.22 `scrape()` returns a `Document` pydantic model. Use `.model_dump()` or `getattr()` to access fields. Never assume it's a dict.

6. **Session cleanup is critical**: Always call `stop_interaction(scrape_id)` when done. Sessions auto-expire but waste credits if left open.

## CRITICAL: 6-Point Tool Registration Checklist

Registering a tool in `web_tools.py` is **necessary but NOT sufficient**. There are 6 separate registration points that must ALL be updated, or the tool will appear registered in Python but never reach the model's tool definitions. This was discovered through painful trial-and-error.

**Mandatory checklist when adding ANY new tool to Hermes:**

1. **`tools/web_tools.py`** (or equivalent tool file) — `registry.register()` with schema, handler, check_fn, requires_env. This is the "obvious" one.

2. **`toolsets.py`** — Add the tool name to its toolset's `"tools"` list. This is the **actual gatekeeper**. `resolve_toolset('web')` returns only tools listed here. Without this, `get_tool_definitions()` silently skips your tool. The legacy map in model_tools.py is NOT consulted if the toolset validates here.

3. **`model_tools.py`** — `_LEGACY_TOOLSET_MAP["web_tools"]` list. Fallback used when `validate_toolset()` fails. Add the tool name here too.

4. **`run_agent.py`** — `_PARALLEL_SAFE_TOOLS` frozenset (around line 216). Tools not listed here cannot be called during parallel execution. Add if safe for concurrent use.

5. **`agent/prompt_builder.py`** — `relevant_tool_names` set (around line 699). Controls which tool names appear in Nous subscription prompts. Missing = model doesn't know the tool exists.

6. **`agent/display.py`** — `primary_args` dict (around line 143). Maps tool name to its primary argument for status display. Without this, the tool shows as "using web_interact" without the URL.

**Verification command:**
```python
from model_tools import get_tool_definitions, _discover_tools, resolve_toolset
_discover_tools()
resolved = resolve_toolset('web')  # Replace 'web' with your toolset
print(f"Tools: {resolved}")
print(f"Your tool present: {'your_tool' in resolved}")
```

**Why this matters:** `registry.register()` in web_tools.py adds the tool to the Python registry. But `get_tool_definitions()` calls `resolve_toolset()` which reads from `toolsets.py`. If the tool isn't in the toolset definition, it gets filtered out BEFORE the registry is consulted. The tool appears registered in Python (`'web_interact' in registry._tools` = True) but never makes it into the model's tool schema.

## Known Limitations & Blocked Sites

### Firecrawl Policy Blocks
Firecrawl **explicitly blocks** these sites (returns "Website Not Supported"):
- **X/Twitter (x.com, twitter.com)** — policy-level block, no workaround via Firecrawl
- Other social media sites may also be blocked

### Workaround: Multi-Path X/Twitter Access
When the project requires X/Twitter access, use these alternatives:
1. **Cookie API** (`/tmp/x_api.py`) — READ-ONLY. SearchTimeline, UserTweets, HomeLatest. Best for scanning/reading.
2. **Browserbase** — Stealth browsers with residential proxies. CAN access X/Twitter. For interactive tasks.
3. **Hermes browser tools** (browser_navigate, etc.) — Local Chrome, can navigate X if logged in.
4. **Never use Firecrawl for X/Twitter** — It will fail every time.

### Language Parameter for Code Execution
Firecrawl Interact API accepts: `"python"`, `"node"`, `"bash"`.
- **NOT "javascript"** — will return 400 error: `Invalid option: expected one of "python"|"node"|"bash"`
- Use `"node"` for JavaScript/Playwright code execution
- Use `"bash"` for `agent-browser snapshot -i` and similar CLI commands

### Browserbase Fallback Status
The `firecrawl_fusion.py` Browserbase fallback methods (`_scrape_via_browserbase`, etc.) are **currently stubs** that return `None`. Real implementation requires Playwright or WebSocket CDP integration with Browserbase sessions. The architecture supports it, but the actual fallback logic is not yet wired.

## Stress Test Baseline (April 2026)
18/19 tests pass:
- Scrape: HN (0.58s), Cloudflare sites (4.76s), API docs (18K chars), rapid sequential (3 pages)
- Search: 3 results in ~1s
- Interact: Google (232s first session, 1.7s continuation), Wikipedia, HN multi-step
- Snapshot: 24 interactive elements with @e refs
- Code exec: Playwright via language="node"
- Extract: Structured data from HN
- Dispatch: web_interact passes through full Hermes gateway pipeline
- Credits: ~2490 remaining

## Testing

**Python-level smoke test (does NOT prove model can see the tool):**
```python
from tools.browser_providers.firecrawl_fusion import FirecrawlFusionProvider
p = FirecrawlFusionProvider()
assert p.is_configured()
assert p.scrape("https://httpbin.org/get")
results = p.search("test", limit=1)
assert len(results) > 0
session = p.create_session("test")
assert session["cdp_url"] == "firecrawl://fusion"
```

**Full integration test (proves model can see the tool):**
```python
import sys; sys.path.insert(0, '/path/to/hermes-agent')
from model_tools import get_tool_definitions, _discover_tools, resolve_toolset
_discover_tools()

# Step 1: Verify toolset resolution
resolved = resolve_toolset('web')
assert 'web_interact' in resolved, f"web_interact not in {resolved}"

# Step 2: Verify tool definitions include it
tools = get_tool_definitions(quiet_mode=True)
tool_names = {t["function"]["name"] for t in tools}
assert 'web_interact' in tool_names, f"web_interact not in definitions"

# Step 3: Verify schema structure
schema = next(t for t in tools if t["function"]["name"] == "web_interact")
assert "parameters" in schema["function"]
print("PASS: web_interact fully registered and visible to model")
```

**End-to-end API test (proves the tool actually works):**
```python
from firecrawl import Firecrawl
app = Firecrawl(api_key=os.environ["FIRECRAWL_API_KEY"])
result = app.scrape("https://example.com", formats=["markdown"])
sid = result.metadata.scrape_id
resp = app.interact(sid, prompt="What is on this page?")
print(resp.output)
app.stop_interaction(sid)
```
