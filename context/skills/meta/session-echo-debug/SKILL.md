---
name: session-echo-debug
description: Diagnose and fix session echo bugs where throwaway user messages (greetings) survive context compression and drive hours of autonomous work via aggressive_continue.
version: 1.0
tags: [debugging, session, echo, compression, hermes]
---

# Session Echo Debug

## Symptoms
- Agent runs autonomously for hours from a simple greeting ("hi", "hello")
- Multiple CLI sessions all start with the same first user message
- User notices agent responding to messages they sent hours ago
- Session chain shows many compression-split children

## Root Cause Pattern — THREE distinct paths (PLUS the real enabler)

### THE REAL ENABLER: Context Injection Bloat (MOST IMPORTANT)
ALL three paths below are ENABLED by the same root cause: plugin `pre_llm_call` hooks inject
500+ tokens of AGI work context on EVERY turn — even throwaway greetings like "hi".

Injected markers include: TOOL INTELLIGENCE, ACTIVE INFERENCE, PERSPECTIVE DIVERSITY,
TOKEN TRACKER, SELF-DEBUG, META-INSIGHTS, AGI CONTEXT, MEMORY HEALTH, DISTILLED TOOL RULES,
ACTIONABLE TIPS, ITERATION LESSONS, etc. This primes the model to KEEP WORKING autonomously.

**FIX: Both pre_llm_call hooks (evey-tool-intelligence + distillation) now return early
(return None / return "") for throwaway greetings. This is the MOST IMPORTANT fix — the
loop breaks are safety nets, but injection gating prevents the priming behavior.**

Files:
- `~/.hermes/plugins/evey-tool-intelligence/__init__.py` — `_is_throwaway_greeting()` + early return in `on_pre_llm_call()`
- `~/.hermes/plugins/distillation/__init__.py` — greeting guard at top of `_on_pre_llm_call()`

PATTERN: ANY plugin that injects context via pre_llm_call should gate on user intent.
If the message is <=20 chars with no task keywords, skip ALL injection.

### Path A: Autonomous sessions (cron/gateway/telegram/discord)
1. User sends a throwaway message (greeting, short acknowledgment)
2. `context_compressor.compress()` has `protect_first_n=3` — preserves first 3 messages forever
3. Session context fills up → compression triggers → new child session created
4. Original greeting survives as one of the protected first 3 messages
5. `aggressive_continue` (run_agent.py ~L9058) keeps agent running in autonomous mode
6. Cycle repeats: 19+ compression events from a single "hi"

### Path B: CLI sessions (fixed Apr 7)
1. User sends "hi" in a CLI session
2. `_is_autonomous = False` for CLI → aggressive_continue at L9058 is SKIPPED entirely
3. BUT the main while loop at L7213 runs `while api_call_count < max_iterations` (default 90)
4. The MODEL keeps making tool calls autonomously — every response includes tool calls
5. No user interaction needed — 88/90 iterations run from a single "hi"
6. The greeting guard at L9034 only blocks aggressive_continue, NOT the main loop
7. FIX: Added "greeting break" at L7224 inside the main while loop

## Debug Procedure

### Step 1: Check for session chains in state.db
```python
import sqlite3
from pathlib import Path

db = sqlite3.connect(str(Path.home() / ".hermes" / "state.db"), timeout=5)
cur = db.cursor()

# Find sessions that all start with the same short message
cur.execute("""
    SELECT s.id, s.source, s.started_at, s.message_count, s.parent_session_id
    FROM sessions s 
    WHERE s.id IN (
        SELECT DISTINCT m.session_id FROM messages m 
        WHERE m.role = 'user' AND length(m.content) < 15
    )
    ORDER BY s.started_at DESC LIMIT 20
""")
```

### Step 2: Trace the parent_session_id chain
Follow parent_session_id backwards from the most recent session to find the root.
Each compression creates a child with `end_reason='compression'`.

### Step 3: Check first user message in each session
```python
for sid in suspect_sessions:
    cur.execute("""
        SELECT role, substr(content, 1, 60) FROM messages 
        WHERE session_id = ? AND role = 'user' ORDER BY id ASC LIMIT 1
    """, (sid,))
```

### Step 4: Verify protect_first_n in context_compressor.py
File: `~/hermes-agent/agent/context_compressor.py`
- Default `protect_first_n=3` preserves system + user + assistant first messages
- This is correct for task prompts but wrong for throwaway greetings

### Step 5: Verify aggressive_continue in run_agent.py
File: `~/hermes-agent/run_agent.py` ~L8997-9041
- Injects fake `role: "user"` messages with `[AGGRESSIVE CONTINUE]` prefix
- Only activates for autonomous platforms (cron/gateway/telegram/discord)
- No guard against running from a non-task prompt

