# Gotchas 67-70: Qwen3.6 GDN Hybrid Architecture Discovery (Apr 18 2026)

## 67. Qwen3.6 is GDN HYBRID, NOT Pure Transformer MoE

**DISCOVERY:** Qwen3.6-35B-A3B uses Gated DeltaNet (GDN) hybrid architecture.
40 total layers: only 10 use standard Transformer attention, 30 use GDN
(linear attention variant with fixed-size state, no growing KV cache).

**Impact:** Per-token KV footprint is ~30x smaller than comparable pure-attention
model. Only 10/40 layers need KV cache. 262K native context possible because
GDN layers maintain fixed-size recurrent state instead of linearly-growing cache.

**Source:** Allen Kuo benchmark article (medium.com @kwyshell, Apr 2026) +
HuggingFace model card + vLLM issue #37554.

**CRITICAL implications:**
- TurboQuant KV cache BLOCKED (see gotcha #68)
- --max-num-seqs must be <= 512 (see gotcha #69)
- NEVER use --calculate-kv-scales (see gotcha #70)
- fp8_e5m2 KV is the CORRECT choice (compatible with hybrid models)

## 68. TurboQuant KV Cache BLOCKED for Qwen3.6 GDN Hybrid

**BUG:** TurboQuant KV cache presets (turboquant_k8v4, turboquant_4bit_nc,
turboquant_3bit_nc) do NOT work with hybrid GDN+Attention models like Qwen3.6.
Boundary layer protection requires uniform attention layers across the model.

**vLLM docs explicitly state:** "Hybrid Mamba-Transformer models NOT supported"
Qwen3.6 uses same architecture as Qwen3.5.

**FOUND & FIXED:** superqwen3-super.sh restart_serving() used
--kv-cache-dtype turboquant_k8v4 for the FP8 server. Changed to fp8_e5m2.
Also fixed: dual-training-orchestrator.sh (legacy) had same wrong setting.

**CORRECT:** --kv-cache-dtype fp8_e5m2 or fp8
**WRONG (silent corruption):** turboquant_k8v4, turboquant_4bit_nc, turboquant_3bit_nc

**NOTE:** v020-tq Docker image includes TQ support but we just don't USE TQ
KV presets. The image itself is fine -- set --kv-cache-dtype fp8_e5m2.

## 69. --max-num-seqs 512 Required for GDN Hybrid Models

**BUG:** vLLM defaults to --max-num-seqs 1024. On Qwen3.6 GDN hybrid,
this overflows the GDN Mamba cache blocks (only 981 available at 60% util).

**FIX:** Add --max-num-seqs 512 to ALL vLLM serve commands:
- spark-maxperf.sh (2 serve commands)
- superqwen3-super.sh restart_serving() (2 commands)
- spark-grpo-train.sh GRPO server (1 command)

**Source:** Allen Kuo -- "default max_num_seqs=1024 exceeds available Mamba
cache blocks for GDN layers. Fix: --max-num-seqs 512"

## 70. NEVER Use --calculate-kv-scales with GDN Hybrid Models

**BUG:** --calculate-kv-scales causes CATASTROPHIC output corruption on
Qwen3.5/3.6 GDN hybrid models with FP8 KV cache.

**Root cause:** calc_kv_scales() computes per-layer FP8 scales from a dummy
forward pass. GDN layers have UNINITIALIZED recurrent state during this pass.
Their garbage outputs poison downstream attention layer scales.

**Symptoms:** Hallucinated inputs, topic fixation loops, gibberish. SILENT.
**vLLM issue:** #37554
**FIX:** Don't use --calculate-kv-scales. Default scales (1.0) work correctly.
**Our scripts:** Confirmed NONE use this flag.
