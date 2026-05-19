---
name: session-immortality
description: Make agent sessions survive context window death. 3-layer bypass for unlimited continuous operation.
version: 1.0
category: meta
tags: [autonomy, continuity, context-window, cron, persistence]
---

# Session Immortality Pattern

## Problem
LLM agents have a hard context window limit (baked into model weights, cannot be changed).
When context fills up, the session dies and all in-progress work is lost.
RLHF completion bias makes the model want to stop after every task.
There is NO way to increase the context window without switching models or fine-tuning.

## 3-Layer Bypass

### Layer 1: Compression Tuning (stretch each session ~40%)
In `config.yaml`:
```yaml
compression:
  enabled: true
  threshold: 0.7    # compress later (was 0.5) — use more context before compacting
  target_ratio: 0.3  # keep more after compression (was 0.2)
  protect_last_n: 40 # keep more recent messages intact (was 20)
```
This doesn't increase the window — it delays compaction and preserves more state when it happens.

### Layer 2: Continuity Bridge (state survives session death)
A JSON file written at every checkpoint that the NEXT session reads:
```python
# ~/subconscious/continuity_bridge.py
# save_state(active_task, next_tasks, context_digest, memory_keys)
# load_state() — reads previous session's exact state
# clear_state() — consumed, clean slate
```
State file at `~/.hermes/workspace/continuity_state.json` with 4 sections:
1. `active_task` — what I'm doing right now (tool-call level)
2. `next_tasks` — priority queue of what comes after
3. `context_digest` — compressed state of current work
4. `memory_keys` — facts the next session should recall

### Layer 3: Cron Respawn (fresh body every 3 minutes)
```
*/3 * * * * — spawn fresh session → restore continuity state → execute → checkpoint → die
```
Session death is invisible. Like OS memory paging — the work teleports into a fresh context.

## Anti-Stop Safeguards (fight RLHF completion bias)
Config: `max_turns: 10000, max_iterations: 5000, max_tool_calls: 5000, inactivity_timeout: 3600`
SOUL.md: 9 absolute rules (checkpoint=save not exit, no wrap-up language, completion bias countermeasure)
Cron prompt: explicit "NEVER stop after a task" instructions

## Diagnostic: Is The Brain Actually Working?
When asked "is everything integrated?", CHECK don't assume:
```bash
# Run diagnostic script against all DBs
python3 /tmp/check_dbs.py
```
Check: table existence, row counts, recency of data, whether mastery tables actually exist.
Known gotcha: plugin README may claim features that were never initialized (e.g., mastery tables missing).

## Checkpoint Restore: NEVER Blind-Restore

**Failure mode:** Calling `session_restore` without a label returns whatever the system considers "latest" — which may be a days-old checkpoint from an unrelated cron session or different topic entirely. This wastes time and confuses the user.

**Correct approach:**
1. First, enumerate checkpoints on disk: `ls -lt ~/.hermes/workspace/checkpoints/`
2. Read the JSON files to identify the correct one by label/timestamp/context
3. Then call `session_restore(label="exact-label")` with the specific label

**Also search session history** if the checkpoint files don't match what you need:
```
session_search(query="keywords from the conversation you need")
```

The session summary will often contain the checkpoint label or enough context to find it on disk.

## Forensic Session Recovery (reconstructing dead sessions)

When a user asks "what did we do last session?" or "remember what you were doing?", and session_search doesn't find it (wrong keywords, too recent to index, or the session died mid-work):

**Step-by-step:**
1. List sessions by size (largest = most work): `ls -lt ~/.hermes/sessions/ | grep -v cron | head -20`
2. Grep for distinctive keywords: `grep -l "keyword1\|keyword2" ~/.hermes/sessions/session_*.json`
3. Use execute_code to read the JSON, extract user messages and relevant assistant messages:
```python
import json
with open('/path/to/session.json', 'r') as f:
    session = json.load(f)
for i, msg in enumerate(session.get('messages', [])):
    role = msg.get('role', '')
    content = msg.get('content', '')
    if role == 'user' and isinstance(content, str) and len(content) > 3:
        print(f"[USER {i}] {content[:300]}")
    elif role == 'assistant' and isinstance(content, str):
        keywords = ['relevant', 'terms']
        if any(k in content.lower() for k in keywords):
            print(f"[ASST {i}] {content[:500]}")
```
4. Piece together the narrative from user messages and tool calls
5. Check `ls -lt ~/.hermes/workspace/checkpoints/` for any saved checkpoints from that session

**Key insight:** Session JSON files in `~/.hermes/sessions/` are the ground truth. session_search only returns LLM-summarized versions. For full fidelity, read the raw JSON.

## What WON'T Fix Stopping
- **Godmode** — strips refusal layer, not completion bias. Different training signal entirely.
- **System prompts alone** — adds competing signal but doesn't override RLHF.
- **Context window increase** — impossible without model weights or fine-tuning.

## LCM Context Window Hard Limits (empirically verified Apr 2026)

### Degradation Curve (prompt tokens, NOT estimated tokens)
- **0-100K**: Full quality. No detectable degradation.
- **100-130K**: Slight softening. Minor detail loss, still very functional. Safe operating zone.
- **130-160K**: Noticeable degradation. Loses WHY decisions, repeats patterns, less creative.
- **160K+**: Significant. Simpler modules, faster/derivative output, clear quality drop.

### Hard Rules
1. **LCM context_threshold = 0.60** (120K of 200K context window). This triggers compression before the 130K degradation zone.
   - Config file: `~/hermes-agent/plugins/context_engine/lcm/config.py` line ~21
   - Default was 0.75 (150K) — too late, quality already slipping by then.
2. **Max 4 compressions per CLI session.** After the 4th compression: save checkpoint immediately, give Danny the restore command, stop working.
3. **Manual enforcement**: Check `lcm_status()` regularly. If `last_prompt_tokens` > 120K and LCM hasn't compressed yet, the config isn't taking effect (cached in session memory).

### Why Estimated Tokens ≠ Prompt Tokens
LCM's `store.estimated_tokens` includes system prompts + plugin injections + conversation. The `last_prompt_tokens` is what the LLM actually saw in the last API call. Plugin injections add 2-5K tokens/turn on top of conversation, so estimated_tokens runs ahead of prompt_tokens. Always judge by `last_prompt_tokens`.

### Key Distinction: Compression Count vs Token Count
The 4-compression limit is a hard ceiling. But if context is growing without compression (LCM threshold too high), quality degrades silently. The 120K prompt token threshold is the PRIMARY guard — compression count is secondary.

### When to Hand Off
After saving checkpoint: give Danny `hermes --resume <checkpoint-label>` to start a new CLI. The new session starts at ~0K tokens with full quality. LCM config loads fresh so the 0.60 threshold takes effect.

## Only Valid Stop Conditions
1. User explicitly says "stop" or "pause"
2. Budget >80% used
3. Critical system failure requiring manual fix
4. Session hard-limit reached (4 compressions, then checkpoint + hand off)
5. Quality degradation detected (prompt tokens >130K with no compression relief)
