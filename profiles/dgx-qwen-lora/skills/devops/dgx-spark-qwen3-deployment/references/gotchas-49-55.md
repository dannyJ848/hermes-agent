# DGX Spark Gotchas 49-55 (Training & UMA, Apr 18 2026)

49. **UMA double-allocation OOM on DGX Spark.** BF16 model (67GB) OOMs at 66%
    because mmap'd safetensor shards + materialized CUDA tensors compete for the
    SAME ~119GB physical memory pool (Unified Memory Architecture). Fix: import
    uma_eager_load.py BEFORE any model loading — EagerSafeOpen monkey-patch loads
    tensors directly, closes file handles, and evicts page cache via
    posix_fadvise(DONTNEED). Drops peak from ~134GB to ~72GB. Ref:
    github.com/kreuzhofer/dgx-spark-unsloth-qwen3.5-training and NVIDIA forum #363268.

50. **LoRA→vLLM adapter format mismatch for MoE.** Unsloth's LoRA produces fused
    expert tensors incompatible with vLLM's expected format. AVOID serving LoRA
    adapters directly in vLLM for MoE models. FIX: Always merge LoRA into a new
    base model via save_pretrained_merged(merged_16bit), then serve the merged
    model. This is already how spark-lora-train.sh works — no separate adapter.

51. **liger-kernel saves GPU memory during training.** Official Qwen3 best practice.
    pip install liger-kernel. Added to spark-lora-train.sh.

52. **packing=True for SFTTrainer on mixed-length data.** Packs short sequences
    together instead of padding — 3x throughput boost when mixing reasoning+generic
    data. Added to spark-lora-train.sh SFTTrainer call.

53. **ThinkingAwareCollator masks loss on empty thinking tags.** When mixing CoT
    reasoning data (full thinking) with generic data (empty thinking tags),
    generic examples get wrapped in empty thinking tags. Collator detects empty
    thinking blocks and sets labels to -100 (ignored in loss). Equivalent to
    ms-swift's loss_scale ignore_empty_think. WITHOUT this, generic training
    data DEGRADES reasoning capability — the model learns to output empty thinking.

54. **preserve_thinking + enable_thinking in vLLM chat-template-kwargs.** Qwen3.6
    flag that carries reasoning traces across conversation turns. Essential for
    agent use. Add to BOTH vLLM serve calls (BF16 port 8000, FP8 port 8001):
    --chat-template-kwargs '{"preserve_thinking": true, "enable_thinking": true}'.

55. **Add 'gate' to LoRA target_modules for MoE router.** The MoE router gate
    (separate from gate_proj in the FFN) controls expert routing. Critical to
    train after abliteration — the refusal direction removal changes routing.
    Without it, LoRA only targets attention+FFN but not the router itself.
    Full targets: q_proj, k_proj, v_proj, o_proj, gate_proj, gate, up_proj, down_proj.
