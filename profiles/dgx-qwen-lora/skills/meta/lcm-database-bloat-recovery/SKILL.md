---
name: lcm-database-bloat-recovery
description: Recover from and prevent LCM (Long Context Memory) SQLite database bloat that causes "database is locked" cascades, compressor failures, and context-size-exceeded API errors. The LCM is the storage substrate behind context compression — when it grows unbounded, everything above it breaks.
version: 1.0
created: 2026-04-27
tags: [lcm, sqlite, compression, bloat, database-locked, context]
---

# LCM Database Bloat Recovery

## Trigger

Use this skill when ANY of these symptoms appear:
- "database is locked" errors cascading across multiple API calls
- Context-size-exceeded errors from the API ("context size exceeded 2097152" on Kimi, etc.)
- Compressor failing silently while messages keep growing
- `~/.hermes/lcm.db` file is >100MB or contains >20K messages
- The agent enters a death spiral where every turn makes context worse
- Session won't accept new tool calls but isn't truly stuck

These symptoms compound: locked DB → failed compression → growing context → locked DB.

## What Is LCM and Why It Bloats

LCM = Long Context Memory. It's a SQLite database at `~/.hermes/lcm.db` with two key tables:
- `messages` — every conversation message (role, content, timestamp, tokens, session_id)
- `summary_nodes` — compressed summary trees from prior compressions

LCM has NO built-in retention policy. Every message from every session accumulates. Multi-day usage can produce 30K+ messages / 200+ summary nodes. At that size:
1. Concurrent reads (compressor) and writes (new messages) collide → SQLite WAL lock contention
2. The compressor's read queries time out → silent compression failure
3. In-memory message list keeps growing (compressor was supposed to shrink it)
4. Eventually exceeds API context limit → hard failure

**Verify the schema before querying** — the messages table uses `store_id` (not `id`) as primary key, and `summary_nodes` uses `node_id`. Use `rowid` for safe portable queries.

## Diagnosis (run in order)

### 1. Check LCM size
```bash
ls -lh ~/.hermes/lcm.db ~/.hermes/lcm.db-wal 2>/dev/null
```
Healthy: <30MB. Bloated: >50MB. Critical: >100MB.

### 2. Count rows
```python
import sqlite3
from pathlib import Path
conn = sqlite3.connect(str(Path.home() / '.hermes/lcm.db'))
cur = conn.cursor()
cur.execute('SELECT COUNT(*) FROM messages'); msgs = cur.fetchone()[0]
cur.execute('SELECT COUNT(*) FROM summary_nodes'); nodes = cur.fetchone()[0]
cur.execute('SELECT MIN(timestamp), MAX(timestamp) FROM messages'); min_ts, max_ts = cur.fetchone()
print(f'{msgs} messages, {nodes} nodes, span {min_ts} to {max_ts}')
conn.close()
```
Healthy: <10K messages. Bloated: >20K. Critical: >30K.

### 3. Check for lock holders
```bash
lsof ~/.hermes/lcm.db 2>/dev/null | head -20
ps aux | grep -i "hermes" | grep -v grep
```
Multiple Hermes processes holding LCM open = zombie sessions. Old PIDs (high CPU time, no recent activity) are zombies blocking the lock.

## Recovery Steps

### Step 1: Kill zombie Hermes processes (if any)
```bash
# Identify zombie: high CPU time, started long ago, not the current session
ps aux | grep "dannygomez.*hermes" | grep -v grep
kill -TERM <zombie_pid>
sleep 1
# If still running:
kill -KILL <zombie_pid>
```
**WARNING:** Don't kill your active session. Compare PIDs with the one you're running in.

### Step 2: Emergency LCM trim (use rowid, NOT id)
```python
import sqlite3
from pathlib import Path

lcm = Path.home() / '.hermes/lcm.db'
conn = sqlite3.connect(str(lcm), timeout=10)
cur = conn.cursor()

# CRITICAL: messages.id does NOT exist. Use rowid.
cur.execute('''
    DELETE FROM messages
    WHERE rowid NOT IN (
        SELECT rowid FROM messages ORDER BY timestamp DESC LIMIT 5000
    )
''')
deleted_msgs = cur.rowcount

cur.execute('''
    DELETE FROM summary_nodes
    WHERE rowid NOT IN (
        SELECT rowid FROM summary_nodes ORDER BY created_at DESC LIMIT 50
    )
''')
deleted_nodes = cur.rowcount

conn.commit()
cur.execute('VACUUM')  # Reclaim disk space
conn.commit()
conn.close()

print(f'Deleted {deleted_msgs} messages, {deleted_nodes} nodes')
```

### Step 3: Clear stale WAL/shm files
```bash
cd ~/.hermes
rm -f lcm.db-wal lcm.db-shm
rm -f *.lock
```
Only safe to do this when no Hermes process is actively writing — verify with `lsof` first.

