# KIMI HARNESS ENHANCEMENT MANIFEST v2.2
## Predictive Tool Loading System

**Date:** 2026-04-26
**Status:** DEPLOYED

---

## WHAT CHANGED FROM v2.1

v2.1 learned from errors.
v2.2 **anticipates needs** — predicts which tools will be needed before the user asks.

---

## ARCHITECTURE

### Layer 1: Keyword Triggers
- Hardcoded mapping of tool names to trigger keywords
- Fast, rule-based prediction for common cases

### Layer 2: Sequence Patterns
- Learns which tools often follow each other
- Example: `web_search` → `web_extract` → `execute_code`
- Stored in `tool_sequence_patterns` table

### Layer 3: Context Learning
- Learns which tools are successful in which contexts
- Stores keywords from successful tool usage
- Ranks by success_rate × usage_count

### Layer 4: Combined Scoring
- Merges all three signals with learned weights
- Returns top-k predictions with confidence scores

---

## SCHEMA

```sql
CREATE TABLE tool_usage_patterns (
    id UUID PRIMARY KEY,
    tool_name TEXT NOT NULL,
    context_keywords TEXT[],
    preceding_tools TEXT[],
    success_rate FLOAT DEFAULT 0.0,
    usage_count INTEGER DEFAULT 1,
    avg_latency_ms INTEGER,
    last_used TIMESTAMP,
    metadata JSONB
);

CREATE TABLE tool_sequence_patterns (
    id UUID PRIMARY KEY,
    tool_a TEXT NOT NULL,
    tool_b TEXT NOT NULL,
    sequence_count INTEGER DEFAULT 1,
    avg_gap_turns INTEGER DEFAULT 1,
    last_seen TIMESTAMP
);
```

---

## FILES

### New
- `agent/predictive_tools.py` — Predictive tool loading engine

---

## HOW IT WORKS

1. **User asks something** → Query analyzed for keywords
2. **Keyword matching** → `web_search` triggered by "research", "find", "latest"
3. **Sequence check** → If `web_search` was just used, predict `web_extract` next
4. **Context learning** → Query keywords matched against successful past usage
5. **Combined score** → All signals merged, top-k returned

---

## EXAMPLE PREDICTIONS

| Query | Predicted Tools | Confidence |
|-------|----------------|------------|
| "Research FlashKDA" | web_search (0.9), web_extract (0.3) | High |
| "Fix syntax error" | patch (0.3), read_file (0.2) | Medium |
| "Deploy to server" | terminal (0.4), cronjob (0.2) | Medium |
| "Send notification" | send_message (0.6) | High |

---

## INTEGRATION POINTS

Can be integrated into:
- System prompt: "Predicted tools for this task: ..."
- Tool dispatch: Pre-warm likely tools
- UI: Show predicted tools in sidebar

---

## FUTURE ENHANCEMENTS

1. **Multi-tool chains** — Predict entire sequences, not just next tool
2. **Latency-aware** — Prefer faster tools when confidence is similar
3. **Success-weighted** — Weight predictions by historical success rate
4. **User preference** — Learn which tools each user prefers
5. **Auto-execution** — Execute predicted tools proactively (with confirmation)

---

## TESTING

```python
from agent.predictive_tools import get_predictive_loader
loader = get_predictive_loader()

# Predict for a query
predictions = loader.predict_needed_tools("Research medical imaging datasets", top_k=5)
for tool, score in predictions:
    print(f"{tool}: {score:.3f}")

# Record usage for learning
loader.record_tool_usage("web_search", "research medical imaging", successful=True)

# Get recommendations
recs = loader.get_tool_recommendations("Build a medical copilot", available_tools)
for r in recs:
    print(f"{r['tool']}: {r['confidence']} (success: {r['success_rate']})")
```
