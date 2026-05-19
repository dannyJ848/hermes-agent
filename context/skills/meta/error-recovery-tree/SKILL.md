---
name: error-recovery-tree
description: Pattern-matching error recovery decision tree. Classifies errors by markers and returns diagnosis + action + priority.
version: 1.0
---

# Error Recovery Decision Tree

## When to Use
Whenever a tool call fails and you need to quickly diagnose the error type and recovery strategy.

## Usage
```python
from subconscious.error_decision_tree import diagnose_error

result = diagnose_error(tool_name, error_type, error_msg)
# Returns: {diagnosis, action, priority, matched}
```

## Known Patterns (15 total)
| Pattern | Markers | Priority | Prevention |
|---------|---------|----------|------------|
| pycache | __pycache__, .pyc, modulenotfound | high | Clear cache, restart |
| auth_401 | 401, unauthorized, api_key | high | Check key, rotate |
| auth_403 | 403, forbidden, cloudflare | medium | Check permissions |
| payment_402 | 402, credit, balance, quota | medium | Switch provider |
| timeout | timeout, connection refused | medium | Retry with backoff |
| not_found | filenotfound, does not exist | low | Verify path |
| wrong_args | typeerror, unexpected keyword | medium | Check schema |
| empty_result | 0 results, no matches | low | Broaden query |
| json_parse | json, decodeerror | medium | Validate output |
| psycopg2_abort | psycopg2, abort, failed INSERT | high | Use execute_many, wrap each insert |
| patch_identical | old_string == new_string | low | Verify strings differ |
| patch_mismatch | Could not find match, old_string | medium | Read file first, get exact text |
| delegate_parallel_fail | delegate_parallel, frequent failure | high | Use delegate_task sequential |
| cronjob_id_missing | cronjob, id, missing schedule | medium | Always include schedule param |
| lcm_table_missing | no such table, summaries | low | Check table exists before query |

## Pre-emptive Error Guard
Before executing a tool call, check against known patterns:

```python
from error_guard import check_tool_call

warning = check_tool_call('patch', {'old_string': 'foo', 'new_string': 'foo'})
if warning:
    print(f"Predicted failure: {warning['predicted_error']}")
    print(f"Prevention: {warning['prevention']}")
```

## Accuracy
- Known patterns: 90% (9/10 test cases)
- Novel errors: ~50% (falls back to type-based classification)
- Pre-emptive guard: ~70% (catches common mistakes before execution)

## Pitfalls
- Word-based matching can miss semantic equivalents ("key expired" won't match "token expired")
- When diagnosis returns "Unknown", escalate to manual investigation
- The payment_402 pattern triggers automatic provider fallback in auxiliary_client.py
- **Pre-emptive guard requires maintaining error_patterns_predictive table** — add new patterns as they are discovered
- **Tool intelligence database must be populated** — predictive routing only works after 5+ calls per tool