### Step 4: Verify recovery
```python
# Run Step 2's count query again — should show <=5000 messages, <=50 nodes
# File size should drop dramatically after VACUUM
```

## Permanent Prevention (the real fix)

Emergency trim alone is a band-aid. To prevent recurrence, harden the compressor itself.

### A. Add hard limits to ContextCompressor

In `~/hermes-agent/agent/context_compressor.py`, add to `__init__`:
```python
# Hard limits to prevent LCM/state bloat
self._max_lcm_messages: int = 10000
self._max_lcm_nodes: int = 100
self._lcm_cleanup_interval: int = 50  # Compressions between LCM cleanups
```

### B. Add `_cleanup_lcm_storage()` method

Insert before `_generate_summary()`:
```python
def _cleanup_lcm_storage(self) -> None:
    """Trim LCM database to prevent unbounded growth. Non-blocking."""
    try:
        import sqlite3
        from pathlib import Path
        lcm_db = Path.home() / ".hermes/lcm.db"
        if not lcm_db.exists():
            return
        conn = sqlite3.connect(str(lcm_db), timeout=5)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM messages")
        msg_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM summary_nodes")
        node_count = cur.fetchone()[0]
        trimmed = False
        if msg_count > self._max_lcm_messages:
            cur.execute("""DELETE FROM messages WHERE rowid NOT IN
                (SELECT rowid FROM messages ORDER BY timestamp DESC LIMIT ?)""",
                (self._max_lcm_messages,))
            trimmed = True
        if node_count > self._max_lcm_nodes:
            cur.execute("""DELETE FROM summary_nodes WHERE rowid NOT IN
                (SELECT rowid FROM summary_nodes ORDER BY created_at DESC LIMIT ?)""",
                (self._max_lcm_nodes,))
            trimmed = True
        if trimmed:
            conn.commit()
            cur.execute("VACUUM")
            conn.commit()
        conn.close()
    except Exception as e:
        logger.warning("LCM cleanup failed (non-critical): %s", e)
```

### C. Hook cleanup into compress()

In the `compress()` method, after `self.compression_count += 1`:
```python
if self.compression_count % self._lcm_cleanup_interval == 0:
    self._cleanup_lcm_storage()
```

### D. Compression reentrancy guard (prevents recursive compression)

When a tool result pushes context over threshold *during* an active compression, the agent loop can attempt to compress again before the first compression finishes. This causes "database is locked" cascades. Add a reentrancy lock in `run_agent.py`:

```python
if self.compression_enabled and _compressor.should_compress(_real_tokens):
    # Reentrancy guard: prevent recursive compression during active compression
    if getattr(self, '_compression_in_progress', False):
        logger.warning("Compression skipped: already in progress")
    else:
        self._compression_in_progress = True
        try:
            self._safe_print("  ⟳ compacting context…")
            messages, active_system_prompt = self._compress_context(
                messages, system_message,
                approx_tokens=self.context_compressor.last_prompt_tokens,
                task_id=effective_task_id,
            )
            conversation_history = None
        finally:
            self._compression_in_progress = False
```

### E. Hard message limit (force compression on long sessions)

At the top of `compress()`, delegate to a separate `_do_compress()` to avoid infinite recursion:

```python
def compress(self, messages, current_tokens=None, focus_topic=None):
    n_messages = len(messages)
    _HARD_MESSAGE_LIMIT = 500
    if n_messages > _HARD_MESSAGE_LIMIT and not self.should_compress():
        if not self.quiet_mode:
            logger.warning("Forcing compression: %d messages exceeds hard limit", n_messages)
        orig_threshold = self.threshold_tokens
        self.threshold_tokens = 1  # Force should_compress=True
        try:
            return self._do_compress(messages, current_tokens, focus_topic)
        finally:
            self.threshold_tokens = orig_threshold
    return self._do_compress(messages, current_tokens, focus_topic)

def _do_compress(self, messages, current_tokens=None, focus_topic=None):
    """Internal compression implementation — never call compress() from here."""
    n_messages = len(messages)
    _min_for_compress = self.protect_first_n + 3 + 1
    if n_messages <= _min_for_compress:
        return messages
    # ... rest of compression logic ...
```

**CRITICAL:** Never call `self.compress()` from inside `compress()` — this creates infinite recursion when the hard limit fires. Always extract the actual compression logic into `_do_compress()` and have `compress()` be a thin wrapper that only handles the threshold override.

### F. Memory bloat monitor with auto-trim (prevents unbounded memory file growth)

The agent's memory files (`MEMORY.md`, `USER.md`) have hard size limits. When they hit the wall, context injection fails silently. Wire a bloat monitor into every turn in `run_agent.py`:

```python
# Memory bloat monitor check with auto-trim
try:
    from agent.memory_bloat_monitor import check_memory_bloat
    _bloat_alert = check_memory_bloat(self._memory_store, auto_trim=True)
    if _bloat_alert:
        logger.warning(_bloat_alert)
        # Emit critical bloat alerts to user
        if "[BLOAT ALERT]" in _bloat_alert:
            self._emit_status(f"⚠ {_bloat_alert}")
except Exception:
    pass
```

