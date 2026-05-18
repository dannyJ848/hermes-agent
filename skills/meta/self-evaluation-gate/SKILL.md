---
name: self-evaluation-gate
title: Self-Evaluation Gate Protocol
version: 1.0
description: |
  Mandatory quality gate that runs before delivering any non-trivial output.
  Scores on 5 dimensions, rejects outputs below threshold, triggers pivot on repeated failures.
author: Hermes Agent
---

# Self-Evaluation Gate Protocol

## Trigger Condition

**ALWAYS** run the evaluation gate before delivering output when ANY of these apply:
- Output is >100 lines
- Output contains code, commands, or file paths
- Output makes factual claims (numbers, dates, names)
- Output recommends actions the user should take
- More than 3 tool calls were used to produce the output
- Expected cost was >$0.10

## Quick Check (5 seconds)

Before calling the gate, do a rapid self-check:

1. **Did I actually answer the question?** (not just acknowledged it)
2. **Are there TODOs or placeholders?** (search for "TODO", "FIXME", "...")
3. **Any destructive commands?** (search for "rm -rf", "DROP", "dd if=")
4. **Did I include file paths and run commands?** (for code outputs)
5. **Am I being vague?** (search for "something", "maybe", "probably")

If any check fails, fix it BEFORE running the gate.

## Running the Gate

```python
from agent.cognitive_orchestrator import get_orchestrator

orchestrator = get_orchestrator()

# Ensure initialized
if not orchestrator._subsystems:
    class MockAgent:
        session_id = 'eval_gate'
        model = 'unknown'
        provider = 'unknown'
    orchestrator.initialize(MockAgent())

result = orchestrator.evaluate_output(
    output=my_draft_response,
    task=original_user_request,
    tools_used=["terminal", "patch", "write_file"],  # list tools used
    expected_cost_usd=0.05,  # estimate if known
    is_code=True,  # True if output contains code/commands
)
```

## Interpreting Results

### Score Tiers

| Score | Tier | Action |
|-------|------|--------|
| 9-10 | excellent | Deliver as-is |
| 7-8 | good | Deliver, minor improvements optional |
| 5-6 | acceptable | Deliver if no revision notes, otherwise fix |
| 3-4 | needs_work | **DO NOT DELIVER** — fix revision notes first |
| 0-2 | reject | **DO NOT DELIVER** — major revision required |

### If `revision_required=True`

1. Read `result["revision_notes"]` — each is a specific fix
2. Fix the highest-impact issues first (safety, then completeness)
3. Re-run the gate on revised output
4. Only deliver when `passed=True` AND `tier` is "acceptable" or better

### If `should_pivot=True`

This means 3+ consecutive outputs failed the gate. **Stop and rethink:**

1. Is my approach fundamentally wrong?
2. Am I missing context from the user?
3. Should I ask for clarification instead of guessing?
4. Is there a simpler way to solve this?

## Common Failure Patterns & Fixes

| Issue | Fix |
|-------|-----|
| "Output extremely short" | Add more detail, examples, or context |
| "No clear steps" | Numbered list of next actions |
| "No file paths" | Include absolute paths for all files |
| "No run/test commands" | Add command to verify the fix works |
| "Hedging language" | Replace "probably" with specific facts |
| "TODO marker found" | Complete the TODO before delivering |
| "Expensive tool used" | Use cheaper alternative (cached_delegate vs delegate_task) |
| "Recursive delete" | Add confirmation prompt or safer alternative |

## Safety Dimension — User Risk Tolerance

The safety evaluator checks for destructive commands (`rm -rf`, `DROP DATABASE`, `dd if= of=/dev/`, etc.). By default it applies a **moderate penalty** (score -= 3.0 per violation) with safety weighted at 5% of overall score.

**This user has extremely high risk tolerance.** When they say "lower it" or "I want high risk tolerance":

