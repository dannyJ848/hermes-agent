# May 3 2026: Flywheel Cleanup Session

## Problem
Cortex flywheel daemon was dead for 256 hours. 405 of 529 subconscious modules (76.6%) were orphaned — never wired into the distillation plugin. 51 flywheel cycles stuck in "running" state, accumulating over time.

## Root Causes
1. **API mismatch**: `cortex_daemon.py` called non-existent method on flywheel object
2. **Missing column**: `cycle_id` not in `cortex_flywheel` table
3. **Column name mismatch**: `record_eval` in `cortex_access.py` used wrong field names
4. **Bytecode cache**: Old `.pyc` files causing stale imports

## Fixes Applied
1. Split flywheel sweep into three real calls (eval, repair, distill)
2. Added `cycle_id` column to table
3. Aligned `record_eval` column names
4. `PYTHONDONTWRITEBYTECODE=1` to prevent cache issues
5. **Auto-cleanup**: Scheduler daemon now kills cycles >30min old every 10 ticks

## Benchmark Results (Post-Fix)
| Metric | Value |
|--------|-------|
| Total eval history | 204,511 |
| Evaluations (24h) | 1,466 |
| Nodes | 66,310 |
| Edges | 369,260 |
| Completed cycles | 7,793 |
| Stuck cycles (after cleanup) | 3 |

## Top Nodes by Elo
- 7a3c21c6 | reasoning | elo=3122 | 7174 matches
- 44f2ab77 | reasoning | elo=3118 | 2793 matches
- e1b05066 | reasoning | elo=3104 | 4254 matches

## Key Script
`scripts/hermes_scheduler_daemon.py` — runs cron tick() every 60s + auto-cleanup every 10min.

## Repo State
- `dannyJ848/hermes-agent:main` — 7 upstream commits merged
- `dannyJ848/hermes-agent:hermes-config` — loop guard + scheduler daemon + README