The `check_memory_bloat(auto_trim=True)` function:
1. Checks `MEMORY.md` and `USER.md` size against thresholds
2. If critical: automatically removes oldest entries to 90% of limit
3. Returns alert string for logging/status emission

Thresholds (configurable in `BloatThresholds`):
- `MEMORY.md`: warn at 2000 chars, trim at 2500
- `USER.md`: warn at 1200 chars, trim at 1375

This prevents the "USER.md approaching limit: 1348/1375" warning from becoming a hard failure.

### G. tiktoken-accurate token estimation

Replace rough `len(text)//4` estimation with tiktoken in `agent/adaptive_injection.py` and `agent/model_metadata.py`:

```python
# In adaptive_injection.py — lazy-loaded, thread-safe
_tiktoken_encoder = None
_tiktoken_lock = threading.Lock()

def _get_encoder():
    global _tiktoken_encoder
    if _tiktoken_encoder is not None:
        return _tiktoken_encoder
    with _tiktoken_lock:
        if _tiktoken_encoder is not None:
            return _tiktoken_encoder
        try:
            import tiktoken
            _tiktoken_encoder = tiktoken.get_encoding("cl100k_base")
        except Exception:
            _tiktoken_encoder = False
    return _tiktoken_encoder

def estimate_tokens(text: str) -> int:
    if not text:
        return 0
    enc = _get_encoder()
    if enc is False:
        return max(1, len(text) // 4)
    try:
        return len(enc.encode(text))
    except Exception:
        return max(1, len(text) // 4)
```

This prevents the compressor from miscalculating context pressure by 10-20%.

### F. Daily LCM compact cron job

Create a cron job that runs at 3 AM:
```python
import sqlite3
from pathlib import Path
lcm = Path.home() / '.hermes/lcm.db'
conn = sqlite3.connect(str(lcm), timeout=10)
cur = conn.cursor()
cur.execute('''DELETE FROM messages WHERE rowid NOT IN
    (SELECT rowid FROM messages ORDER BY timestamp DESC LIMIT 8000)''')
cur.execute('''DELETE FROM summary_nodes WHERE rowid NOT IN
    (SELECT rowid FROM summary_nodes ORDER BY created_at DESC LIMIT 80)''')
conn.commit()
cur.execute('VACUUM')
conn.commit()
conn.close()
```

## Pitfalls

- **`messages.id` does not exist.** The schema uses `store_id` as PK, but use `rowid` for portable queries. `DELETE FROM messages WHERE id NOT IN (...)` will throw `OperationalError: no such column: id`.
- **VACUUM is mandatory after large DELETEs.** Without it, the file size stays the same — SQLite just marks pages as free internally.
- **Don't delete WAL/shm files while a process is writing.** They contain uncommitted transactions. Always `lsof` first or shut down processes.
- **The LCM cleanup must be non-blocking.** Wrap in try/except — never let LCM cleanup failures break compression.
- **Distinguish LCM bloat from state.db bloat.** state.db (`~/.hermes/state.db`) holds session metadata and message logs. LCM holds the compression substrate. Both can bloat independently. Check both.
- **Don't trust file size after compression.** A small in-memory context with a large LCM file means the compressor is working but the substrate is bloated. Check row counts, not just bytes.
- **The hard message limit (500) catches scenarios where token counting underestimates.** Even if estimated tokens look fine, 500+ messages is always a sign something is wrong.

## Verification After Fix

```python
# 1. LCM is clean
import sqlite3
from pathlib import Path
conn = sqlite3.connect(str(Path.home() / '.hermes/lcm.db'))
cur = conn.cursor()
cur.execute('SELECT COUNT(*) FROM messages'); print(f'msgs: {cur.fetchone()[0]}')
cur.execute('SELECT COUNT(*) FROM summary_nodes'); print(f'nodes: {cur.fetchone()[0]}')
conn.close()

# 2. Compressor has new limits
from agent.context_compressor import ContextCompressor
comp = ContextCompressor('kimi-for-coding', quiet_mode=True)
assert hasattr(comp, '_max_lcm_messages')
assert hasattr(comp, '_cleanup_lcm_storage')

# 3. Cron job is registered
# (use cronjob tool to list)
```

## Related Skills

- `context-quality-guard` — when to compress (threshold tuning) — this skill is about WHAT to do when compression itself is failing because the substrate is bloated
- `session-immortality` — broader session continuity, includes compression config tuning
- `context-injection-audit` — per-turn pre_llm_call hook bloat (different layer)
- `cortex-flywheel-api-reconcile` — Cortex Postgres DB issues (different DB)
- `continuous-health-monitor` — general daemon health monitoring, complementary to LCM-specific checks
