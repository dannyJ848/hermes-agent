# Hermes Agent Checkpoint — Apr 23 2026 14:30 UTC
# Label: apr23-adaptive-thinking-live
# Status: ADAPTIVE THINKING DEPLOYED, EAGLE-3 TRAINING IN PROGRESS

## DGX Spark — Current State
- vLLM: RUNNING on port 8000, qwen3.6-27b-uncensored, BF16 eager mode
- Baseline speed: 4.02 tok/s (thinking disabled), 2.58 tok/s (thinking enabled)
- GPU util: 0% (idle, waiting for requests)
- Training: Eagle3 draft model training in background (42+ min, CPU-bound)

## Adaptive Thinking System — DEPLOYED
- Files: ~/.hermes/tools/adaptive_thinking.py, adaptive_thinking_middleware.py, spark_adaptive_client.py
- Function: Automatically enables thinking only for complex multi-step problems
- Test results: 8/8 correct classifications
- Speed: Consistent ~4.0 tok/s across all prompt types
- Integration: Client-side wrapper injects chat_template_kwargs

## Enhancement Database — 17 enhancements
- Applied: 9 (including adaptive thinking)
- Pending: 8 (including Eagle-3 speculative decoding)

## Research Findings
- TileKernels (DeepSeek): GPU kernel optimization via TileLang DSL
- LongSpec: LSTM-based speculative decoding with constant KV cache
- vLLM Blackwell SM121 support: Issue #31128 closed, PR #37700 merged

## Next Steps
1. Wait for Eagle-3 training completion (~1-2h remaining)
2. Integrate Eagle-3 draft model with vLLM for 2x speedup
3. Research TileKernels for custom GB10 kernel optimization
4. Test LongSpec integration for context-length-agnostic drafting

## Critical Files
- ~/.hermes/tools/adaptive_thinking.py — Core logic
- ~/.hermes/tools/spark_adaptive_client.py — Hermes integration
- ~/.hermes/research/qwen36_enhancements.json — Enhancement tracking
- /data/train_eagle3_draft.py — Training script on Spark
