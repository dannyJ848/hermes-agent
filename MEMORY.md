# MEMORY.md


## DGX Qwen3.6-27B-Uncensored Integration (2026-05-19)

- **Model**: Qwen3.6-27B-Uncensored-Final-Merged (109.4 GB, 15 shards)
- **Location**: `/data/models/Qwen3.6-27B-Uncensored-Final-Merged`
- **Base**: `/data/models/Qwen3.6-27B-Uncensored` (Qwen3_5ForConditionalGeneration)
- **LoRA**: Rank-256 adapter from `/data/SpecForge/custom_dflash/checkpoints/final_model/`
- **Merge method**: Lightweight shard-by-shard CPU merge (safetensors direct)
- **Vision**: Fully preserved (270 visual keys confirmed in output)
- **vLLM**: Port 8000, host 0.0.0.0, BF16 native, FP8 KV cache
- **Tool parser**: `qwen3_xml`
- **Speed**: ~3.4 tok/s generation, 1-2s TTFT (GB10 GPU-bound)
- **Start script**: `/data/models/start_qwen27b_merged.sh`

### Critical Config Notes
- vLLM only recognizes full path model ID: `/data/models/Qwen3.6-27B-Uncensored-Final-Merged`
- Short names like `final-model` or `qwen3.6-27b-uncensored` return 404
- All `model_id` fields in spark-bf16 provider must use full path
- MacBook default model: `kimi-for-coding` / `kimi-coding` (cloud)
- DGX model accessed via `spark-bf16` provider when needed

### Merge Process (for reference)
1. CPU merge via `peft` → OOM killed at 63GB RAM
2. GPU merge via `merge_and_unload()` → hung, DGX crashed
3. **Working solution**: Lightweight shard-by-shard safetensors merge
   - Processes each shard independently
   - No full model load into RAM
   - 15 shards processed, config copied from base
   - 270 vision keys verified present

