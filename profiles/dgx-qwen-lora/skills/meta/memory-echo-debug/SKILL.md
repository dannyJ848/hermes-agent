---
name: memory-echo-debug
description: Diagnose and fix memory echo/feedback loops where the agent keeps reverting to the same topic across sessions due to its own responses being stored as high-trust facts.
version: 1.0
tags: [debugging, memory, cerebrum, feedback-loop]
---

# Memory Echo Bug Debugging

## Symptoms
- Agent keeps bringing up the same topic unprovoked across multiple sessions
- Topic is usually a transient system state (running processes, session status, etc.)
- Gets worse over time (more sessions = stronger echo)

## Root Cause Pattern
A feedback loop in the Cerebrum memory consolidation pipeline:

1. Agent answers a question about system state (e.g., "is the other session running?")
2. Response stored as `semantic_fact` with trust 0.5-0.7 (via `score_salience()` + `extract_facts()`)
3. Next session: `prefetch_all()` in `run_agent.py` line ~6873 recalls facts matching user message keywords
4. Recalled fact injected as `[Recalled Context]` system message
5. Model sees the recalled context → talks about the same topic again
6. New response stored AGAIN, trust boosted +0.05 per consolidation cycle (caps at 1.0)
7. Higher trust = higher recall priority = stronger echo

## Debug Steps

### 1. Confirm the echo source
```python
import sqlite3, os
db = sqlite3.connect(os.path.expanduser("~/.hermes/cerebrum_memory.db"))
# Search for facts containing the echoed topic
rows = db.execute("""
    SELECT id, content, trust, source, created_at 
    FROM semantic_facts 
    WHERE content LIKE '%<echo_topic>%'
    ORDER BY trust DESC
""").fetchall()
for r in rows:
    print(f"ID={r[0]}, trust={r[2]:.2f}, source={r[3]}")
    print(f"  {r[1][:150]}")
```

### 2. Trace the recall injection path
- `run_agent.py` line ~6873: `self._memory_manager.prefetch_all(user_message)`
- `agent/memory_manager.py` line 140: `prefetch_all()` calls each provider's `prefetch()`
- Cerebrum provider's `prefetch()` queries `semantic_facts` by relevance to user message
- Results injected as `[Recalled Context — use this knowledge when reasoning]`

### 3. Check the consolidation pipeline
- `plugins/memory/cerebrum/consolidation.py`:
  - `score_salience()` — determines if content is "important" (base 0.3, boosted by patterns)
  - `extract_facts()` — extracts standalone facts from content
  - `ConsolidationPipeline.consolidate()` — promotes episodic items to semantic if salience >= 0.5
- `plugins/memory/cerebrum/layers.py` line ~488: duplicate facts get trust +0.05 (caps at 1.0)

### 4. Delete echo facts
```python
ids_to_delete = [<found_ids>]
for fid in ids_to_delete:
    db.execute("DELETE FROM semantic_facts WHERE id = ?", (fid,))
    db.execute("DELETE FROM fact_entities WHERE fact_id = ?", (fid,))
db.commit()
```

### 5. Add ephemeral-state filter (prevent recurrence)
In `consolidation.py`, add patterns that detect transient state:

```python
_EPHEMERAL_STATE_PATTERNS = [
    re.compile(r'\b(?:other\s+)?session\b.*(?:running|alive|dead|down|UP|PID)', re.I),
    re.compile(r'\bPID\s*\d+', re.I),
    re.compile(r'\b(?:gateway|daemon|brain|cron)\b.*(?:UP|down|running|alive|dead|started)', re.I),
    # Add more patterns specific to the echo topic
]

def _is_ephemeral_state(content):
    return any(p.search(content) for p in _EPHEMERAL_STATE_PATTERNS)
```

Then patch `score_salience()` to return 0.10 for ephemeral content (below 0.5 consolidation threshold), and `extract_facts()` to return `[]` for ephemeral content.

## Key Files
- `~/hermes-agent/run_agent.py` — recall injection at line ~6873
- `~/hermes-agent/agent/memory_manager.py` — `prefetch_all()` at line 140
- `~/hermes-agent/plugins/memory/cerebrum/provider.py` — `sync_turn()` at line 329
- `~/hermes-agent/plugins/memory/cerebrum/consolidation.py` — `score_salience()`, `extract_facts()`
- `~/hermes-agent/plugins/memory/cerebrum/layers.py` — `SemanticStore.consolidate()` at line ~470
- `~/.hermes/cerebrum_memory.db` — `semantic_facts` table

## Variant: Self-Utterance Echo (Repetition Bug)

A different flavor of echo where the agent's OWN phrasing gets stored as facts,
then recalled next turn, priming the model to repeat the same sentences.

### Symptoms
- Agent narrates/explains the same thing twice in a row (e.g., "Now I see the problem..." followed by "Right — the problem is...")
- Repetition gets worse as more context accumulates
- The repeated phrases appear in the [Recalled Context] system injection

### Root Cause
Same pipeline, but instead of session-state, it's agent self-descriptions:
1. Agent says "So to answer your question honestly: 1. screencapture takes screenshots..."
2. This gets stored as semantic_fact (agent utterance treated as "knowledge")
3. Next turn: recalled context injects it
4. Model sees its own prior phrasing → unconsciously mirrors/repeats it

### Diagnosis Query
```sql
-- Find agent self-utterances stored as facts
SELECT rowid, content, trust FROM semantic_facts
WHERE content LIKE 'Agent:%'
   OR content LIKE 'So to answer%'
   OR content LIKE 'Now I see%'
   OR content LIKE 'Let me%'
   OR content LIKE 'Here''s what%'
   OR content LIKE '%screencapture%';
```

### Cleanup (when DB locked by gateway)
```bash
# Gateway locks cerebrum_memory.db. Use busy timeout:
sqlite3 -cmd ".timeout 5000" ~/.hermes/cerebrum_memory.db \
  "DELETE FROM semantic_facts WHERE content LIKE '%<echo_phrase>%'; SELECT changes();"
```

### Prevention
The `_is_ephemeral_state()` filter in consolidation.py catches process/session state,
but NOT agent self-descriptions. To block those too, add patterns like:
```python
re.compile(r'^Agent:', re.I),           # Agent responses stored as facts
re.compile(r'^So to answer', re.I),     # Common agent hedging
re.compile(r'^Now I see', re.I),        # Common agent narration
re.compile(r'^Let me', re.I),           # Common agent preamble
```
Or better: in `extract_facts()`, skip content where source == "agent" and content
starts with common agent preamble patterns.

## Pitfalls
- Don't just delete the facts — fix the consolidation filter too, or the echo will recur
- The trust boosting mechanism (+0.05 per consolidation) means the echo gets STRONGER over time
- Check BOTH `semantic_facts` AND `fact_entities` when purging (foreign key)
- The ephemeral patterns must be broad enough to catch variations but narrow enough to not block real knowledge
- Agent-source facts about system state are almost always ephemeral — user-source facts about preferences are almost always durable
- When cerebrum DB is locked (gateway holds it), use `sqlite3 -cmd ".timeout 5000"` for write access
- Agent self-utterances ("So to answer...", "Now I see...") are a DIFFERENT echo pattern than session-state — both need filtering