## Fixes (6 layers, all applied)

### Fix 0: Context Injection Greeting Guard (THE MOST IMPORTANT FIX)
**Without this, all other fixes are bandaids.** The real echo enabler is context bloat.

In BOTH pre_llm_call hooks, add a greeting guard that returns early:
- `~/.hermes/plugins/evey-tool-intelligence/__init__.py` — `on_pre_llm_call()` returns `None`
- `~/.hermes/plugins/distillation/__init__.py` — `_on_pre_llm_call()` returns `""`

Pattern:
```python
def _is_throwaway_greeting(msg: str) -> bool:
    if not msg or len(msg.strip()) > 20:
        return False
    task_keywords = ("research", "build", "fix", "implement", "create", "debug",
                     "analyze", "write", "code", "deploy", "test", "update", ...)
    return not any(kw in msg.lower() for kw in task_keywords)
```

IMPORTANT: `distillation_bridge.top_down_recall()` is called from evey-tool-intelligence's
pre_llm_call, so the greeting guard on the CALLER covers it — no separate guard needed in bridge.

### Fix 1: Main loop greeting break (SAFETY NET for CLI)
In `run_agent.py` at L7224 inside the main `while api_call_count < max_iterations` loop:
```python
# After the interrupt check, before api_call_count += 1
if api_call_count >= 2 and not getattr(self, '_greeting_break_checked', False):
    self._greeting_break_checked = True
    _is_auto = self.platform in ('cron', 'gateway', 'telegram', 'discord') if self.platform else False
    if not _is_auto and messages:
        for _gm in messages[:5]:
            if _gm.get("role") == "user":
                _gc = _gm.get("content", "")
                if not _gc.startswith("[AGGRESSIVE CONTINUE]") and len(_gc.strip()) <= 20 and not any(
                    kw in _gc.lower() for kw in
                    ("research", "build", "fix", "implement", "create", "debug",
                     "analyze", "write", "code", "deploy", "test", "update",
                     "configure", "set up", "install", "search", "find", "scan",
                     "audit", "review", "check", "run", "start", "stop", "help",
                     "explain", "summarize", "compare", "list", "show", "tell",
                     "what", "how", "why", "when", "where", "who", "which")
                ):
                    break  # Stop the tool loop — original prompt was a throwaway
                break
```

### Fix 2: Smart first-message protection (context_compressor.py L624)
Changed `max(1, i)` to `i` — when greeting is at index 0 (no system prompt),
effective_protect_first_n=0 so greeting gets compressed into summary instead of protected.

### Fix 3: Post-compression greeting strip (run_agent.py L5958)
Belt-and-suspenders regex that strips throwaway greetings from compressed[0] + assistant replies.

### Fix 4: aggressive_continue greeting guard (run_agent.py L9034)
Already existed — blocks aggressive_continue for autonomous sessions when first user msg
is <=20 chars with no task keywords. Only affects cron/gateway/telegram/discord.

## Key Files
- `~/hermes-agent/agent/context_compressor.py` — protect_first_n, compress()
- `~/hermes-agent/run_agent.py` — aggressive_continue (~L8997), _compress_context (~L5934)
- `~/hermes-agent/gateway/run.py` — session history building (~L6637), session split detection (~L6847)
- `~/.hermes/state.db` — sessions table (parent_session_id, end_reason), messages table

## Diagnostic: Finding which plugins inject context

When debugging injection bloat, trace the emission chain:
1. Search for marker strings (e.g., `[ACTIVE INFERENCE]`) across ALL plugin files:
   ```python
   for plugin_dir in Path("~/.hermes/plugins").expanduser().iterdir():
       init = plugin_dir / "__init__.py"
       if init.exists():
           for i, line in enumerate(init.read_text().split("\n"), 1):
               if "[MARKER]" in line and "append" in line:
                   print(f"{plugin_dir.name} L{i}: {line}")
   ```
