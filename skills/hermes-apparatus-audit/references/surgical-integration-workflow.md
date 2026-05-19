# Surgical Integration Workflow
## From upstream cherry-pick to cognitive subsystem enhancement
### Session: 2026-05-18 | Commit: e2e2c5825

---

## Problem

Upstream NousResearch/hermes-agent is 8,722 commits ahead with incompatible architecture (no hook infrastructure for cognitive orchestrator). Merging wholesale would destroy all 21 cognitive subsystems. But upstream contains valuable patterns we want.

## Solution: Surgical Pattern Adaptation

Instead of merging upstream code, **adapt specific patterns** into existing cognitive subsystems. Each pattern is:
- **Additive** — inserted alongside existing code, never replacing
- **Self-contained** — has its own docstring explaining upstream origin
- **Fail-safe** — wrapped in try/except where it interfaces with existing systems
- **Non-blocking** — daemon threads for background work

---

## Workflow Steps

### 1. Audit upstream for relevant patterns

```bash
# Add upstream remote
git remote add nousresearch https://github.com/NousResearch/hermes-agent.git
git fetch nousresearch

# Check for hook infrastructure (should return 0 for incompatible upstream)
git show nousresearch/main:run_agent.py | grep -c 'invoke_hook\|before_action\|after_action'

# If 0, upstream is INCOMPATIBLE — do not merge
```

### 2. Cherry-pick high-value files for study

```bash
# Create study directory
mkdir upstream_cherrypick/

# Extract specific files (not whole codebase)
git show nousresearch/main:agent/background_review.py > upstream_cherrypick/background_review.py
git show nousresearch/main:agent/agent_runtime_helpers.py > upstream_cherrypick/agent_runtime_helpers.py
git show nousresearch/main:agent/conversation_compression.py > upstream_cherrypick/conversation_compression.py
git show nousresearch/main:agent/iteration_budget.py > upstream_cherrypick/iteration_budget.py

# Create analysis document
cat > upstream_cherrypick/ANALYSIS.md << 'EOF'
# Integration Strategy
- TIER S (Game Changers): background_review.py, agent_runtime_helpers.py
- TIER A (High Value): conversation_compression.py, iteration_budget.py
- TIER B (Useful): async_utils.py, conversation_loop.py
- INCOMPATIBLE: Plugin system, config system, tool dispatch
EOF
```

### 3. Study each file, identify the core pattern

Read the cherry-picked file. Identify:
- **What problem does it solve?**
- **What is the core mechanism?** (not the implementation details)
- **Can our existing subsystem solve the same problem?**

Example from `background_review.py`:
- Problem: Post-turn evaluation for memory/skill updates
- Mechanism: Fork agent with tool whitelist, run in daemon thread
- Our equivalent: `training_gym.py` already has post-exercise hooks — enhance them

### 4. Write the adaptation as a standalone block

Insert at the **end** of the target file (before `if __name__ == "__main__"`), clearly marked:

```python
# ── UPSTREAM PATTERN: <Name> (adapted from <source_file>.py) ──
# <One-line description of what this does>
# <How it differs from upstream>

def new_function(...):
    """Docstring explaining upstream origin and adaptation."""
    ...
```

### 5. Verify no existing code was touched

```bash
# Check only additions, no deletions
git diff --stat
# Expected: only insertions (+), no deletions (-) except maybe blank lines

# Verify file still imports
cd ~/.hermes && python3 -c "from agent.training_gym import *; print('OK')"
```

### 6. Commit with descriptive message

```bash
git add agent/training_gym.py agent/distillation_bridge.py ...
git commit -m "cognitive: Surgical integration of N upstream patterns

1. training_gym — Background review fork pattern
2. distillation_bridge — Trajectory export
3. unified_intelligence — Iteration budget
4. context_sculptor — Feasibility probes
5. memory_bridge — Memory isolation

All patterns are ADAPTIVE (not replacement)."
```

---

## Pitfalls

1. **Don't import upstream modules directly** — they depend on upstream architecture
2. **Don't modify existing function signatures** — breaks orchestrator compatibility
3. **Don't assume upstream constants exist** — `MINIMUM_CONTEXT_LENGTH` may not exist in our fork
4. **Don't use upstream imports** — `from agent.auxiliary_client import ...` may fail silently
5. **Always wrap in try/except** — new code must not break existing subsystems

---

## Verification

After integration, verify:
- `hermes doctor` still reports all cognitive systems active
- `git diff` shows only additions, no modifications to existing logic
- `python3 -c "from agent.<module> import *"` works for each modified file
- No new dependencies introduced

---

## Related

- `references/audit-2026-05-18-full-apparatus-wiring.md` — the audit that triggered this integration
- `references/dgx-full-port-procedure-may18-2026.md` — cross-machine sync after integration
- `references/cognitive-orchestrator-pattern-2026-05.md` — the orchestrator that hosts these subsystems
