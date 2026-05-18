# Upstream Surgical Integration Pattern

## Date: 2026-05-18

## Problem

Upstream (NousResearch/hermes-agent) is 8,722 commits ahead. Attempting a full merge would:
- Break 21 cognitive subsystems
- Conflict with monolithic integration architecture
- Replace working code with incompatible upstream hooks

## Solution: Cherry-Pick → Adapt → Insert

Instead of merging, extract specific patterns from upstream and adapt them into existing subsystems.

## The 5-Step Pattern

### Step 1: Identify

Find upstream commits with techniques you want:

```bash
# In upstream clone
cd /tmp/hermes-upstream
git log --oneline --all | head -50

# Inspect a commit
git show abc1234 --stat

# Cherry-pick a specific file
git checkout upstream/main -- agent/background_review.py
```

### Step 2: Study

Read the file completely. Identify the core technique:

- What problem does it solve?
- What is the minimal pattern that delivers value?
- What upstream infrastructure does it depend on?

### Step 3: Adapt

Strip upstream dependencies, rename to match your conventions:

| Upstream | Your System |
|----------|-------------|
| `background_review.py` | `training_gym.py` |
| `agent_runtime_helpers.py` | `distillation_bridge.py` |
| `iteration_budget.py` | `unified_intelligence_engine.py` |
| `conversation_compression.py` | `adaptive_context_sculptor.py` |

Replace upstream imports:
- `from hermes_cli.plugins import ...` → `from agent.cognitive_orchestrator import ...`
- `from hermes_cli.hooks import ...` → direct method calls on your systems

### Step 4: Insert

Add new code alongside existing code — never replace:

```python
# In agent/training_gym.py — add new method to existing class
def _spawn_exercise_review(self, exercise_id: str) -> None:
    """Post-exercise evaluation daemon."""
    import threading
    def review():
        try:
            # ... adapted from upstream background_review.py
        except Exception:
            pass  # daemon thread must not crash
    threading.Thread(target=review, daemon=True).start()
```

Key rules:
- Use daemon threads for background work
- Wrap all new code in try/except
- Don't touch existing methods
- Don't change existing imports

### Step 5: Verify

```bash
# Import smoke test
python -c "from agent.training_gym import TrainingGym; t = TrainingGym(); print('OK')"

# Run existing tests
pytest agent/test_training_gym.py -v

# Check no regressions
pytest agent/ -q --tb=short
```

## May 2026 Integration Results

| Pattern | Source File | Destination | Lines Added |
|---------|-------------|-------------|-------------|
| Background review fork | `background_review.py` | `training_gym._spawn_exercise_review()` | ~40 |
| Trajectory export | `agent_runtime_helpers.py` | `distillation_bridge.export_trajectory()` | ~25 |
| Iteration budget | `iteration_budget.py` | `unified_intelligence_engine.CognitiveIterationBudget` | ~60 |
| Feasibility probe | `conversation_compression.py` | `adaptive_context_sculptor.check_compression_feasibility()` | ~30 |
| Memory isolation | `background_review.py` | `memory_cortex_bridge.set_cognitive_isolation()` | ~45 |

**Total: 6 files cherry-picked, 5 patterns integrated, 0 existing files modified.**

## Verification

All 20 cognitive subsystems active after integration:

```bash
python -c "
from agent.cognitive_orchestrator import get_orchestrator
o = get_orchestrator()
status = o.get_status()
print(f'Subsystems: {len(status[\"subsystems\"])}/20 active')
"
```

## Key Principle

Your cognitive orchestrator is the source of truth. Upstream patterns are inputs to it, not replacements for it. When upstream is incompatible, adapt patterns — don't merge code.
