# reasoning-analysis-debugging-failure-patterns-cycle6

*Researched: 2026-04-04 23:08 CDT*

# Reasoning Analysis: Debugging Failure Patterns (Cycle 6)

## Summary
Analysis of 204 reasoning traces revealed that **debugging is the weakest reasoning dimension** with catastrophic failure rates.

## Key Findings

### 1. Debugging: 20.5% Success Rate
- **39 debugging traces**, only 8 succeeded (20.5%)
- Average depth: 1.1 (reflexive single tool call)
- Every single failure used only `terminal` tool
- Calibration error: 0.49 (confident at 50%, actual 20%)

### 2. Tool Misuse is #1 Failure Mode
- 16 of 19 recorded failures are `tool_misuse`
- Root cause: attempting GUI-dependent commands in headless environment
- Top failing commands: `screencapture`, `osascript`, `tesseract`, `cliclick`, `sips`

### 3. Successful Debugs Are Simple Lookups
- Successful: `which`, `file`, `wc`, `sqlite3`, `head` — read-only queries
- Failed: Interactive operations, GUI tools, pip install, permission changes

### 4. Research Performs Adequately (83.9% success)
- But depth remains 1.03 — no multi-step reasoning chains
- Room for improvement in research depth

## Fix Implemented: `debugging_preflight()` Method
Added to `~/subconscious/reasoning_analyzer.py`:
- Pre-checks sandbox compatibility before running commands
- Queries past success rates from reasoning_traces database
- Provides structured alternatives when risk is HIGH
- Forces minimum depth requirement (3 steps)

## Impact Prediction
If the pre-flight protocol is followed, debugging success should increase from ~20% to ~60%+ by:
1. Eliminating all sandbox-blocked commands (currently ~80% of failures)
2. Forcing deeper investigation (depth 1.1 → 3+)
3. Providing safe alternatives (read_file, search_files, execute_code)

## CLI Usage
```bash
python3 ~/subconscious/reasoning_analyzer.py preflight "screencapture -x /tmp/test.png"
```

## Skill Updated
`systematic-debugging` skill patched with Pre-Flight Environment Check section.


## Sources

- ~/subconscious/reasoning_analyzer.py
- ~/subconscious/brain.db reasoning_traces table
