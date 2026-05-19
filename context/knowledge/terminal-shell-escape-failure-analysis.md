# terminal-shell-escape-failure-analysis

*Researched: 2026-04-04 23:20 CDT*

# Terminal Shell Escape Failure Analysis (Cycle 7)

## Problem
Terminal tool has 10% success rate (364/3438 successes, 67 failures, 492 partials).
This is the #1 engineering bottleneck — "brain growth not translating to better hands."

## Root Causes (ranked by frequency)
1. **Heredoc/quote escaping** (dominant): python3 -c with multi-line code, heredocs, nested quotes mangled by bash
2. **tcsetattr noise** (2 cases): macOS shell noise causing false failure classification
3. **Empty output + exit_code 1** (4 cases): Commands that produce no output but fail silently
4. **SQLite schema mismatches** (3 cases): Querying columns/tables that don't exist

## Fix: safe_terminal.py Module
Created ~/subconscious/safe_terminal.py with:
- `classify_terminal_result()`: Distinguishes real failures from shell noise
- `get_safe_terminal_advice()`: Pre-call safety check for dangerous patterns
- `recategorize_recent_failures()`: Fixes misclassified failures in call_log

## Behavioral Rules (for agent)
1. NEVER use `python3 -c` with multi-line code — use `execute_code` tool
2. NEVER use heredocs (<<EOF) with Python — use `write_file` + `terminal(bash file)`
3. For any Python logic — use `execute_code` tool (handles escaping)
4. For simple shell commands — use `terminal` directly
5. For complex shell — write to /tmp/script.sh, then `bash /tmp/script.sh`

## Key Metrics
- Engineering success rate: 10.7% (13/121)
- Terminal confidence: 0.10
- Lesson utilization rate: 27.9% (lessons aren't being applied)

## Sources

- ~/subconscious/tool_capability.db
- ~/subconscious/audits/2026-04-04_2302.json
