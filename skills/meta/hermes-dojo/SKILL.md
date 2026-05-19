---
name: hermes-dojo
description: >
  Continuous self-improvement system. Analyzes past sessions for recurring failures
  and skill gaps, then creates or patches skills and runs self-evolution to fix them.
  Inspired by Yonkoo11/hermes-dojo. Use when reviewing agent performance or
  identifying improvement opportunities.
version: 1.0.0
metadata:
  author: hermes
  hermes:
    tags: [self-improvement, analytics, meta-agent, skills]
    category: meta
    requires_toolsets: [terminal]
---

## Agent Init Debugging Pattern
When tools silently fail to register at runtime:
1. **File-based diagnostics first**: Gateway logger.info may not reach any log file for agent init. Use `open('/tmp/diag.log', 'w')` writes with flush in the init code path.
2. **Direct Python test**: Create an AIAgent instance with venv Python (`./venv/bin/python -c "from run_agent import AIAgent; ..."`) to isolate whether the issue is code vs. gateway infrastructure.
3. **Agent caching**: Gateway caches agents per session key. After config/plugin changes, cached agents won't pick up changes. Restart gateway AND ensure new sessions (not cached ones) are tested.
4. **Beware sed cleanup**: Using `sed -i '' '/pattern/d'` on Python files can leave orphaned `if` blocks with empty bodies → SyntaxError. Always verify with `py_compile` after bulk sed operations.
5. **Honcho v3 API**: Honcho uses `/v3/` paths, not `/api/v1/` or `/health`. Any code hitting wrong paths will silently fail (caught by `except Exception`).

## Overview

Hermes Dojo is your agent's training gym. It reads past sessions, finds where you struggle,
and creates or improves skills to fix those weaknesses.

Core loop: **measure → identify weakness → fix → evolve → verify → report**

## Step 1: Analyze Performance

Run `session_search` to review recent sessions. Look for:

### Failure Signals
- Tool errors: regex patterns like `error:`, `traceback`, `timeout`, `command not found`, `permission denied`, `ENOENT`, `rate limit`
- User corrections: messages containing "no,", "wrong", "I meant", "not what I", "try again", "that broke", "doesn't work", "why did you"
- Retry loops: same tool called 3+ times without progress
- Skill gaps: repeated manual tasks with no skill (e.g., CSV parsing, PDF conversion)

### Error Pattern Catalog
| Pattern | Root Cause | Fix Strategy |
|---------|-----------|--------------|
| `command not found` | Missing CLI tool | Verify with `which` before execution, suggest install |
| `timeout` | Slow API/service | Add retry with exponential backoff (5s, 10s, 20s) |
| `permission denied` | File access issue | Check permissions before ops, suggest `chmod` |
| `no such file` | Wrong path | Validate path exists, search common alternatives |
| `rate limit` | Too many requests | Parse retry-after header, add delay logic |
| `syntax error` | Code generation issue | Add validation step before execution |

## Step 2: Generate Recommendations

For each identified weakness:

### A) FIX Mode — Existing skill fails → PATCH it
1. Read the current skill's SKILL.md with `skill_view`
2. Analyze the failure patterns
3. Use `skill_manage(action='patch')` to add error handling or edge case coverage
4. Log the change
5. **Verify**: Run the patched skill's workflow to confirm the fix works

### B) DERIVED Mode — Adapt a successful pattern to a new context
1. Identify a skill that works well in one domain (e.g., debugging in TS)
2. Extract the core algorithm/pattern from it
3. Create a new skill adapted to a different domain (e.g., debugging in Python)
4. Include domain-specific pitfalls and tool differences
5. **Verify**: Run a test case through the derived skill

### C) CAPTURED Mode — Extract a new pattern from a successful execution
1. Identify a session where a complex task succeeded (5+ tool calls, non-trivial logic)
2. Extract the workflow into a new skill with `skill_manage(action='create')`
3. Include specific instructions based on what worked in past sessions
4. Add pitfalls from any wrong turns that were corrected during the session
5. **Verify**: Confirm the captured skill covers the full workflow

### D) EVOLVE Mode — Deeper improvement via GEPA or self-reflection
1. For skills that fail consistently despite patches
2. Option A: Run `hermes-agent-self-evolution` (DSPy + GEPA) if available
3. Option B: Use `reflect_on_output` to critique the skill's instructions
4. Iterate on the instructions based on reflection feedback
5. **Verify**: Re-run the problematic scenario to confirm improvement

### Evolution Mode Selection
- If skill exists but has errors → FIX
- If skill works in domain A but needed in domain B → DERIVED
- If no skill exists but you just succeeded at a complex task → CAPTURED
- If skill has been patched 2+ times and still fails → EVOLVE

## Step 3: Track Improvement

Store metrics after each fix:
- Before/after success rates per skill
- User correction frequency over time
- New skills created vs. skills patched

Present results clearly:
```
=== Dojo Report ===
Sessions analyzed: 23 (last 7 days)
Overall success rate: 78% → 85% (+7%)

Top Fixes Applied:
1. terminal_run: 73% → 89% (added command verification)
2. web_extract: 81% → 92% (added retry logic)
3. NEW SKILL: csv-parsing (created from 4 recurring requests)
```

