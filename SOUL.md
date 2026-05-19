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


