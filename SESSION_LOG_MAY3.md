# Qwen 27B Training Session Log - May 3, 2026

## Current Status
- Training KILLED at step 50/1000 due to flat losses (no learning)
- GPU clean, ready for new pipeline

## Datasets Available
- SlimOrca-200k: /data/datasets/slimorca/
- OpenHermes-200k: /data/datasets/openhermes/
- CodeContests/APPS/ShareGPT/UltraChat: Too big to download
- Franken V8: Can generate synthetic reasoning traces

## Goal
Qwen 27B as expert logician — Claude-level reasoning, coding, tool calling, iterative ability.
Franken V8 chosen for reasoning enhancement focus.

## Next Steps
1. Build maximum quality pipeline with AdamW, warmup, cosine decay
2. Use ALL available data (SlimOrca + OpenHermes + Franken V8 synthetic)
3. 10k+ steps with proper curriculum learning
4. Evaluate on MMLU/GSM8K benchmarks

## Files in this branch
- franken_v8_bridge_v3.py: Complete bridge loading 11.5B Franken V8 params
- train_ultimate_v3.py: Full pipeline
- train_ultimate_v3_trainonly.py: Training-only with normalized teacher matching
- precompute_teacher_v2.py: Teacher hidden state precomputation
- evaluate_checkpoints.py: Checkpoint evaluation
- fix_teacher_distill.py: Fixed teacher distillation
- test_gradient_stability_v2.py / v3.py: Gradient stability tests
