# Subconscious Systems Catalog

Complete inventory of cognitive systems built for Hermes Agent self-improvement.

## Systems by Category

### Memory Management
| System | File | Purpose | Hook |
|--------|------|---------|------|
| Memory Cortex Bridge | `memory_cortex_bridge.py` | Auto-offload to cortex DB | pre_tool_call |
| Proactive Memory Guard | `proactive_memory_guard.py` | Offload BEFORE adding | memory_add_guard |
| Tiered Memory | `tiered_memory.py` | HOT/WARM/COLD tiers | Background |
| Memory Daemon | `memory_daemon.py` | Background consolidation | Cron |

### Error Handling
| System | File | Purpose | Hook |
|--------|------|---------|------|
| Error Pattern Miner | `error_pattern_miner.py` | Classify errors, generate tips | post_tool_call |
| Auto Fallback Engine | `auto_fallback_engine.py` | Retry with alternatives | post_tool_call |
| Smart Tool Router | `smart_tool_router.py` | Route around weak tools | pre_tool_call |

### Context Management
| System | File | Purpose | Hook |
|--------|------|---------|------|
| Context Window Guard | `context_window_guard.py` | Prevent overflow | pre_llm_call |
| Auto Compressor | `auto_compressor.py` | Compress at 75% threshold | pre_llm_call |
| Session Continuity | `session_continuity_engine.py` | Preserve across death | Session start/end |

### Quality & Intelligence
| System | File | Purpose | Hook |
|--------|------|---------|------|
| Tool Intelligence Tracker | `tool_intelligence_tracker.py` | Track tool performance | pre/post_tool_call |
| Distillation Quality Gate | `distillation_quality_gate.py` | Validate tips | post_llm_call |
| LLM Judge | `llm_judge.py` | Auto-evaluate tips | Background |
| Self Audit Engine | `self_audit_engine.py` | Health checks | Cron |

### Optimization
| System | File | Purpose | Hook |
|--------|------|---------|------|
| Hermes Enhancement Suite | `hermes_enhancement_suite.py` | Retry, circuit breaker, cache | All hooks |
| Agent Loop Optimizer | `agent_loop_optimizer.py` | Optimize core loop | Agent init |

### Monitoring
| System | File | Purpose | Trigger |
|--------|------|---------|---------|
| Auto Launch Monitor | `auto_launch_monitor.py` | Watch/restart processes | Cron |
| Checkpoint Watcher | `checkpoint_watcher_daemon.py` | Training monitoring | Cron |

### Integration
| System | File | Purpose |
|--------|------|---------|
| Subconscious Hook Wiring | `subconscious_hook_wiring.py` | Wire all into 5 hook points |
| Cortex Access | `cortex_access.py` | DB interface |
| Cortex Flywheel | `cortex_flywheel.py` | Training feedback loop |

## Tool Performance Data (May 2026)

```
PROVEN (use freely):
  browser_console: 95% (150 calls)
  web_extract: 94% (180 calls)
  execute_code: 92% (500 calls)
  write_file: 88% (600 calls)
  process: 86% (350 calls)
  terminal: 86% (400 calls)
  read_file: 90% (800 calls)

CAUTION (verify results):
  web_search: 72% (120 calls)
  patch: 65% (200 calls)

AVOID (substitute):
  cronjob: 13% (31 calls) → use terminal
  skill_manage: 57% (482 calls) → use write_file for pinned skills
```

## Integration Points

### plugins.py
- `pre_tool_call`: Memory bridge, tool router, intelligence tracking
- `post_tool_call`: Error mining, quality gate, circuit breaker update

### model_tools.py
- `pre_llm_call`: Context guard, compressor, memory injection
- `post_llm_call`: Quality scoring, distillation trigger
- `transform_tool_result`: Caching, truncation, formatting

## File Locations

All systems in: `/Users/dannygomez/hermes-agent/hermes_cli/subconscious/`

Integration hooks in:
- `/Users/dannygomez/hermes-agent/hermes_cli/plugins.py`
- `/Users/dannygomez/hermes-agent/model_tools.py`
