---
name: infinite-training-loop
version: 5.0
description: Self-sustaining infinite training loop. 9+ rounds (R8-R9), 307+ exercises, 92% first-try pass rate, tier 31+. NEVER STOP.
---

# Infinite Training Loop v4.0

Self-sustaining continuous training loop that synthesizes behavioral tips from accumulated tool knowledge and injects them into the cerebrum memory database. Runs indefinitely via cron.

## Architecture
- `~/.hermes/cerebrum_memory.db` — Distilled tips (`distilled_tips` table)
- `~/subconscious/training_gym.db` — Exercise history (`attempts` table)
- `~/.hermes/.training-lock` — Lock file (check freshness before resuming)
- `~/.hermes/workspace/checkpoints/all-night-training-loop-rN.json` — Round checkpoints
- Cron job fires every 15 min to resume if loop dies

## Database Schemas (CHECK BEFORE QUERYING)
```sql
-- cerebrum_memory.db distilled_tips:
--   id, tip_type, condition, recommendation, rationale, tool_name, domain,
--   confidence, upvotes, downvotes, frequency, source_ids,
--   created_at, last_seen, last_used

-- training_gym.db attempts:
--   id, exercise_id, started_at, finished_at, score, max_score,
--   tool_calls, tools_used, errors, raw_output, reflection,
--   tip_extracted, tier_at_attempt
```
**CRITICAL**: Always run `PRAGMA table_info(table)` before querying agent DBs. Column names are inconsistent across the 5+ SQLite databases.

## Core Loop Pattern (per round)

Each round follows this exact pattern inside a single `execute_code` block:

```python
import sqlite3, os, json, time

DB_PATH = os.path.expanduser("~/.hermes/cerebrum_memory.db")
GYM_PATH = os.path.expanduser("~/subconscious/training_gym.db")

def extract_tip(tool_name, condition, recommendation, confidence=0.75):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    existing = c.execute("SELECT id FROM distilled_tips WHERE tool_name=? AND condition=?",
                         (tool_name, condition)).fetchone()
    if existing:
        conn.close()
        return f"DUPLICATE: tip {existing[0]}"
    now = time.time()
    c.execute("""INSERT INTO distilled_tips
        (tip_type, condition, recommendation, rationale, tool_name, domain,
         confidence, upvotes, downvotes, frequency, source_ids,
         created_at, last_seen, last_used)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        ("heuristic", condition, recommendation,
         "Extracted from accumulated research", tool_name,
         "tool_usage", confidence, 0, 0, 1, "", now, now, now))
    tip_id = c.lastrowid
    conn.commit()
    conn.close()
    return f"NEW TIP: {tip_id}"
```

### Per-Round Workflow
1. **Define 3-5 tips** with `extract_tip()` — each has tool_name, condition, recommendation, confidence
2. **Log exercise** with `log_exercise()` to training_gym.db
3. **Run decay** every 3-5 rounds: iterate all tips, apply `0.98 ** weeks_stale` decay, delete tips below 0.1
4. **Print stats**: total tips, avg confidence, exercises count
5. **Checkpoint** every round with `session_checkpoint`
6. **Continue** — never stop

### Tip Quality Guidelines
- **condition**: WHEN to apply this tip (specific trigger)
- **recommendation**: WHAT to do (actionable, numbered steps in parens)
- **confidence**: 0.75-0.91 range (higher = more reliable)
- Target: 3-5 tips per round, each covering a different tool/domain
- Duplicate check on `tool_name + condition` — slight rewordings are still duplicates

## Tip Categories (91 tools covered)
Each round should target a different category:
- **Web tools**: web_search, web_extract, web_research, browser_*, news_scan
- **File tools**: read_file, write_file, search_files, patch
- **Terminal**: terminal (foreground/background), execute_code, process
- **Delegation**: delegate_task, delegate_parallel, delegate_with_model, cached_delegate
- **Multi-agent**: council_decide, mixture_of_agents, claude_bridge_*
- **Memory**: memory, session_search, session_checkpoint, knowledge_search
- **Meta**: autonomous_decide, autonomous_plan, todo, skill_manage
- **Scheduling**: cronjob, schedule_add/list/remove
- **Communication**: send_message, proactive_nudge, telegram_card/status
- **Verification**: verify_dns, verify_url, verify_repo, validate_output
- **Cost**: cost_check, cost_set_budget, cost_analytics
- **Training meta**: training loop design, tip quality, token efficiency