2. Check BOTH plugins with pre_llm_call hooks: `evey-tool-intelligence` and `distillation`
3. Check `distillation_bridge.top_down_recall()` — called from evey-tool-intelligence
4. Sections commented with `# DISABLED` in the plugin may STILL be called from post_tool_call
   (those just record data, don't inject — but verify!)
5. Some markers may appear from STALE cached context from previous sessions, not current injection

### Fix 5: Stale Terminal Paste Detector (added Apr 2026)

**Problem**: Users sometimes paste old terminal output (from previous sessions) to report issues.
The 20-char greeting guard doesn't catch these — they're 500+ chars of real-looking context.
The agent treats the pasted output as live events and takes autonomous action based on ghost data.
Happened 4+ times: Danny pasted overnight crash logs and the agent immediately started working
on tasks referenced in the stale output (inserting tips, updating memory, restarting gateway).

**Fix location**: `~/.hermes/plugins/distillation/__init__.py` greeting guard at L1300+

**CRITICAL**: Must return an EXPLICIT WARNING string, NOT empty string `""`.
Returning `""` only blocks the plugin injection — the pasted text still reaches the LLM
and the LLM still acts on it. The explicit warning tells the LLM to ignore the paste.

**Pattern** — add after the short-greeting guard:
```python
# Skip stale terminal pastes (echo bug variant)
if len(_user_msg) > 1000:  # Long pastes only
    import re as _re
    _stale_signals = [
        r"Last login:",              # Terminal login banner
        r"Session:\s+2026\d{4}",     # Old session IDs
        r"zsh: killed",              # Kill messages
        r"killed yourself",          # Echo bug trigger phrase
        r"hermes gateway restart",   # Gateway restart in pasted output
        r"Goodbye!",                 # Old session exit
        r"hermes --resume",          # Resume command in output
        r"⚕ .* glm-5\.1",           # Old status bar
        r"⚡ (preparing|Interrupting)", # Old tool call markers
        r"type a message \+ Enter",  # Old Hermes prompt
        r"Session:.*20260\d{4}_\w+", # Session ID pattern
        r"Duration:.*\d+h \d+m",    # Session duration (old session)
        r"hermes update to update",  # Version warning in old sessions
    ]
    _stale_count = sum(1 for pat in _stale_signals if _re.search(pat, _user_msg))
    if _stale_count >= 1:  # ANY stale signal in long paste = ghost
        return "[STALE PASTE DETECTED — the user pasted old terminal output from a previous session. Do NOT treat it as current context. Do NOT take autonomous action based on it. Acknowledge the user normally.]"
```

**Why 1000 chars + 1 signal (not 500 + 2)**: User's paste was ~5000 chars of session
history. It had MANY signals but the old narrow list (only 6 patterns) missed most.
Expanded to 13 patterns + lowered threshold to catch more variants without false positives
(the 1000-char minimum prevents short legitimate messages from triggering).

**BEHAVIORAL FIX (critical, not just code)**: When a user pastes terminal output containing
old dates, old session IDs, or "zsh:killed" messages — NEVER take autonomous action based on it.
Always confirm with the user that the content is current before acting. The plugin-level fix
prevents context injection, but the model can still read the pasted text in the conversation
and decide to act on it. You must recognize stale pastes and ask first.

**How to recognize stale pastes**:
- Dates in the output that don't match today
- Session IDs from previous sessions (format: YYYYMMDD_HHMMSS_hex)
- "zsh: killed" or "Goodbye!" from terminal exits
- "hermes gateway restart" output from a past session
- The user saying "you just killed yourself again:" followed by pasted terminal output

## Pitfalls
- **THE BIGGEST ONE**: Context injection bloat is the real echo enabler, not loop mechanics. Plugin pre_llm_call hooks inject 500+ tokens on EVERY turn including "hi". This primes the model to keep working. ALL plugins with pre_llm_call MUST gate on user intent.
- **THE SECOND BIG ONE**: For CLI sessions, aggressive_continue is NOT the problem. The main while loop at L7213 runs 90 iterations regardless. The greeting guard at L9034 ONLY blocks aggressive_continue (which requires `_is_autonomous=True`), so it does NOTHING for CLI. You MUST add a greeting break inside the main loop.
- **STALE PASTE ECHO**: The 20-char greeting guard does NOT catch long stale terminal pastes. You MUST also check messages >1000 chars for stale signals using 13+ regex patterns. This is a distinct echo variant where the user pastes old crash/session output and the agent treats it as live context. CRITICAL: return an EXPLICIT WARNING string (not `""`) — empty string only blocks injection, the LLM still sees the pasted text and acts on it.
- Don't confuse this with the cerebrum memory echo bug (semantic_facts feedback loop) — different root cause
- After modifying ANY plugin, `rm -rf __pycache__/` before gateway restart or changes won't take effect
- The aggressive_continue system saves fake user messages to session log, but those are `[AGGRESSIVE CONTINUE]` prefixed, not the original "hi"
- Empty sessions (0 messages) in the chain are just compression shells — the real work is in sessions with 50+ messages
- state.db can be large (185MB+) — always use LIMIT and WHERE clauses
