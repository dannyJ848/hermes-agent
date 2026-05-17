# Cycle 6 Wiring and Schema Fixes — May 2026

## Novel Systems Built (Cycle 6)

All files in `~/subconscious/` (not `hermes_cli/subconscious/`):

| System | File | Table | Status |
|--------|------|-------|--------|
| InjectionGovernorV2 | `cognitive_infrastructure_v2.py` | `tip_injection_attempts` | Wired but logging at wrong place — 0 rows |
| CreditAssigner | `cognitive_infrastructure_v2.py` | `skill_rewards` | 3 rows (test data only) |
| SessionEndExtractor | `cognitive_infrastructure_v2.py` | `session_rapid_extractions` | 1 row (test data) |
| ToolIntelligenceRouter | `tool_intelligence_integration.py` | `tool_routing_decisions` | 8 rows |
| AutoSkillCron | `cognitive_infrastructure_v2.py` | `auto_skill_pipeline` | 10 pending docs |

## Hook Wiring Reality

The hooks were wired into `~/.hermes/plugins/distillation/__init__.py` (281KB), not `plugins.py`:

```python
# Lines ~90-120 in distillation/__init__.py
import sys
sys.path.insert(0, str(Path.home() / 'subconscious'))

# pre_llm_call: ToolIntelligenceRouter warns, CreditAssigner records injection
# post_tool_call: CreditAssigner records outcome, ToolRouter logs decision
# session_end: SessionEndExtractor extracts lessons
```

**Critical bug**: GovernorV2 logging was added BEFORE injection lines are assembled. Actual injection happens later in the function. Result: `tip_injection_attempts` has 0 rows despite attempts being made.

## Tool Intelligence Schema (Actual)

Database: `~/.hermes/tool_intelligence.db`

**Tables:**
- `tool_calls` — raw call log (tool_name, success, duration_ms, tokens_in, tokens_out, error_type, error_msg, timestamp)
- `tool_stats` — aggregated stats (tool_name, total_calls, success_count, failure_count, avg_duration_ms, avg_tokens_in, avg_tokens_out, last_used, failure_rate, confidence_score)
- `tool_performance_summary` — summary view

**NOT `tool_success_rates`** — that table does not exist.

**Columns in `tool_stats`:**
```
tool_name, total_calls, success_count, failure_count, avg_duration_ms,
avg_tokens_in, avg_tokens_out, last_used, failure_rate, confidence_score
```

**NOT `avg_duration`** — column is `avg_duration_ms`.

## Current Tool Performance (May 9, 2026)

| Tool | Success | Calls | Status |
|------|---------|-------|--------|
| terminal | 100% | 1085 | ✅ Proven |
| skill_manage | 100% | 327 | ✅ Proven |
| skill_view | 100% | 201 | ✅ Proven |
| execute_code | 99% | 176 | ✅ Proven |
| read_file | 100% | 141 | ✅ Proven |
| patch | 97% | 95 | ✅ Proven |
| memory | 100% | 64 | ✅ Proven |
| write_file | 100% | 60 | ✅ Proven |
| search_files | 100% | 55 | ✅ Proven |
| skills_list | 100% | 38 | ✅ Proven |
| vision_analyze | 40% | 10 | ❌ Weak — removed GLM |
| cronjob | 17% | 41 | ❌ Weak — avoid |

## Key Decisions

1. **GLM removed from vision** — user directive, no replacement yet
2. **Qwen 27B training** — step 5320/10000, ETA ~26h, will be local vision provider
3. **Hands system operational** — but blind without vision verification
4. **InjectionGovernorV2 bug** — needs fix: move logging AFTER injection assembly
5. **CreditAssigner** — only works during agent LLM turns, not direct tool calls
