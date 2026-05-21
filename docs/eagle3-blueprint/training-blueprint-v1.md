# EAGLE-3 Draft Model Training Blueprint
## Qwen3.6-27B-Uncensored on DGX Spark GB10

**Version**: 1.0  
**Date**: May 21, 2026  
**Status**: Ready for implementation

---

## Executive Summary

This blueprint defines the complete pipeline to train a custom EAGLE-3 draft model specifically aligned with `Qwen3.6-27B-Uncensored` on DGX Spark GB10. The off-the-shelf `specdrift-qwen3.6-27b-eagle3` drafter achieves only 5-8% token acceptance (50% slower than baseline). A custom-trained drafter targeting this exact model should achieve 60-80% acceptance, delivering the theoretical 1.5-2x speedup.

**Target speed**: 6-8 tps (vs current 3.1 tps baseline, 5.4 tps MTP-5)

---

## Architecture Overview

### EAGLE-3 Draft Model Design

Based on analysis of the `specdrift-qwen3.6-27b-eagle3` checkpoint and vLLM's `llama_eagle3.py` implementation:

```
EAGLE3-Qwen3-27B-Draft
├── Input: [embeddings; hidden_states] concatenated (2 × 5120 = 10240 for layer 0)
├── FC Layer: ReplicatedLinear(5120 × 3 → 5120) — combines 3 target hidden states
├── Norm: RMSNorm(5120)
├── 1× Transformer Block:
│   ├── SelfAttention: QKVParallelLinear(10240 → 6144, heads=48, kv_heads=8)
│   ├── MLP: SwiGLU(5120 → 16384 → 5120)
│   └── RMSNorm + residual connections
├── Output: LM Head → logits over reduced vocab (32000 draft vs 248320 target)
└── Vocab Mapping: d2t[32000] + t2d[248320] tensors for token translation
```

**Key design decisions**:
- **Single layer** (like specdrift) — sufficient for EAGLE-3, minimal memory overhead
- **Layer 0 input**: 2× hidden_size (concatenated embeddings + hidden_states) — matches EAGLE-3 paper
- **FC layer**: Combines 3 auxiliary hidden states from target model layers [3, 31, 59] (configurable)
- **Reduced vocab**: 32000 draft vocab vs 248320 target — critical for speed
- **Architecture class**: `LlamaForCausalLMEagle3` — vLLM natively supports this

### Target Model Hidden State Extraction Points

```python
# From Qwen3.6-27B-Uncensored (64 layers total)
aux_hidden_state_layer_ids = [3, 31, 59]  # early, mid, late layers

# Layer 3: captures low-level syntactic patterns
# Layer 31: captures semantic mid-level representations  
# Layer 59: captures high-level reasoning patterns
```

These are concatenated by the FC layer and fed into the draft model.

---

## Training Pipeline

### Phase 1: Data Generation (Offline)

**Tool**: `vllm-project/speculators` library  
**Duration**: ~6-12 hours for 100K samples  
**Output**: `.pt` files with hidden states + token IDs + loss masks

#### 1.1 Dataset Selection

**Primary**: ShareGPT/Vicuna-style conversations (reasoning + coding + general)
**Size**: 50K-100K conversations
**Format**: OpenAI chat format → apply Qwen3.6 chat template

**Recommended sources**:
- `Open-Orca/OpenOrca` (reasoning-heavy, good for thinking models)
- `teknium/OpenHermes-2.5` (diverse instruction following)
- `mlabonne/orpo-dpo-mix-40k` (preference-tuned, high quality)
- Custom: User's own conversation history with Hermes (highly aligned)

#### 1.2 Hidden State Generation

```bash
# Using speculators data generation
python -m speculators.data_generation_offline \
  --verifier-model /data/models/Qwen3.6-27B-Uncensored \
  --dataset-path /data/datasets/training_conversations.jsonl \
  --output-path /data/eagle3_training/hidden_states/ \
  --aux-layer-ids 3 31 59 \
  --max-seq-len 4096 \
  --tensor-parallel-size 1 \
  --batch-size 32
```

