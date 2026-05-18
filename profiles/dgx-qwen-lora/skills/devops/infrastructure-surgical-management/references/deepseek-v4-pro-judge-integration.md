# DeepSeek v4 Pro Judge Integration — Session Notes (May 6, 2026)

## What Was Built

Wired `deepseek-v4-pro` LLM Judge into the `learning-brain` plugin's `post_tool_call` hook for real-time tip quality evaluation.

## Architecture

```
Tool Call Result (JSON with tip field)
    │
    ▼
post_tool_call_hook()
    │
    ▼
Extract tips from result['tip'], result['tips'], result['learning'], etc.
    │
    ▼
LLMJudge.evaluate_single(tip) — deepseek-v4-pro
    │
    ┌───────────────┴───────────────┐
score < 0.6                    score >= 0.7 + actionable
    │                              │
    ▼                              ▼
error_registry              session_continuity
(tool, error, fix)          (tips_learned JSON array)
    │                              │
    ▼                              ▼
Review & rewrite           Distillation pipeline
```

## Files Modified

1. **plugins/learning-brain/__init__.py**
   - Added `from subconscious.llm_judge import LLMJudge`
   - Added `_get_judge()` singleton
   - In `post_tool_call_hook()`: extract tips from JSON results, evaluate each, route by quality score

2. **hermes_cli/subconscious/llm_judge.py**
   - Fixed DeepSeek V4 Pro JSON extraction (reasoning_content vs content field)
   - Added `response_format` parameter to `_call_llm()`
   - Increased `evaluate_single()` max_tokens from 300 → 2000
   - Fixed system prompt to direct output to content field

3. **hermes_cli/context_updater.py**
   - Added `tips_learned` column to `session_continuity` table
   - `update_session()` now creates new sessions if missing (was only updating existing)
   - Added `tip` parameter to `update_session()`

## DeepSeek v4 Pro Gotchas

### 1. JSON Output Location

DeepSeek v4 Pro returns:
- `content`: The actual JSON output (when system prompt is correct)
- `reasoning_content`: The model's chain-of-thought reasoning

**Problem:** If reasoning is long, `content` may be empty and JSON truncated in `reasoning_content`.

**Fix:**
```python
# System prompt MUST explicitly say:
"After thinking, output ONLY valid JSON in the content field"

# max_tokens MUST be 2000+ for complex evaluations
# (800 tokens insufficient — reasoning uses 600-900 before JSON)

# Use response_format={"type": "json_object"} as baseline
```

### 2. Cost

- Per evaluation: ~$0.0002 (discounted until 2026-05-31)
- Per compare_tips: ~$0.0002
- 1000 evaluations/day = ~$0.20

### 3. Quality Score Interpretation

The judge is STRICT. Good tips often score 0.3-0.7, not 0.9+.

| Score | Meaning | Action |
|-------|---------|--------|
| 0.0-0.3 | Vague, incorrect, or missing triggers/actions | Record error, suggest rewrite |
| 0.3-0.6 | Actionable but has issues (suboptimal advice, missing context) | Log for review |
| 0.7-1.0 | High quality, specific, actionable | Log to session for distillation |

## Test Verification

```python
from hermes_cli.subconscious.llm_judge import LLMJudge

judge = LLMJudge(model='deepseek-v4-pro')

# Good tip — should be actionable but may score modestly
good = judge.evaluate_single({
    "text": "Always use try-except when parsing JSON from external sources",
    "domain": "code",
    "confidence": 0.9
})
assert good["is_actionable"] is True

# Bad tip — should score low with issues
bad = judge.evaluate_single({
    "text": "Be careful with stuff",
    "domain": "general",
    "confidence": 0.5
})
assert bad["quality_score"] < 0.3
assert len(bad["issues"]) > 0
```

## Integration Test

```bash
cd /Users/dannygomez/hermes-agent
python3 -c "
import sys
sys.path.insert(0, 'hermes_cli')

from plugins.learning_brain import register, _get_judge

class MockCtx:
    def __init__(self):
        self.hooks = {}
    def register_hook(self, name, fn):
        self.hooks[name] = fn

ctx = MockCtx()
register(ctx)

# Test with high-quality tip
tip = '{\"tip\": \"Always use try-except when parsing JSON\", \"confidence\": 0.9}'
result = ctx.hooks['post_tool_call']('web_search', {'query': 'test'}, tip, None, 'session_123', 1500)
print(result)  # {'success': True, 'analyzed': True, 'healed': None, 'judge_evaluated': True}

judge = _get_judge()
print(f'Cost: \${judge.total_cost:.4f}')
"
```

## Unified Context Verification

```bash
python3 -c "
import sqlite3
from pathlib import Path
db = sqlite3.connect(str(Path.home() / '.hermes/unified_context.db'))
c = db.cursor()

# Check sessions with tips
c.execute('SELECT session_id, tips_learned FROM session_continuity WHERE tips_learned != \"[]\"')
for row in c.fetchall():
    print(f'Session {row[0]}: {row[1]}')

# Check low-quality tip errors
c.execute(\"SELECT tool_name, signature FROM error_registry WHERE signature LIKE '%Low-quality tip%'\")
for row in c.fetchall():
    print(f'Error: {row[0]} - {row[1]}')
"
```
