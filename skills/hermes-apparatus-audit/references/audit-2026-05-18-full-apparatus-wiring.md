# Full Apparatus Wiring and Performance Audit — May 18, 2026

## Scope
Line-by-line verification of the entire integrated Hermes cognitive apparatus across MacBook and DGX.

## MacBook State
- **Commit**: 7f6281ca9 → bf0c4337f (after persistence update)
- **Skills**: 384 SKILL.md (91 builtin + 293 local)
- **Tools**: 27 shown by CLI (15 enabled + 12 disabled)
  - Actual: 31 implemented tool functions
  - Aliases: 76 in toolsets.py
  - Unimplemented: 60 aliases without backing functions
- **Agent modules**: 200 Python files
- **Tool modules**: 111 Python files
- **Cognitive systems**: 21 total
  - 20 subsystems in cognitive_orchestrator.py
  - Plus iteration_engine.py wired separately in run_agent.py

## DGX State
- **Location**: /data/SpecForge/hermes-agent
- **Commit**: 7f6281ca9 (synced with MacBook before persistence update)
- **Python**: 3.12.3 with venv
- **Hermes**: v0.13.0
- **Skills**: 385 (1 more than MacBook — likely temp file)
- **Tools**: ~50 enabled (full evey plugin suite)
- **Cognitive**: All 21 subsystems present and wired

## Cognitive Subsystem Verification

### Files Present
| File | Lines | Bytes | Status |
|------|-------|-------|--------|
| agent/cognitive_orchestrator.py | ~1,000 | 41,829 | ✅ Imports 20 subsystems |
| agent/iteration_engine.py | 671 | 28,961 | ✅ Wired in run_agent.py |
| agent/cortex_flywheel.py | 428 | 16,501 | ✅ In orchestrator |
| agent/agent_scorecard.py | 317 | 9,761 | ✅ In orchestrator |
| agent/red_team_hippocampus.py | 757 | 29,503 | ✅ In orchestrator |
| agent/tool_misuse_prevention.py | 156 | 5,592 | ✅ In orchestrator |
| agent/memory_cortex_bridge.py | 465 | 17,076 | ✅ In orchestrator |
| agent/hermes_enhancement_suite.py | 370 | 14,054 | ✅ In orchestrator |

### Wiring in run_agent.py
- Line 2130: `from agent.cognitive_orchestrator import initialize_cognitive_systems`
- Line 2131: `self.cognitive_orchestrator = initialize_cognitive_systems(self)`
- Lines 10091-10211: `before_action` and `after_action` hooks in tool execution loop
- Lines 10757, 11009: iteration_engine before/after action hooks
- Lines 11531-12170: `invoke_hook` calls for pre_llm_call, post_tool_call

### 20 Orchestrator Subsystems
1. tiered_memory — 3-tier memory with overflow
2. error_learning — Error pattern extraction
3. skill_tracker — Skill quality tracking
4. brain — ParallelBrain 6-phase cycle
5. cortex_flywheel — Continuous learning flywheel
6. distillation_bridge — Research-to-distillation pipeline
7. self_audit — Post-session quality scoring
8. training_gym — Continuous self-improvement loop
9. memory_bridge — Memory-cortex bidirectional sync
10. subconscious — Hook registration system
11. autobrowse_tracer — Execution tracing
12. context_sculptor — Adaptive context shaping
13. tool_oracle — Predictive tool routing
14. trust_scorer — Epistemic trust scoring
15. unified_intelligence — Cross-system analytics
16. failure_prevention — Before-action risk scoring
17. experimentation — Self-directed learning loop
18. domain_transfer — Pattern generalization across domains
19. attention_prioritizer — Relevance-based memory injection
20. evaluation_gate — Self-evaluation quality gate

Plus iteration_engine (wired separately in run_agent.py) = 21 total

## False Alarm Clarification
Earlier audit reported cognitive systems "unwired" because `hermes_cli/main.py` doesn't import them. This is expected — `hermes_cli/main.py` is just the CLI wrapper. The actual agent runtime in `run_agent.py` correctly initializes all 21 subsystems. Both MacBook and DGX have identical, functioning wiring.

## Tool Count Clarification
- `discover_builtin_tools()` loads 28 modules
- 31 actual tool functions with `task_id` parameter
- 76 aliases in toolsets.py
- 60 aliases without implementation
- 15 internal helpers not exposed
- Old "92 tools" was from fully-configured setup with all API keys

## Performance Notes
- run_agent.py: 784,787 bytes (old v0.13 architecture with hooks)
- Upstream run_agent.py: 178,046 bytes (new architecture without hooks)
- The size difference reflects the hook infrastructure and cognitive integration

## Key Finding
The cognitive orchestrator requires `invoke_hook`, `before_action`, `after_action` infrastructure in run_agent.py. Upstream (8,722 commits ahead) removed this infrastructure. Updating to upstream would break all 21 cognitive subsystems.