**What gets saved per sample**:
```python
{
  "input_ids": tensor[seq_len],           # tokenized conversation
  "hidden_states": [                      # list of 3 tensors
    tensor[seq_len, 5120],                # layer 3 hidden states
    tensor[seq_len, 5120],                # layer 31 hidden states
    tensor[seq_len, 5120],                # layer 59 hidden states
  ],
  "loss_mask": tensor[seq_len],           # 1=train, 0=ignore (prompt tokens)
  "verifier_logits": tensor[seq_len, 248320],  # target model output probs
}
```

#### 1.3 Vocabulary Mapping

```bash
# Build d2t (draft→target) and t2d (target→draft) tensors
python -m speculators.build_vocab_mapping \
  --token-freq /data/eagle3_training/hidden_states/token_freq.pt \
  --target-vocab-size 248320 \
  --draft-vocab-size 32000 \
  --output /data/eagle3_training/vocab_mapping/
```

**Result**: `d2t.pt` (32000 indices into target vocab) + `t2d.pt` (248320 indices into draft vocab, -1 for OOV)

---

### Phase 2: Draft Model Training

**Tool**: `speculators` training scripts with FlexAttention  
**Duration**: ~4-8 hours on GB10  
**Memory**: ~40GB GPU (fits in GB10 unified memory)

#### 2.1 Training Configuration

```yaml
# eagle3_qwen3_27b_config.yaml
model:
  verifier_model: /data/models/Qwen3.6-27B-Uncensored
  draft_vocab_size: 32000
  target_vocab_size: 248320
  hidden_size: 5120
  num_hidden_layers: 1          # Single layer draft
  num_attention_heads: 48
  num_key_value_heads: 8        # GQA
  intermediate_size: 16384       # SwiGLU MLP
  max_position_embeddings: 4096
  rms_norm_eps: 1.0e-6
  use_cache: false
  
  # EAGLE-3 specific
  aux_hidden_state_layer_ids: [3, 31, 59]
  fc_input_size: 15360           # 5120 * 3 (concatenated hidden states)
  use_aux_hidden_states: true
  norm_before_fc: true
  
  # Vocab mapping
  vocab_mapping_path: /data/eagle3_training/vocab_mapping/

training:
  batch_size: 8                   # Per device
  gradient_accumulation_steps: 4  # Effective batch = 32
  num_epochs: 3
  learning_rate: 5.0e-4           # Higher LR for small draft model
  lr_scheduler: cosine
  warmup_ratio: 0.1
  max_grad_norm: 1.0
  
  # FlexAttention for memory efficiency
  use_flex_attention: true
  torch_compile: true
  
  # Train-time testing (multi-step draft simulation)
  num_speculative_tokens: 5       # Match inference config
  train_time_testing: true
  
  # Loss masking
  loss_only_on_assistant: true    # Ignore prompt tokens
  
  # Checkpointing
  save_every_n_steps: 500
  output_dir: /data/eagle3_training/checkpoints/
  
data:
  train_data_path: /data/eagle3_training/hidden_states/
  max_seq_length: 4096
  num_workers: 4
```

#### 2.2 Training Script

```bash
#!/bin/bash
# train_eagle3_draft.sh

cd /data/SpecForge/speculators  # or wherever speculators is cloned

export CUDA_VISIBLE_DEVICES=0
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512

python scripts/train.py \
  --config /data/eagle3_training/eagle3_qwen3_27b_config.yaml \
  --data-path /data/eagle3_training/hidden_states/ \
  --output-dir /data/eagle3_training/checkpoints/ \
  --num-epochs 3 \
  --batch-size 8 \
  --gradient-accumulation 4 \
  --lr 5e-4 \
  --num-speculative-tokens 5 \
  --aux-layer-ids 3 31 59 \
  --draft-vocab-size 32000 \
  --use-flex-attention \
  --torch-compile
```

