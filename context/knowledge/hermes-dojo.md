# hermes-dojo

*Researched: 2026-04-01 22:24 CDT*

# Hermes Dojo — Automated Self-Improvement for Hermes Agent

**Source:** [Yonkoo11/hermes-dojo](https://github.com/Yonkoo11/hermes-dojo) (★3, Hackathon project, March 2026)

## Overview
Hermes Dojo is a self-improvement system that reads session logs, finds recurring failures, and automatically creates or patches skills to fix them. It closes the feedback loop: measure → identify weakness → fix → evolve → verify → report.

## Architecture (5 Components)

### 1. Performance Monitor (`monitor.py`)
- Reads `~/.hermes/state.db` (SQLite session database)
- Identifies failures via regex error patterns: `error:`, `traceback`, `timeout`, `command not found`, `permission denied`, etc.
- Detects user corrections: messages with "no,", "wrong", "I meant", "not what I", "try again", etc.
- Skill gap detection: repeated manual tasks with no skill (CSV parsing, web scraping, etc.)
- Outputs per-tool success/failure rates, error groupings, session metrics

### 2. Weakness Analyzer (`analyzer.py`)
- Takes monitor output and generates ranked improvement recommendations
- Maps tool failures to existing skills (direct name match + fuzzy matching)
- Three recommendation types:
  - **Patch**: Skill exists but fails → add error handling
  - **Create**: No skill for recurring need → generate new one
  - **Evolve**: Skill needs deeper improvement → run GEPA self-evolution
- Priority scoring based on failure frequency and impact

### 3. Auto-Fixer (`fixer.py`)
- Generates structured commands for the agent's `skill_manage` tool
- Does NOT modify skills directly — outputs instructions the agent executes
- Fix strategies catalog: path_not_found, timeout, permission_denied, command_not_found, rate_limit
- Each strategy has: patch description + skill_addition (markdown to append)
- Can trigger self-evolution via `hermes-agent-self-evolution`

### 4. Reporter (`reporter.py`)
- Generates CLI or Telegram reports with deltas, sparklines, and summaries
- Shows before/after scores per skill

### 5. Learning Curve Tracker (`tracker.py`)
- Stores daily metrics in `data/metrics.json`
- Shows improvement over days/weeks — proof the agent is growing

## Key Patterns for SOMA

1. **Error Pattern Catalog**: The regex-based error classification is simple but effective. We can adapt this for TypeScript build errors, medical terminology lookup failures, etc.

2. **Correction Detection**: User messages like "no,", "wrong", "I meant" are strong signals. We should track these and learn from them automatically.

3. **Skill Gap Detection**: If a user asks for the same capability N times without a skill, auto-generate one. Directly applicable to SOMA's expanding medical knowledge.

4. **Fix Strategy Templates**: Predefined fix patterns (retry logic, path validation, timeout handling) are reusable across skills. Better than ad-hoc fixes.

5. **Measure → Fix → Verify Loop**: The key insight is that improvement must be measured. Without metrics, you can't tell if a fix actually helped.

## Commands
- `/dojo analyze` — Analyze recent sessions for failures
- `/dojo improve` — Fix weakest skills + run self-evolution
- `/dojo report` — Generate improvement report
- `/dojo history` — Show learning curve over time
- `/dojo auto` — Set up overnight cron (analyze + improve + report)


## Sources

- https://github.com/Yonkoo11/hermes-dojo