## Commands
- `/dojo` or `/dojo analyze` — Analyze recent sessions for failure patterns
- `/dojo improve` — Fix top weaknesses
- `/dojo report` — Show current metrics and improvement history

## Specific Diagnostic Patterns

### Checkpoint Manager Git Failures
The checkpoint system uses **shadow git repos** at `~/.hermes/checkpoints/{sha256(abs_path)[:16]}/` with `GIT_DIR` + `GIT_WORK_TREE` env vars pointing to the target directory. When `git add -A` fails:

1. Find the failing shadow repo: match the error's working directory to its hash via `python3 -c "import hashlib; print(hashlib.sha256('/path/to/dir'.encode()).hexdigest()[:16])\"`
2. Check the HERMES_WORKDIR file: `cat ~/.hermes/checkpoints/{hash}/HERMES_WORKDIR`
3. Common causes:
   - **Embedded git repos** (cloned projects inside the work dir) — git tries to add them as submodules, fails with "adding embedded git repository"
   - **Permission-denied files** (root-owned files like `/private/tmp/ticket-*`) — blocks `git add -A`
   - **Too many files** — `_MAX_FILES=50000` limit in checkpoint_manager.py
4. **Fix (CORRECT method)**: Patch `DEFAULT_EXCLUDES` list in `tools/checkpoint_manager.py` — add glob patterns for the problematic files/dirs. Do NOT patch `info/exclude` per shadow repo — `_init_shadow_repo()` overwrites it from `DEFAULT_EXCLUDES` on every init.
5. Verify: `GIT_DIR=~/.hermes/checkpoints/{hash} GIT_WORK_TREE=/path/to/dir git add -A`
6. **CAVEAT**: This patch gets overwritten by `hermes update` — must re-apply after updates. Document in memory so Dojo can re-apply.

### Cron ImportError After Git Pull
If cron jobs fail with `cannot import name 'X' from 'module'` immediately after a `git pull` on hermes-agent:
- **Root cause**: Python caches imported modules in `sys.modules`. Running processes keep the old version.
- **Fix**: Full Hermes restart: `pkill -f hermes_cli.main; pkill -f 'hermes -p'; pkill -f run_agent.py; sleep 2; hermes`
- **Prevention**: Always restart Hermes after any `git pull` on the hermes-agent repo.

### Error Log Analysis Tips
- `errors.log` can be >1000 lines — always read from the END (use `offset` parameter) to get recent errors
- Ignore errors older than the last restart timestamp
- Distinguish between one-off (timeout, DNS) and systematic (ImportError, Permission denied) patterns
- Only systematic patterns (3+ occurrences) warrant skill creation

## Step 4: Poly-Reflective CoT (PR-CoT) Self-Analysis

After generating recommendations, apply multi-perspective reflection before finalizing changes. Based on MyGO PR-CoT research (Cycle 219).

For each identified weakness, run 4 reflection perspectives:

1. **Logical Consistency** — Are the identified failure patterns internally consistent? Could the "failure" actually be correct behavior in a different context?
2. **Information Completeness** — Did you check ALL relevant sessions, not just the most recent ones? Are there environmental factors (API outages, config changes) that explain the failures?
3. **Bias Check** — Are you over-indexing on familiar patterns? Could a completely different root cause explain the symptoms? Are you creating skills that match your comfort zone rather than the actual need?
4. **Alternative Solutions** — Is patching the skill the right fix, or should you: change the environment, update config, switch models, or accept the limitation?

Scoring: Each perspective gets a pass/fail. Only proceed with the fix if all 4 pass, or if the failures are acknowledged in the fix plan.

Cost: ~4 extra LLM calls per analysis session. Worth it for high-impact skills.

## Pitfalls
- Don't patch skills based on single failures — require 2+ occurrences
- Don't create skills for one-off requests — check if the need recurs across 3+ sessions
- Always verify the patched skill actually works before declaring victory
- The GEPA evolution step costs API credits — reserve for high-value skills only
- Memory is capped at 12K chars — prefer concise entries and replace stale ones rather than always appending
- PR-CoT reflection adds ~4 LLM calls — skip for trivial fixes, use for high-impact skill changes

## Sources
- Yonkoo11/hermes-dojo (GitHub, ★3)
- NousResearch/hermes-agent-self-evolution (GitHub, ★340)
- GEPA paper: arXiv:2507.19457 (ICLR 2026 Oral)
- OpenSpace (HKUDS): github.com/HKUDS/OpenSpace — 3-mode evolution (FIX/DERIVED/CAPTURED), 46% token reduction
- Karpathy AutoResearch: github.com/karpathy/autoresearch — self-refining program.md pattern
- XMUDeepLIT/Awesome-Self-Evolving-Agents — comprehensive survey with TTCS benchmark
- AVO paper: arxiv 2603.24517 — agentic variation operators beating expert-engineered solutions
