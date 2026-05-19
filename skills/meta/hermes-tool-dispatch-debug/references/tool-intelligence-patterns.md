# Tool Intelligence Patterns

Session: 2026-05-09 — Extracted from 2057 tool calls across enhancement cycles

## Weak Tools (Route Around)

### `cronjob` — 13% success (38 calls)
**Failure mode:** `id` field confusion. The tool expects a specific `id` parameter format that doesn't match user intent.
**Prevention:** Always use `terminal` with raw crontab syntax instead:
```bash
# Instead of cronjob tool:
(crontab -l 2>/dev/null; echo "*/5 * * * * /path/to/script") | crontab -
```

### `delegate_parallel` — 33% success (3 calls)
**Failure mode:** Frequent failure (3x). The parallel coordination mechanism breaks under load.
**Prevention:** Use `delegate_task` sequential instead. Parallel gains are lost to retry overhead.

### `patch` — 94% success (52 calls)
**Failure mode:** `old_string` mismatch. The exact text in the file doesn't match what the agent expects.
**Prevention strategies:**
1. Always `read_file` before `patch` to get exact current text
2. Use `offset`/`limit` for large files to avoid truncation
3. If patch fails twice, switch to `write_file` for full replacement
4. Verify `old_string != new_string` before calling

## Proven Tool Combos

| Combo | Use Case | Why It Works |
|-------|----------|--------------|
| `web_search` → `web_extract` | Research | Search finds URLs, extract pulls content |
| `execute_code` → `write_file` | Bulk operations | Code generates data, write_file persists |
| `read_file` → `patch` | Surgical edits | Verify exact text before modification |
| `search_files` → `read_file` | Discovery | Find files, then inspect contents |
| `terminal` → `process` | System ops | Terminal for one-offs, process for daemons |

## Token Efficiency Patterns

**High efficiency:**
- `execute_code` with bulk DB operations — replaces 10+ individual tool calls
- `write_file` for full file replacement — avoids patch retry loops
- `read_file` with offset/limit — avoids loading multi-MB files into context

**Low efficiency (avoid):**
- `patch` with ambiguous old_string — causes retry loops, wastes tokens
- `cronjob` with wrong id — fails silently, no progress made
- `delegate_parallel` — 3x failure rate means 3x token waste on retries

## Error Pattern Prediction

The `error_patterns_predictive` table tracks 6 known patterns:

| Pattern | Trigger | Prevention |
|---------|---------|------------|
| `psycopg2_abort` | Multiple INSERTs in loop | Use `execute_many` or wrap each in try/except |
| `patch_identical` | old_string == new_string | Verify strings differ before calling |
| `patch_mismatch` | old_string not found | Read file first, get exact text |
| `delegate_parallel_fail` | Any delegate_parallel usage | Use delegate_task sequential |
| `cronjob_id_missing` | action=create without schedule | Always include schedule param |
| `lcm_table_missing` | Query missing table | Check table exists before querying |

## Building Tool Intelligence

To populate `tool_performance_summary`:
```sql
INSERT INTO tool_performance_summary (tool_name, total_calls, success_count, failure_count, success_rate, last_updated)
SELECT tool_name, COUNT(*), SUM(success), SUM(1-success), AVG(success), UNIX_TIMESTAMP()
FROM tool_calls GROUP BY tool_name;
```

To query routing recommendations:
```python
from predictive_router import get_tool_recommendation
rec = get_tool_recommendation('patch')
# Returns: {'status': 'reliable', 'recommendation': 'use_with_caution', 'success_rate': 0.94}
```
