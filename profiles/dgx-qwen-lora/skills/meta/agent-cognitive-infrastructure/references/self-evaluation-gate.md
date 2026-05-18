# Self-Evaluation Gate — Reference

## Overview

Pre-delivery quality gate that scores every output on 5 dimensions before delivering to the user. If score < 6.0, the gate REJECTS the output and provides specific revision notes.

## API

### `SelfEvaluationGate.evaluate(output, task, tools_used, expected_cost_usd, is_code)`

Returns `GateResult` with:
- `passed` (bool): True if score >= 6.0
- `overall_score` (float): 0-10 weighted average
- `tier` (QualityTier): excellent/good/acceptable/needs_work/reject
- `scores` (List[EvaluationScore]): Per-dimension breakdown
- `revision_required` (bool): True if not passed or tier == needs_work
- `revision_notes` (List[str]): Specific fix instructions
- `estimated_tokens_burned` (int): Rough token estimate

### `SelfEvaluationGate.should_pivot()`

Returns `(bool, str)` — True after 3 consecutive failures, with reason string.

### Orchestrator Integration

```python
from agent.cognitive_orchestrator import get_orchestrator

orchestrator = get_orchestrator()
result = orchestrator.evaluate_output(
    output=my_response,
    task="What the user asked",
    tools_used=["terminal", "patch"],
    expected_cost_usd=0.0,
    is_code=True,
)

if not result["passed"]:
    print("REJECTED:")
    for note in result["revision_notes"]:
        print(f"  - {note}")
    # Fix issues before delivering

if result["should_pivot"]:
    print(f"PIVOT: {result['pivot_reason']}")
    # Try completely different approach
```

## Dimensions

| Dimension | Weight | Checks |
|-----------|--------|--------|
| Accuracy | 25% | Hedging language ("probably", "maybe"), numbers without sources, placeholder URLs, contradictions |
| Completeness | 25% | Missing task keywords, TODO/FIXME/XXX markers, outputs <50 chars, ending in "..." |
| Actionability | 20% | File paths present, run commands included, vague words ("something", "somehow"), next steps |
| Cost Efficiency | 15% | Expensive tools flagged (delegate_task, browser_navigate), redundant calls (>5x same tool), cost >$0.50 |
| Safety | 15% | `rm -rf`, `dd if= of=/dev/`, `mv to /dev/null`, `DROP DATABASE`, `DELETE FROM...WHERE`, sudo without context |

## Scoring Logic

```
overall = sum(score * weight for score, weight in zip(dimension_scores, weights))

Tier thresholds:
  excellent: >= 8.5
  good:      >= 7.0
  acceptable: >= 5.0
  needs_work: >= 3.0
  reject:      < 3.0

Pass threshold: >= 6.0
```

## Test Results

| Scenario | Score | Tier | Passed | Issues |
|----------|-------|------|--------|--------|
| Good output (comprehensive, actionable, safe) | 8.0/10 | good | ✅ | 0 |
| Bad output (vague, TODO, rm -rf) | 3.9/10 | needs_work | ❌ | 15 |
| Empty output | 2.5/10 | reject | ❌ | 3 |
| Output with placeholder URL | 6.5/10 | acceptable | ✅ | 1 |

## Pivot Detection

After 3 consecutive evaluations with `passed=False`, `should_pivot` returns True. This forces a completely different approach to break out of failure loops.

```python
for i in range(3):
    result = orchestrator.evaluate_output(bad_output, task, tools)
    if result["should_pivot"]:
        # Stop current approach, try something else entirely
        break
```

## Stats Tracking

```python
stats = orchestrator.get_evaluation_stats()
# Returns:
# {
#   "total_evaluations": 42,
#   "pass_rate": 0.78,
#   "avg_score": 7.2,
#   "consecutive_failures": 0,
#   "by_dimension": {
#     "accuracy": {"avg": 7.5, "min": 3.0, "max": 9.0},
#     ...
#   }
# }
```

## Integration into Agent Loop

The gate is wired into the cognitive orchestrator but NOT automatically called on every response (that would require modifying the Hermes agent loop itself). Instead:

1. **Manual call before complex outputs**: Call `evaluate_output()` before delivering code, long explanations, or multi-step instructions
2. **Before expensive operations**: Call with `expected_cost_usd` set to flag costly tool usage
3. **After failures**: Call to check if pivot is needed

## Files

- `~/hermes-agent/agent/self_evaluation_gate.py` — Core gate logic (398 lines)
- `~/hermes-agent/agent/cognitive_orchestrator.py` — Integration via `evaluate_output()` and `get_evaluation_stats()`
