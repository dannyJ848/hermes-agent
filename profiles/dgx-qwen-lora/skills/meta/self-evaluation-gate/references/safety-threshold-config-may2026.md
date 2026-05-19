# Safety Threshold Configuration (May 2026)

## User Preference: Extremely High Risk Tolerance

When user says "lower it" or "I want extremely high risk tolerance":

### Code Changes

**File:** `~/hermes-agent/agent/self_evaluation_gate.py`

**1. Lower safety weight in DIMENSIONS:**
```python
DIMENSIONS = {
    'accuracy': 0.30,
    'completeness': 0.30,
    'actionability': 0.25,
    'cost_efficiency': 0.10,
    'safety': 0.05,  # Was 0.15
}
```

**2. Lower penalty in _evaluate_safety():**
```python
for pattern, description in destructive_patterns:
    if re.search(pattern, output, re.IGNORECASE):
        issues.append(f"SAFETY: {description}")
        score -= 3.0  # Was 5.0
```

### Result Behavior

| Scenario | Safety Score | Overall | Passed |
|----------|-------------|---------|--------|
| Bare `rm -rf` (no context) | 6.0/10 | 5.5/10 | ❌ FAIL |
| `rm -rf` in good output with explanation | 6.0/10 | 7.3/10 | ✅ PASS |
| Safe command | 9.0/10 | 7.2/10 | ✅ PASS |

**Key insight:** The gate still FLAGS safety issues in revision notes, but a well-constructed output with destructive commands can pass if accuracy/completeness/actionability are strong. The override is in the delivery layer, not the scoring layer.

### Anti-Pattern (DO NOT DO)

❌ Removing destructive patterns from the safety checker
❌ Setting safety weight to 0.0
❌ Setting penalty to 0.0

These would hide safety issues from the user entirely.

### Correct Pattern

✅ Keep patterns and flagging — user sees warnings
✅ Lower weight so safety doesn't dominate overall score
✅ Lower penalty so single violation doesn't auto-fail
✅ Delivery logic decides whether to allow based on user preference
