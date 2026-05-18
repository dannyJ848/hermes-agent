# SGLang + Qwen3.6-27B Hybrid Mamba/SSD Incompatibility

**Date:** May 15, 2026
**SGLang version tested:** v0.5.11 (Docker image `lmsysorg/sglang:latest`, 30.4GB)
**Model:** Qwen3.6-27B-Uncensored (hybrid architecture: 48 Mamba/SSD layers + 16 full-attention layers)
**Status:** BLOCKED — weight loading hangs indefinitely

## Symptom

SGLang container launches, model directory is found, but hangs at "Load weight begin" with memory frozen at ~52GB. No error messages, no crash, no progress after 5+ minutes.

```
INFO 05-15 00:39:33 [model_runner.py:123] Load weight begin.
# ... hangs here indefinitely ...
```

## Root Cause

Qwen3.6-27B uses a **hybrid Mamba/SSD + attention architecture** (`Qwen3_5ForConditionalGeneration` class in transformers). The model has:
- 48 GDN (Gated Delta Net) / Mamba / SSD layers
- 16 full self-attention layers

SGLang v0.5.11 has a `qwen3_5` model module and recognizes `Qwen3_5ForCausalLM`, but the **weight loader does not fully support hybrid Mamba/SSD architectures**. The weight loading process silently stalls when encountering the GDN/Mamba layer weights.

## Verification Steps

```bash
# Check SGLang has qwen3_5 module
docker run --rm lmsysorg/sglang:latest python3 -c "from sglang.srt.models import qwen3_5; print('qwen3_5 module exists')"

# Check model class
python3 -c "from transformers import AutoConfig; c = AutoConfig.from_pretrained('/data/models/Qwen3.6-27B-Uncensored'); print(c.architectures)"
# Output: ['Qwen3_5ForConditionalGeneration']

# Check SGLang recognizes the class
docker run --rm lmsysorg/sglang:latest python3 -c "
from sglang.srt.models.qwen3_5 import Qwen3_5ForCausalLM
print('Qwen3_5ForCausalLM class exists')
"
```

All checks pass — SGLang has the module and class. The issue is in the weight loader, not model registration.

## Deep Investigation: Why SGLang Fails (May 15, 2026)

A systematic investigation traced the failure from config mismatch through weight format incompatibility.

### Step 1: Config Mismatch — `layers_block_type` vs `layer_types`

SGLang's `Qwen3_5ForCausalLM.__init__` expects `config.layers_block_type`, but Qwen3.6-27B provides `config.layer_types`:

```python
# Qwen3.6-27B config
layer_types: ["linear_attention", "linear_attention", "linear_attention", "full_attention", ...]  # 64 entries

# SGLang expects
layers_block_type: ["attention", "linear_attention", ...]  # "attention" not "full_attention"
```

**Patchable:** Monkey-patch `AutoConfig.from_pretrained` to set `layers_block_type = layer_types` with `full_attention` → `attention` mapping. Also add `rope_theta` (missing in config).

### Step 2: Layer Type KeyError — `full_attention` not in `ALL_DECODER_LAYER_TYPES`

SGLang's `ALL_DECODER_LAYER_TYPES` only has `{"attention": ..., "linear_attention": ...}`. Qwen3.6 uses `"full_attention"` in its layer type list.

**Patchable:** Add `"full_attention"` as alias for `"attention"`:
```python
qwen_module.ALL_DECODER_LAYER_TYPES['full_attention'] = qwen_module.ALL_DECODER_LAYER_TYPES['attention']
```

### Step 3: Parallel State Initialization Requirements

SGLang's model constructor requires initialized distributed environment, global server args, and DP attention state. These are normally set up by `sglang.launch_server`, not available when instantiating the model class directly:

```python
# Required initialization sequence
torch.distributed.init_process_group(backend='gloo', rank=0, world_size=1)
init_distributed_environment(backend='gloo', world_size=1, rank=0, local_rank=0, ...)
initialize_model_parallel(tensor_model_parallel_size=1, pipeline_model_parallel_size=1)
# Set _global_server_args internally
# Initialize DP attention with ServerArgs + ModelConfig
```

**Patchable:** Initialize all subsystems manually before model creation.

### Step 4: Weight Format Mismatch — THE BLOCKER

After all patches above, the model instantiates successfully (25.6B parameters, 754 params). However, **checkpoint weights cannot be loaded** because the weight formats are fundamentally different:

| Component | Checkpoint Format | SGLang Expects |
|-----------|------------------|----------------|
| Linear attention QKV | `in_proj_qkv` + `in_proj_z` (separate tensors) | `in_proj_qkvz` (single merged tensor) |
| Linear attention BA | `in_proj_b` + `in_proj_a` (separate tensors) | `in_proj_ba` (single merged tensor) |
| Attention QKV | `q_proj`, `k_proj`, `v_proj` (separate) | `qkv_proj` (merged) |
| MLP gate+up | `gate_proj`, `up_proj` (separate) | `gate_up_proj` (merged) |