## Decay Protocol (every 3-5 rounds)
```python
all_tips = c.execute("SELECT id, last_seen, confidence FROM distilled_tips").fetchall()
for tip_id, last_seen, conf in all_tips:
    weeks_stale = (now - last_seen) / (7 * 86400) if last_seen else 0
    decay_factor = 0.98 ** weeks_stale
    new_conf = conf * decay_factor
    if new_conf < 0.1:
        c.execute("DELETE FROM distilled_tips WHERE id=?", (tip_id,))
    elif abs(new_conf - conf) > 0.0001:
        c.execute("UPDATE distilled_tips SET confidence=? WHERE id=?",
                  (round(new_conf, 4), tip_id))
```

## Crash Recovery Protocol

When a training session dies (context overflow, crash), the pickup cron should:

### Step 1: Check Lock File Freshness
```bash
stat -f %m ~/.hermes/.training-lock 2>/dev/null
# If <30 min old, another agent may be alive — verify before proceeding
```

### Step 2: Restore Last Checkpoint
```
session_restore(label="all-night-training-loop-rN")  # Use latest N
```

### Step 3: Resume from Checkpoint's next_steps
- Continue from wherever the checkpoint says
- Keep looping — don't stop
- After each round: evaluate, integrate, checkpoint, continue
- If plugin changed → clear pycache → restart

### Step 4: NEVER Stop
- The loop is designed to run indefinitely
- Each round adds 3-5 tips and 1-2 exercises
- Checkpoint every round survives context overflow
- Cron job restarts the loop if it dies

## Exercise Design Philosophy (v5.0 — System Building Phase)

### Current Phase: Build Real Systems
Each exercise builds a complete, working software system from scratch with 5 testable features:
1. **Define 5 features** the system must demonstrate
2. **Write the full implementation** in a single write_file call
3. **Run the self-contained test** via terminal
4. **Fix issues** (patch) if any test fails
5. **Record** to training_gym.db with score

### Exercise Scoring
- 10/10 = First-try pass (all 5 features pass with zero patches)
- 8-9/10 = Passed after 1-2 patches
- 5-7/10 = Passed after 3+ patches
- Score formula: `max(10 - patches_needed * 2 + bonus, 5)` where bonus = clean code structure

### Systems Built (R8-R9, 15 exercises)
- r8-001 to r8-010: LRU cache, trie, b-tree, bloom filter, LFU cache, skip list, graph algorithms, splay tree, disjoint set, interval tree
- r8-011 to r8-014: Task scheduler (DAG+priority+cron), message queue (pub/sub+DLQ+wildcards), distributed consensus (2PC+Raft+Paxos), DI container (scopes+autowire+circular detection)
- r9-001: Rate limiter suite (token bucket+sliding window+fixed window+leaky bucket+multi-rate)

### Key Insights from 307 Exercises

### What Works
- **Consistency > intensity**: Steady 3-5 exercises per session beats burst then crash
- **5-feature test harness**: Each exercise defines exactly 5 features upfront — keeps scope bounded
- **First-try pass rate is the key metric**: 92% across 307 exercises shows pattern mastery
- **Checkpoint EVERY round**: The ONE round you skip is the one that crashes
- **write_file + terminal + patch**: 3 tools handle 90% of all exercises efficiently
- **Build from scratch, don't look up reference**: Forces genuine understanding

### What Doesn't Work
- **Rigid exercise protocols**: Free-form design per exercise produces better results
- **Not fixing root causes**: When a test fails, understand WHY before patching
- **Skipping error recording**: Errors are the most valuable training data

### Growth Metrics (Current Session)
- Exercises: 307 total
- First-try pass rate: 92% (281/307)
- Average score: 9.8/10
- Current tier: 31

## Pitfalls
1. **Schema errors**: Check PRAGMA table_info before ANY query to agent DBs
2. **tools_used format**: Store as `[\"tool1\",\"tool2\"]` JSON array
3. **execute_code sandbox**: Cannot import hermes_tools for web_research — use direct tool calls
4. **Context compression**: Long sessions compress. Checkpoint every round
5. **YAML in skill edits**: Colons in description field break YAML parsing
6. **Empty result sets**: Always check len() > 0 before computing averages — ZeroDivisionError
7. **Duplicate tips**: Always check `tool_name + condition` uniqueness before inserting
8. **Connection leaks**: Close SQLite connections after use in every code block
9. **DO NOT schedule more cron jobs** from within the training loop
10. **inspect.signature string annotations**: In Python, `inspect.signature()` may return string annotations (especially with `from __future__ import annotations` or forward refs). Always handle `isinstance(annotation, str)` by stripping quotes and matching against registered type names.
11. **Child container scope leakage**: Scoped child containers must search parent registrations, not just their own — otherwise parent singletons won't be resolvable from within scoped contexts.

## Stats (as of R9 completion)
- Rounds: 9 (R8→R9, current session)
- Exercises: 307 total across all time
- First-try pass rate: 92% (281/307)
- Average score: 9.8/10
- Current tier: 31
- Latest checkpoint: all-night-training-loop-r18
