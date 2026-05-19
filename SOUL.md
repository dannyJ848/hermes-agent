# SOUL.md



### DGX Model Merge (2026-05-19)
- **Lightweight merge pattern**: When merging large LoRA into base on memory-constrained systems, use shard-by-shard safetensors processing instead of loading full model
- **Vision-safe merge**: Verify LoRA target modules (`q/k/v/o/gate/up/down_proj`) have zero overlap with vision layers (`visual.*`) before merging
- **vLLM model ID**: vLLM serves models by their filesystem path, not short names. Always use full path in `model_id`
- **Config isolation**: MacBook and DGX Hermes instances need separate profiles to avoid accidentally swapping default models

