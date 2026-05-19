# DGX Hermes Sync vs Async Patterns - May 16 2026

## Problem

When wrapping `run_agent.main()` in a daemon loop, multiple async/sync boundary errors occur:

1. `TypeError: object NoneType can't be used in 'await' expression` — caused by wrapping `await main()` inside `asyncio.run()`
2. `TypeError: An asyncio.Future, a coroutine or an awaitable is required` — caused by calling `asyncio.run()` from within an already-running event loop
3. `RuntimeError: asyncio.run() cannot be called from a running event loop` — when trying to nest event loops

## Root Cause

`run_agent.main()` is already an `async def` function. The correct usage depends on context:

| Context | Correct Pattern | Wrong Pattern |
|---------|----------------|---------------|
| Top-level script | `asyncio.run(main(...))` | `await main(...)` (no event loop) |
| Inside async function | `await main(...)` | `asyncio.run(main(...))` |
| ThreadPoolExecutor | `asyncio.run(main(...))` in thread | `await` in non-async thread |
| Already running loop | `await main(...)` | `asyncio.run(main(...))` |

## Working Daemon Pattern

```python
#!/usr/bin/env python3
import asyncio
import json
from datetime import datetime
from run_agent import main  # main is async def

async def daemon_loop():
    """Async daemon - just await main() directly."""
    while True:
        try:
            # ... read request from queue ...
            
            # CORRECT: main() is async, we're in async context
            await main(
                query=query,
                model="/data/models/Qwen3.6-27B-Uncensored",
                api_key="not-needed",
                base_url="http://localhost:8000/v1",
                max_turns=10,
                verbose=True
            )
            
            # CORRECT: use asyncio.sleep in async context
            await asyncio.sleep(5)
            
        except Exception as e:
            print(f"[{datetime.now()}] Error: {e}")
            await asyncio.sleep(10)

if __name__ == "__main__":
    # CORRECT: top-level entry point uses asyncio.run()
    asyncio.run(daemon_loop())
```

## Broken Pattern (What NOT to Do)

```python
# WRONG: This causes TypeError
def run_sync(query, model, ...):
    loop = asyncio.get_event_loop()
    if loop.is_running():
        # Already in async context - just await!
        # But we're in a sync function...
        return asyncio.run(main(...))  # ❌ RuntimeError!
    else:
        return loop.run_until_complete(main(...))

# WRONG: Nested asyncio.run
def daemon_loop():
    while True:
        # main() returns None (it runs and prints)
        # asyncio.run() on a non-coroutine causes TypeError
        result = asyncio.run(main(...))  # ❌ TypeError!
```

## Key Rules

1. **If you're inside `async def`**: Use `await main(...)` directly
2. **If you're at top level**: Use `asyncio.run(main(...))`
3. **Never nest `asyncio.run()`**: Can't call from running loop
4. **`main()` returns None**: Don't try to capture return value for logic
5. **Use `await asyncio.sleep()` in async context**: Not `time.sleep()`

## systemd Service Context

When running under systemd with `Type=simple`, the process starts fresh (no existing event loop), so `asyncio.run(daemon_loop())` at top level is correct.

## Verification

```bash
# Check daemon is processing without TypeError
sudo journalctl -u hermes-dgx-daemon.service -f | grep -E "Error|TypeError|completed"

# Should see:
# - "✅ Request X completed" 
# - No "TypeError: object NoneType" messages
# - No "RuntimeError: cannot be called from a running event loop"
```
