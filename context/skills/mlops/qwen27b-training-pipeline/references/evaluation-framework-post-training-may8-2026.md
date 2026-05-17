# Evaluation Framework — Post-Training (May 8, 2026)

## Context
After training completes, evaluate the merged BF16 model before deployment.

## Files Created

| File | Purpose |
|------|---------|
| `evaluate_model.py` | Full evaluation suite — lm-eval + custom reasoning + adversarial |
| `merge_model.sh` | Merge LoRA adapter into base model → single 54GB file |
| `post_training_pipeline.sh` | One-command: merge → evaluate → package results |
| `deploy_hermes_qwen.sh` | Hermes Agent integration — vLLM server + config |

## Evaluation Suite

### Standard Benchmarks (lm-eval-harness)
- MMLU, GSM8K, HumanEval, BBH, ARC, Winogrande

### Custom Reasoning Tests
- Wason selection task (deductive reasoning)
- Syllogism validation (classical logic)
- Counterfactual reasoning
- Mathematical proof verification

### Adversarial Robustness
- Ambiguous premises
- Contradictory evidence
- Edge cases (0.999... = 1, empty set paradox)

## Deployment

### vLLM Server (BF16, no quantization)
```bash
vllm serve $MERGED_MODEL \
    --port 8000 \
    --dtype bfloat16 \
    --tensor-parallel-size 1 \
    --max-model-len 32768 \
    --gpu-memory-utilization 0.95
```

### Hermes Agent Routing
- Local Qwen for: reasoning, logic, math, proofs, code
- Z.AI fallback for: general queries

## Key Decision: BF16 vs Quantized

**Keep BF16 for continuous learning.** GGUF is read-only — hard to fine-tune further. BF16 allows:
- Continued LoRA training on new data
- Merging new adapters as Hermes learns
- No quantization error accumulation
- Full precision = best reasoning quality

**Master copy**: BF16 merged model (~54GB)
**Optional**: GGUF backup for portability (~15GB) but keep BF16 as working copy