#### 2.3 Training Monitoring

```bash
# Watch training progress
tail -f /data/eagle3_training/checkpoints/training.log

# Key metrics to track:
# - loss: should decrease from ~2.5 to ~1.0 over 3 epochs
# - draft_acceptance_rate (during eval): target >60%
# - tokens_per_second (during eval): target >6 tps
```

---

### Phase 3: Model Export & vLLM Integration

#### 3.1 Export to HuggingFace Format

```bash
python -m speculators.export \
  --checkpoint /data/eagle3_training/checkpoints/best_model.pt \
  --output-dir /data/models/eagle3-qwen3.6-27b-custom/ \
  --config-template /data/eagle3_training/eagle3_qwen3_27b_config.yaml
```

**Output structure**:
```
/data/models/eagle3-qwen3.6-27b-custom/
├── config.json                    # LlamaForCausalLMEagle3 architecture
├── model.safetensors              # Draft model weights
├── d2t.safetensors               # Draft→target vocab mapping (32000)
├── t2d.safetensors               # Target→draft vocab mapping (248320)
├── vocab_mapping/                 # Optional: JSON vocab maps
└── speculator_config.json        # vLLM auto-loading config
```

#### 3.2 config.json Specification

```json
{
  "architectures": ["LlamaForCausalLMEagle3"],
  "hidden_size": 5120,
  "num_hidden_layers": 1,
  "num_attention_heads": 48,
  "num_key_value_heads": 8,
  "intermediate_size": 16384,
  "vocab_size": 32000,
  "draft_vocab_size": 32000,
  "target_vocab_size": 248320,
  "hidden_act": "silu",
  "rms_norm_eps": 1.0e-6,
  "use_cache": false,
  "max_position_embeddings": 4096,
  "rope_theta": 1000000.0,
  "rope_scaling": null,
  "eagle_config": {
    "aux_hidden_state_layer_ids": [3, 31, 59],
    "fc_input_size": 15360,
    "use_aux_hidden_states": true,
    "norm_before_fc": true
  },
  "speculator_config": {
    "method": "eagle3",
    "num_speculative_tokens": 5,
    "verifier_model": "/data/models/Qwen3.6-27B-Uncensored"
  }
}
```

#### 3.3 vLLM Serve Command

```bash
vllm serve /data/models/Qwen3.6-27B-Uncensored \
  --max-model-len 65536 \
  --tensor-parallel-size 1 \
  --gpu-memory-utilization 0.85 \
  --enable-auto-tool-choice \
  --tool-call-parser qwen3_xml \
  --enable-chunked-prefill \
  --enable-prefix-caching \
  --kv-cache-dtype auto \
  --dtype bfloat16 \
  --max-num-batched-tokens 65536 \
  --max-num-seqs 64 \
  --host 0.0.0.0 --port 8000 \
  --speculative-config '{
    "method": "eagle3",
    "model": "/data/models/eagle3-qwen3.6-27b-custom",
    "num_speculative_tokens": 5,
    "parallel_drafting": false
  }'
```

---

## Implementation Checklist

### Prerequisites
- [ ] Install `speculators` library on DGX
- [ ] Verify Qwen3.6-27B-Uncensored model loads correctly in vLLM
- [ ] Prepare training dataset (50K+ conversations)
- [ ] Ensure `/data/eagle3_training/` has 500GB+ free space

### Phase 1: Data Generation
- [ ] Run hidden state generation (6-12 hours)
- [ ] Verify `.pt` files contain correct tensors
- [ ] Build vocabulary mapping (d2t + t2d)
- [ ] Validate loss masks correctly mask prompt tokens

### Phase 2: Training
- [ ] Configure training YAML
- [ ] Run training (4-8 hours)
- [ ] Monitor loss curve (target: ~1.0 final loss)
- [ ] Run evaluation to check draft acceptance rate (target: >60%)
- [ ] Save best checkpoint

