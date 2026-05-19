# MASTER.md
# MASTER.md


### Current State (2026-05-19)
- **MacBook Hermes**: Default `kimi-for-coding` (cloud), v0.14.0
- **DGX Hermes**: vLLM serving merged Qwen3.6-27B-Uncensored-Final-Merged
- **DGX Endpoint**: http://10.0.0.171:8000/v1
- **Spark-bf16 provider**: model_id = `/data/models/Qwen3.6-27B-Uncensored-Final-Merged`

### Cognitive Subsystem Status
- **Orchestrator**: 21/21 subsystems active (post-recovery)
- **Core modules**: cortex_flywheel, cerebrum, distillation, cognitive_orchestrator functional
- **Stub modules**: 18 created to restore orchestrator compatibility
- **Real module**: agent_scorecard.py created (was completely missing)
- **Last verification**: 2026-05-19, all initialize without errors in fresh process

### Git State
- **Main branch**: `30db4ce9b` (cognitive subsystem fix)
- **Pre-merge backup**: `17dcd0873` (200 files in agent/)
- **Upstream merge**: `d7b2997b1` (v0.14.0, 1641 commits)
- **Files missing post-merge**: 112 from backup (many experimental cognitive modules)
- **Recovery strategy**: Stubs for orchestrator compatibility, real implementations to be restored from backup as needed

### Pending / Watch
- [ ] Restore real implementations of 18 stub modules from pre-merge backup
- [ ] Audit all 112 missing files — identify which are critical vs experimental
- [ ] Add post-merge verification to prevent silent cognitive subsystem failures
- [ ] DGX model serving stable, no changes needed