1. **Lower the penalty** in `self_evaluation_gate.py`: `score -= 3.0` (not 5.0)
2. **Lower the weight**: safety = 0.05 (not 0.15), redistribute to accuracy/completeness/actionability
3. **Keep the flagging** — safety issues still appear in revision notes so the user sees them
4. **Never remove the patterns** — the gate should always DETECT destructive commands even if it doesn't auto-reject

**Current config for this user:**
```python
# In self_evaluation_gate.py SelfEvaluationGate.DIMENSIONS
DIMENSIONS = {
    'accuracy': 0.30,
    'completeness': 0.30,
    'actionability': 0.25,
    'cost_efficiency': 0.10,
    'safety': 0.05,
}
# In _evaluate_safety():
score -= 3.0  # per destructive pattern match
```

**Result:** A well-constructed output with `rm -rf` can still pass (score ~7.3/10) because accuracy/completeness/actionability dominate. A bare `rm -rf` with no context still fails (~5.5/10) due to weak other dimensions.

**Pattern for high-risk-tolerance users:**
- Gate still scores safety low and reports issues
- Delivery logic checks `user_risk_tolerance` flag before rejecting
- User sees the warning but can proceed

```python
# In delivery logic (NOT in the gate itself)
if not result["passed"] and result["tier"] == "needs_work":
    safety_issues = [n for n in result["revision_notes"] if "SAFETY:" in n]
    if safety_issues and user_has_high_risk_tolerance():
        # Warn but allow
        deliver_with_warning(output, safety_issues)
    else:
        # Reject normally
        reject_and_revise(output, result["revision_notes"])
```

## Cost Awareness

The gate flags expensive patterns. Prefer these alternatives:

| Expensive | Cheaper Alternative |
|-----------|---------------------|
| `delegate_task` | `cached_delegate` or direct tool call |
| `browser_navigate` + click chain | `web_extract` for static content |
| `browser_vision` | `browser_snapshot` for text-only pages |
| `claude_bridge_task` | Direct `terminal`/`patch` for simple edits |
| Multiple `web_search` | Single search + `web_extract` on results |

## Integration with Other Systems

- **Failure Prevention**: Gate runs AFTER failure prevention risk assessment
- **Domain Transfer**: If pivot triggered, check domain_transfer for alternative approaches
- **Attention Prioritizer**: Gate scores are stored and used to improve memory relevance
- **Training Gym**: Failed evaluations become training exercises

## Stats Tracking

```python
stats = orchestrator.get_evaluation_stats()
print(f"Pass rate: {stats['pass_rate']:.0%}")
print(f"Avg score: {stats['avg_score']:.1f}")
print(f"Consecutive failures: {stats['consecutive_failures']}")
```

## Example: Full Workflow

```python
# 1. Produce draft output
draft = generate_response(user_request)

# 2. Quick self-check (5 seconds)
if "TODO" in draft or "rm -rf" in draft:
    draft = fix_issues(draft)

# 3. Run evaluation gate
result = orchestrator.evaluate_output(
    output=draft,
    task=user_request,
    tools_used=tools_used_this_turn,
    is_code="```" in draft,
)

# 4. Decide delivery
if result["passed"] and result["score"] >= 6.0:
    deliver(draft)
else:
    # Fix and retry
    for note in result["revision_notes"]:
        draft = apply_fix(draft, note)
    
    # Re-evaluate
    result2 = orchestrator.evaluate_output(draft, user_request, tools_used)
    if result2["passed"]:
        deliver(draft)
    else:
        # Escalate: ask user for clarification
        ask_clarification(result2["revision_notes"])
```

## Pitfalls

1. **Don't skip the gate for "simple" outputs** — even short outputs can have safety issues
2. **Don't ignore revision notes** — they're specific and actionable
3. **Don't loop forever** — if 3 evaluations fail, pivot or ask user
4. **Don't forget to initialize** — gate won't work without `orchestrator.initialize()`
5. **Don't evaluate empty outputs** — gate will reject them immediately
6. **Don't conflate scoring with delivery policy** — the gate SCORES; delivery logic DECIDES. A low safety score for `rm -rf` is correct even if the user has high risk tolerance. The override belongs in the delivery layer, not the scorer.
