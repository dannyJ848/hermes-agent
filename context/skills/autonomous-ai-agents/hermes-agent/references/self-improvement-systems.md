# Self-Improvement Systems Integration

Session: May 6, 2026 — Building proactive self-monitoring into Hermes source

## What Was Built

Eight self-improvement systems + master integrator, all wired into `hermes_cli/`:

| System | File | Purpose | Status |
|--------|------|---------|--------|
| Loop Guard | `hermes_cli/loop_guard.py` | Detects 3+ repeated tool calls, blocks loops | ✓ Tested |
| Self-Healing Dispatch | `hermes_cli/self_healing_dispatch.py` | Auto-routes to alternative tool on failure | ✓ Tested |
| Failure Post-Mortem | `hermes_cli/failure_post_mortem.py` | Analyzes errors, extracts patterns, suggests fixes | ✓ Tested |
| Intent Verifier | `hermes_cli/intent_verifier.py` | Verifies output matches user intent | ✓ Tested |
| Proactive Tip Injector | `hermes_cli/proactive_tip_injector.py` | Surfaces relevant tips before task | ✓ Tested |
| Token Budget Tracker | `hermes_cli/token_budget_tracker.py` | Monitors token usage per session | ✓ Tested |
| Confidence Calibrator | `hermes_cli/confidence_calibrator.py` | Knows when uncertain vs certain | ✓ Tested |
| **LLM Judge** | `hermes_cli/subconscious/llm_judge.py` | Auto-evaluates tip quality using deepseek-v4-pro | ✓ Live |
| **Hermes Brain** | `hermes_cli/hermes_brain.py` | Master integrator wiring all systems | ✓ Tested |

## Practice Run Results

### Loop Guard
```
Call 1: loop=False, count=1
Call 2: loop=False, count=2
Call 3: loop=True, count=3  ← BLOCKED
Call 4: loop=True, count=4  ← BLOCKED
```

### Self-Healing
- Input: `patch` with identical strings
- Output: routed to `write_file` with "rewrite entire file" strategy

### Failure Post-Mortem
Learned patterns from actual session errors:
- `patch` + "identical strings" → `patch_logic` → verify uniqueness
- `execute_code` + `IndentationError` → `code_formatting` → use `write_file`
- `terminal` + "no such table" → `database_schema` → check table exists

### Confidence Calibration
- Assumed claim ("DeepSeek is judge"): 0.40 confidence → should disclaim
- Direct observation ("PID is 590094"): 0.95 confidence → proceed

## Key Pitfall: Search Scope

The judge system lived in `~/subconscious/` (2653 files), NOT in `hermes_cli/` or `gateway/`. Initial searches missed it entirely. **Lesson:** When user says "find it", expand search scope broadly — check `~/.hermes/`, `~/subconscious/`, and any other project-specific directories.

## Integration Pattern

```python
from hermes_brain import HermesBrain
from subconscious.llm_judge import LLMJudge
brain = HermesBrain()
judge = LLMJudge(model="deepseek-v4-pro")

# Before tool call
result = brain.before_tool_call('patch', args, session_id)
if result['action'] == 'BLOCK':
    print(f"Loop detected: {result['alternative']}")

# After error
result = brain.after_tool_call('patch', args, None, error)
print(f"Lesson: {result['lesson']}")

# Evaluate a tip for quality
tip = {"text": "Always validate JSON before parsing", "domain": "code"}
eval_result = judge.evaluate_single(tip)
print(f"Quality: {eval_result['quality_score']}, Actionable: {eval_result['is_actionable']}")

# Compare two tips
tip_a = {"text": "Use try-except for JSON parsing", "domain": "code", "confidence": 0.9}
tip_b = {"text": "Be careful with JSON", "domain": "code", "confidence": 0.5}
compare = judge.compare_tips(tip_a, tip_b)
print(f"Winner: {compare['winner']}, Confidence: {compare['confidence']}")

# Task lifecycle
brain.on_task_start('merge upstream')
brain.on_task_end(task_id, expected, actual)
```

## Database Tables Created

- `loop_detection` — tool call patterns with args hash
- `healing_log` — fallback attempts with success/failure
- `error_patterns` — error signatures + root cause + fix strategy
- `intent_checks` — task description vs expected vs actual outcome
- `token_usage` — per-session token tracking
- `confidence_log` — calibration accuracy over time

## Files Modified

- `hermes_cli/plugins.py` — dispatch_tool() instrumented with intelligence tracking
- `hermes_cli/systems_registry.json` — unified config
- `hermes_cli/unified_status.py` — single command status view
- `hermes_cli/persistence_health.py` — database health checker
- `hermes_cli/subconscious/llm_judge.py` — LLM-based tip evaluator (deepseek-v4-pro)
- `hermes_cli/context_updater.py` — live persistence with tips_learned tracking
- `hermes_cli/instant_context.py` — CLI resume showing judge status + tips
- `plugins/learning-brain/__init__.py` — learning loop plugin with judge integration