### Phase 3: Deployment
- [ ] Export to HuggingFace format
- [ ] Verify config.json matches vLLM expectations
- [ ] Test vLLM serve with custom drafter
- [ ] Benchmark speed (target: 6-8 tps)
- [ ] Compare acceptance rate vs specdrift baseline

---

## Expected Results

### Comparison Table

| Metric | Baseline | MTP-5 | Specdrift EAGLE-3 | **Custom EAGLE-3 (Target)** |
|--------|----------|-------|-------------------|----------------------------|
| Speed | 3.1 tps | 5.4 tps | 1.5 tps | **6-8 tps** |
| Acceptance | N/A | ~14% | ~5-8% | **60-80%** |
| Startup | 300s | 300s | 300s | 300s |
| Memory | 52GB | 52GB | 52GB | ~55GB |
| Quality | 100% | 100% | 100% | 100% |

### Acceptance Rate Breakdown (Target)

| Position | Specdrift | Custom (Target) |
|----------|-----------|----------------|
| Position 0 | 30-60% | 85-95% |
| Position 1 | 0-5% | 70-80% |
| Position 2 | 0% | 55-65% |
| Position 3 | 0% | 40-50% |
| Position 4 | 0% | 25-35% |
| **Mean** | **1.2-1.6** | **3.5-4.5** |

---

## Troubleshooting Guide

### Issue: Hidden state generation OOM
**Fix**: Reduce `--batch-size` to 16 or 8. GB10 unified memory can swap but it's slow.

### Issue: Training loss not decreasing
**Fix**: Check that loss masks are correct (prompt tokens should be 0). Verify hidden states are from the correct layers.

### Issue: vLLM fails to load custom drafter
**Fix**: Ensure config.json uses `"architectures": ["LlamaForCausalLMEagle3"]`. Check that `fcs.X.weight` tensors are NOT present (use single FC layer).

### Issue: Low acceptance rate after training
**Fix**: 
1. Train for more epochs (try 5 instead of 3)
2. Increase dataset diversity (add coding, math, reasoning)
3. Adjust aux_layer_ids (try [7, 27, 55] instead of [3, 31, 59])
4. Increase draft vocab size (try 64000 instead of 32000)

### Issue: Drafter slower than expected
**Fix**: Enable `parallel_drafting: true` in vLLM config (requires vLLM 0.21.0+ with P-EAGLE support).

---

## Resource Requirements

| Resource | Amount | Notes |
|----------|--------|-------|
| GPU Memory | ~55GB | Target + draft + training overhead |
| Disk (training) | ~500GB | Hidden states + checkpoints |
| Disk (final model) | ~2GB | Single-layer draft model |
| Time (data gen) | 6-12h | Depends on dataset size |
| Time (training) | 4-8h | 3 epochs on GB10 |
| Time (export) | ~10min | Conversion to HF format |

---

## Next Steps

1. **Install speculators**: `pip install speculators` on DGX venv
2. **Prepare dataset**: Download 50K+ conversations, apply Qwen3.6 chat template
3. **Generate hidden states**: Run Phase 1 overnight
4. **Train draft model**: Run Phase 2 while monitoring
5. **Export & test**: Phase 3, then benchmark vs MTP-5

**Success criterion**: Custom EAGLE-3 achieves >60% acceptance and >6 tps sustained throughput.

---

## References

- [vLLM Speculators Library](https://github.com/vllm-project/speculators)
- [EAGLE-3 Paper](https://arxiv.org/abs/2503.01840) (Zhang et al., 2025)
- [P-EAGLE Paper](https://arxiv.org/abs/2602.01469) (AWS, 2026)
- [vLLM Speculative Decoding Docs](https://docs.vllm.ai/en/latest/features/speculative_decoding/)
- [Speculators v0.3.0 Blog Post](https://blog.vllm.ai/2025/12/13/speculators-v030.html)
