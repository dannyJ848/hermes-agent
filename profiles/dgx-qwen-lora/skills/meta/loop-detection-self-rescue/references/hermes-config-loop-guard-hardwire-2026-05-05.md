# Hardwired Loop Guard in Hermes Config — May 5, 2026

## What Happened
User said "hardwire into hermes config yaml" and "hardwire it into config" — they wanted loop guard settings permanently embedded in `~/.hermes/config.yaml`, not just suggested.

## Exact Settings Applied

### 1. Agent-level loop guard (`agent.loop_guard`)
```yaml
agent:
  loop_guard:
    enabled: true
    max_consecutive_identical_calls: 3
    max_total_calls_per_turn: 16
    hard_stop_after_calls: 16
    detect_repeated_patterns: true
    pattern_window_size: 5
    cooldown_after_trigger_ms: 500
```

### 2. Tool loop guardrails (`tool_loop_guardrails`)
```yaml
tool_loop_guardrails:
  warnings_enabled: true
  hard_stop_enabled: true
  warn_after:
    exact_failure: 2
    same_tool_failure: 3
    idempotent_no_progress: 2
  hard_stop_after:
    exact_failure: 3
    same_tool_failure: 5
    idempotent_no_progress: 3
```

### 3. Delegation hard stop (`delegation.hard_stop`)
```yaml
delegation:
  hard_stop:
    enabled: true
    max_tool_calls: 16
    max_consecutive_same_tool: 3
    max_repeated_pattern: 5
    action: stop_and_report
```

### 4. Code execution loop guard (`code_execution.loop_guard`)
```yaml
code_execution:
  loop_guard:
    enabled: true
    max_repeated_terminal_calls: 3
    max_repeated_file_calls: 3
    hard_stop_after: 16
    detect_circular_patterns: true
```

## Commands Used
```bash
hermes config path                          # Find config location
hermes config check                         # Check config status
hermes config migrate                       # Migrate to latest version
```

## Key Lesson
When user says "hardwire into config", they mean ACTUALLY PATCH THE FILE, not suggest settings. Use `patch` tool on `~/.hermes/config.yaml` directly.