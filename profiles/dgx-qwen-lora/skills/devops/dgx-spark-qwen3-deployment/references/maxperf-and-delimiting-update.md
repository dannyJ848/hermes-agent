# DGX Spark Skill Update — Apr 18 2026

## Update 1: TurboQuant KV Cache Incompatibility

TurboQuant KV cache (turboquant_k8v4) is NOT compatible with Qwen3.6 when using:
- MTP speculative decoding (qwen3_next_mtp)
- Hybrid Mamba models (Qwen3.5/3.6 use hybrid attention+Mamba)

vLLM issue #40127: `NotImplementedError: TurboQuant KV cache is not supported for hybrid (attention + Mamba) models`

**FIX:** Use `--kv-cache-dtype fp8_e5m2` instead. Still gives 2x KV capacity vs BF16.
TurboQuant works ONLY without MTP and without hybrid Mamba — not our config.

## Update 2: init_on_alloc=0 (CRITICAL for Grace Blackwell)

Ubuntu generic kernel sets `init_on_alloc=1` by default. On Grace Blackwell's
unified memory, this means the kernel zero-fills every new page INCLUDING GPU
memory allocations. This kills cudaMalloc performance (5-15% impact).

NVIDIA Grace Performance Tuning Guide explicitly recommends `init_on_alloc=0`
for coherent systems where GPU memory is exposed as system memory.

```bash
echo 'GRUB_CMDLINE_LINUX="$GRUB_CMDLINE_LINUX init_on_alloc=0"' | sudo tee /etc/default/grub.d/init-on-alloc.conf
sudo update-grub
sudo reboot
```

Also add `iommu.passthrough=1` for DMA bypass while editing kernel params.

## Update 3: 7-Layer MAXPERF (spark-maxperf.sh)

| Layer | What | Gain |
|-------|------|------|
| P1 Hardware | nvidia-smi -pm 1, power limit MAX, ECC OFF, clock lock | 2-3% bandwidth |
| P2 OS Kernel | perf governor, THP=always, init_on_alloc=0, IOMMU passthrough, swappiness=1, ulimit 65536 | 5-15% cudaMalloc |
| P3 GPU Runtime | FlashInfer, expandable_segments, MARLIN_USE_ATOMIC_ADD=1 | 5-10% overall |
| P4 vLLM Serve | fp8_e5m2 KV, MTP x2, prefix cache, chunked prefill, -O2, 95% GPU util, fastsafetensors | 30% throughput |
| P5 Training | BF16 native only, FlashAttn2, torch.compile, NCCL tuned | 15-20% training |
| P6 Delimiting | 5-layer uncensored (see below) | Full control |
| P7 Serving | :8000 BF16 + :8001 FP8 | Both modes |

## Update 4: 5-Layer Delimiting (beyond weight abliteration)

L1 (abliteration) alone is NOT enough. Four more layers enforce restrictions:

L1: Refusal direction abliteration (norm-preserving biprojected) — Phase 4.0
L2: Chat template override — strip safety persona framing from Jinja2 template
L3: System prompt purge — delete default_system_message, safety_config from tokenizer_config.json
L4: Generation config unrestrict — remove top_k=20, set top_p=1.0, no penalties
L5: Thinking mode control — preserve /think /no_think, USER controls per request

Key insight: safety alignment relies "almost entirely on the chat template."
Stripping template drops refusals 80%->40%. L1 kills remaining 40%.
Together = 0/465 refusals — same as HauhauCS but with true BF16.

Script: ~/dgx-spark-prep/abliterate-qwen3.sh (709 lines)

## Update 5: Benchmarked vLLM Serve Command (58-66 tok/s)

Source: Turrican, NVIDIA DGX Spark forum (Apr 2026)

