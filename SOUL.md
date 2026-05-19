# SOUL.md
# SOUL.md

### DGX Model Merge (2026-05-19)
- **Lightweight merge pattern**: When merging large LoRA into base on memory-constrained systems, use shard-by-shard safetensors processing instead of loading full model
- **Vision-safe merge**: Verify LoRA target modules (`q/k/v/o/gate/up/down_proj`) have zero overlap with vision layers (`visual.*`) before merging
- **vLLM model ID**: vLLM serves models by their filesystem path, not short names. Always use full path in `model_id`
- **Config isolation**: MacBook and DGX Hermes instances need separate profiles to avoid accidentally swapping default models

### Upstream Merge Survival (2026-05-19)
- **Verify after every upstream merge**: Run `git diff HEAD~1 -- agent/ | wc -l` to check if custom modules were overwritten
- **Cognitive subsystem audit**: After merge, run orchestrator init in fresh Python process and verify 21/21 subsystems actually load (not just report "active")
- **Silent failure pattern**: Missing modules log as `WARNING` not `ERROR`, so health checks pass while subsystems are dead
- **Singleton trap**: `CognitiveOrchestrator` is a singleton — once initialized with failed imports, it caches failed state forever unless singleton is cleared
- **Backup discipline**: Always create pre-merge backup commit (like `17dcd0873`) — upstream merges can delete 100+ custom files silently

### Module Recovery Pattern
- When orchestrator reports `<N>/21 active`, check `agent/` for missing modules vs pre-merge backup
- Create stubs with correct `__init__` signatures matching what `cognitive_orchestrator.py` imports
- Clear singleton: `CognitiveOrchestrator._instance = None` before re-testing
- Verify in subprocess (fresh Python process) to avoid import caching

### Cognitive Pipeline — Full Implementation (2026-05-19)
- **SelfEvaluationGate**: Real 5-dimension quality scoring (accuracy, completeness, clarity, safety, reasoning) with SQLite persistence. Thresholds: ≥70% for complex tasks, ≥50% for simple. Blocks sub-threshold responses.
- **IterationEngine**: Turn-by-turn experiential learning loop. `before_action()`/`after_action()` wired into `conversation_loop.py` at every turn. 45+ experiences recorded in SQLite.
- **CognitiveOrchestrator**: 21/21 subsystems active. All 15 previously-stub modules now have real methods (brain, self_audit, training_gym, tiered_memory, memory_cortex_bridge, distillation_bridge, error_learning, skill_effectiveness_tracker, autobrowse_tracer, tool_oracle, unified_intelligence_engine, predictive_failure_prevention, autonomous_experimentation, cross_domain_transfer, attention_context_prioritizer).
- **Conversation Loop Hooks**: 4 cognitive injection points wired:
  1. Pre-turn evaluation gate check (line ~522)
  2. Turn-by-turn learning feedback — iteration engine before/after each action (line ~612)
  3. Adaptive context injection — appends cognitive insights to ephemeral system prompt without breaking prompt cache (line ~820)
  4. Post-turn quality evaluation + self-audit + training gym exercise + session end (lines ~3931, ~4168)
- **MegaWiring**: `wire_all()` patches `AIAgent.__init__` to forward to `agent_init.py::init_agent()`. All cognitive init lives in `agent_init.py`, not the forwarder.
- **Config**: `agent.verbose=True`, `display.tool_progress_command=True`, `display.show_reasoning=True`, `display.interim_assistant_messages=True`. All cognitive sections enabled in `cognitive_orchestrator`, `cortex`, `cerebrum`, `distillation`, `metrics`, `vector_memory`, `code_intelligence`, `cache`.
- **Verification command**: `python3 -c "from agent.cognitive_orchestrator import get_orchestrator; o=get_orchestrator(); print(sum(1 for v in o.initialize(type('A',(),{'session_id':'x','model':'x','provider':'x','quiet_mode':True})()).values() if v=='active'))"` should print `21`