**Example mismatch:**
```
Checkpoint has: model.layers.0.linear_attn.in_proj_qkv.weight
                model.layers.0.linear_attn.in_proj_z.weight
SGLang expects: layers.0.linear_attn.in_proj_qkvz.weight

Checkpoint has: model.layers.3.self_attn.q_proj.weight
                model.layers.3.self_attn.k_proj.weight
                model.layers.3.self_attn.v_proj.weight
SGLang expects: layers.3.qkv_proj.weight
```

The checkpoint has **1199 weight tensors**; SGLang's model has **754 parameters**. The difference is exactly the split-vs-merged weight formats.

**NOT patchable without weight conversion:** SGLang's `load_weights` has a `stacked_params_mapping` that handles merging for Qwen3.5 checkpoints, but Qwen3.6 uses a **different split pattern** (`qkv`+`z` and `b`+`a` for linear attention, vs SGLang's expected `qkvz` and `ba`).

### Step 5: Kernel Interface Risk

Even if weights were converted offline, SGLang's `Qwen3_5GatedDeltaNet` uses custom CUDA kernels (`fused_qkvzba_split_reshape_cat_contiguous`, `RadixLinearAttention`) that expect specific tensor layouts. The merged `in_proj_qkvz` tensor layout may differ from what the kernels expect.

## Attempted Workarounds (All Failed)

| Attempt | Result |
|---------|--------|
| Simplified config (no FP8, no torch compile, no LoRA) | Same hang |
| `--trust-remote-code` | Same hang |
| Foreground run with 90s timeout | Timed out after 120s |
| Different `--mem-fraction-static` values | Same hang |
| Config patches (`layers_block_type`, `rope_theta`) | Model creates, weights don't load |
| Layer type alias (`full_attention` → `attention`) | Model creates, weights don't load |
| Parallel state + server args initialization | Model creates, weights don't load |
| Weight key remapping (`model.language_model.` → `model.` → strip `model.`) | 0 parameters loaded — format mismatch |
| Offline weight conversion (theoretical) | Not attempted — estimated 30-50% success even after conversion |

## GPU Memory Impact

The SGLang process that hangs holds **~100GB of GPU memory** and does NOT release it when the container is stopped/removed:

```bash
# After 'docker rm -f sglang', process still holds GPU memory
nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader
# Output: 286687, sglang::scheduler, 100626 MiB
```

**Cleanup required:**
```bash
# docker rm -f is NOT sufficient
sudo kill -9 <PID>  # Must kill the sglang::scheduler process directly
# Then verify with nvidia-smi
```

## Working Alternative

**Use vLLM instead.** vLLM 0.20.2+ fully supports Qwen3.6-27B hybrid architecture with:
- Native SM121 kernels
- FlashAttention v2
- GDN Triton allocator
- Working speculative decoding (n-gram)
- Tool calling (`qwen3_xml` parser)
- LoRA adapter serving

See `qwen27b-dgx-deployment` skill for working vLLM configuration.

## When SGLang Might Work

SGLang may work for Qwen3.6 models in these scenarios:
- **Pure attention models** (not hybrid Mamba/SSD) — e.g., dense Qwen variants
- **Future SGLang versions** that add explicit Qwen3.6 hybrid architecture support with proper weight format handling
- **With EAGLE-3 speculative decoding** — but draft model must also be compatible

## Recommendation

For Qwen3.6-27B and similar hybrid Mamba/SSD models on DGX Spark:
1. **Use vLLM as primary inference engine** — proven working, full feature support
2. **Do NOT attempt SGLang** until explicit hybrid architecture support is documented
3. **If testing SGLang**, always verify GPU memory cleanup afterward — hung processes hold VRAM
4. **Weight format mismatch is the fundamental blocker** — not just a config issue

## Related

- `dgx-spark-qwen3-deployment:references/vllm-speedup-landscape-may15-2026.md` — vLLM vs SGLang feature comparison
- `qwen27b-dgx-deployment` skill — Working vLLM deployment with LoRA + tool calling
- `dgx-spark-qwen3-deployment:references/apr21-performance-audit-findings.md` — SGLang on GB10 (working for non-hybrid models)
- `dgx-spark-qwen3-deployment:references/sglang-qwen36-community-verification.md` — **Community-wide verification that NO ONE has successfully served Qwen3.6-27B (dense) with SGLang. GitHub issues #23687, #24589, #24364, HF Discussion #5, Reddit, NVIDIA forums all confirm non-functional. Weight format mismatch + string-mutation bug in qwen3_5.py loader.**