```bash
vllm serve /data/models/Qwen3.6-35B-A3B-Uncensored \
  --host 0.0.0.0 --port 8000 \
  --served-model-name Qwen3.6-Uncensored \
  --max-model-len 262144 \
  --gpu-memory-utilization 0.95 \
  --max-num-batched-tokens 32768 \
  --enable-auto-tool-choice --tool-call-parser qwen3_coder \
  --reasoning-parser qwen3 \
  --kv-cache-dtype fp8_e5m2 \
  --load-format fastsafetensors \
  --attention-backend flashinfer \
  --enable-prefix-caching --enable-chunked-prefill \
  --speculative-config '{"method":"qwen3_next_mtp","num_speculative_tokens":2}' \
  -O2

# Required env:
export VLLM_MARLIN_USE_ATOMIC_ADD=1
export PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True,max_split_size_mb:128"
```

## Update 6: Provider Switch — Lilac Replacing FriendliAI

FriendliAI cache discount useless at 95%+ cache miss rate for dynamic research.
Lilac: $0.90/M input, $3.00/M output (36% cheaper), 130 t/s (25% faster).
FriendliAI: $1.40/M input, $4.40/M output, 104 t/s.
Burn remaining $10 on FriendliAI first, then switch to Lilac.

## Update 7: Updated Launch Day Sequence

1. macbook-transfer-helper.sh --enable-ssh
2. spark-day1.sh --macbook <IP> --usb
3. spark-maxperf.sh (7-layer optimize + delimit + serve)
4. wire-spark-to-hermes.sh <SPARK_IP>
5. spark-quality chat
6. source /data/training-env.sh && dual-training-orchestrator.sh

## Update 8: vLLM v0.19.1 + Transformers v5.5.4 (Apr 18 2026)

Major version jump from Transformers v4 to v5.5.4. Key benefits for Qwen3.6 MoE:

- 6.6x MoE weight loading speedup (66s -> 10s on A100 for 110B MoE)
  via parallel expert loading
- New ExpertBackend: pluggable execution architecture (eager/fused/vLLM)
- Quantized MoE support (infrastructure benefits FP8 serving)
- WeightConverter: merge/split experts at load time
- AttentionInterface: centralized abstraction for attention methods

ENV VARS (add to Docker run + spark-maxperf.sh):
  HF_ENABLE_PARALLEL_LOADING=1   # 6.6x MoE load speedup
  HF_DEACTIVATE_ASYNC_LOAD=0    # keep v5 async ON
  HF_HUB_ENABLE_HF_TRANSFER=1  # fast model downloads

Docker image: vllm/vllm-openai:v0.19.1
Tag as: vllm-spark:v0191
Fallback chain: tq -> base -> v0191 -> custom -> community -> stock

No breaking changes to existing vLLM serve flags.

## Update 9: EXO Disaggregated Prefill/Decode Architecture

EXO 1.0 (exo-explore/exo, 43.8k stars) supports heterogeneous clustering:
- Spark = prefill (100 TFLOPs compute, compute-bound phase)
- Mac Studio = decode (819 GB/s bandwidth, memory-bound phase)
- Layer-by-layer KV streaming overlaps compute + transfer
- Full overlap when t_send < t_compute (GQA models at 5K+ context)
- Automatic device discovery, hardware profiling, phase placement

Benchmark (Llama-3.1 8B, 8K prompt):
  Spark alone:    1.47s prefill + 2.87s decode = 4.34s (1.9x)
  Mac Studio:     5.57s prefill + 0.85s decode = 6.42s (1.0x baseline)
  COMBINED:       1.47s prefill + 0.85s decode = 2.32s (2.8x!)

Danny's hardware: M2 Air 24GB — too small for meaningful decode benefit.
Best at 24GB: only small models for decode, marginal bandwidth advantage.

UPGRADE PATH: Mac Studio M4 Ultra 512GB (819 GB/s) + Spark = 3-4x total
  - Can run Qwen3.6-35B for decode (3B active, ~6GB in 8-bit)
  - 819 GB/s vs Spark's 273 GB/s = 3x decode bandwidth
  - EXO auto-discovers, profiles, and optimizes placement
  - RDMA over Thunderbolt 5 for 99% latency reduction
  - GB10 Blackwell support in EXO PR #1842

NOT integrated into spark-day1.sh yet — requires Mac Studio hardware.
