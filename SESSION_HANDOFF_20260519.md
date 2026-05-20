# Context Handoff — 2026-05-19 Session

## MacBook State
- Hermes: v0.14.0 at ~/hermes-agent, origin/main at 6e2772eb9
- Default model: kimi-for-coding (Kimi cloud API)
- Config: ~/.hermes/config.yaml — kimi-for-coding default, spark-bf16 provider for DGX
- Python: 3.10 (brew), CLI at ~/Library/Python/3.10/bin/hermes

## DGX State (spark-85e8.local, 10.0.0.171)
- Hermes: v0.14.0 at /data/SpecForge/hermes-agent (synced with MacBook)
- vLLM: RUNNING on port 8000
- Model: /data/models/Qwen3.6-27B-Uncensored (base, BF16, no LoRA)
- DFlash speculative decoding: active (Qwen3.5-27B-DFlash draft)
- Tool parser: qwen3_xml
- Max model len: 131072
- GPU: NVIDIA GB10, CUDA sm_121

## Key Decisions
- LoRA training ABANDONED — 17% GSM8K regression, 3x slower, no MMLU gain
- Using base Qwen3.6-27B-Uncensored for max performance
- Final-Merged model kept at /data/models/Qwen3.6-27B-Uncensored-Final-Merged (not served)

## To Resume DGX Work
```bash
hermes chat --provider spark-bf16 --model /data/models/Qwen3.6-27B-Uncensored
```

## Benchmarks on File
- LoRA MMLU: 86.57% | Base MMLU-Pro: 86.2%
- LoRA GSM8K: 66.19% | Base expected: ~84%
- LoRA HumanEval: 82.93%
- Full results: /data/SpecForge/custom_dflash/evaluation_results/
