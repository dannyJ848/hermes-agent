# Qwen3.6-27B DGX Spark Performance Optimization Checkpoint
# Date: April 23, 2026
# Session: Apr 23 afternoon - MTP/EAGLE-3 hacking + BF16 optimization

## CRITICAL FINDINGS

### 1. MTP Speculative Decoding = DEADLOCK/LOCKUP
- MTP (Multi-Token Prediction) loads successfully on Qwen3.6-27B
- `--enforce-eager` + MTP = API deadlock (requests hang forever)
- torch.compile + MTP = SYSTEM LOCKUP (SSH dies, needs power cycle)
- **MTP IS NOT VIABLE on GB10 with current vLLM 0.19.1rc1**

### 2. EAGLE-3 = ARCHITECTURE BLOCKED
- vLLM supports EAGLE-3 natively for Qwen3.5 (`SupportsEagle3` interface)
- BaldEagle draft model uses `Qwen3_5ForCausalLMEagle` architecture
- vLLM accepts ONLY specific draft architectures: `Eagle3LlamaForCausalLM`, `Eagle3Qwen3vlForCausalLM`, etc.
- `Qwen3_5ForCausalLM` (standard) is NOT in supported EAGLE-3 draft list
- **EAGLE-3 IS BLOCKED without custom model class registration**

### 3. Baseline BF16 Speed (thinking enabled): 1.49 tok/s
- Default Qwen3.6 outputs thinking/reasoning tokens before answer
- 128 completion tokens = ~86 seconds
- **SLOW due to thinking overhead**

### 4. BF16 + Thinking DISABLED: 4.57 tok/s
- `chat_template_kwargs: {'enable_thinking': False}`
- Same 128 tokens = ~28 seconds
- **3.1x SPEEDUP from disabling thinking**

### 5. Container Crash Pattern
- Server crashes after 1-2 requests with "Connection reset by peer"
- May be TurboQuant image issue or memory pressure
- Container auto-restarts but takes 3-4 minutes to reload

## RESEARCH DISCOVERIES

### DeepSeek TileKernels (released Apr 23, 2026)
- GPU kernel library using TileLang DSL
- Could enable custom Blackwell SM121 kernels
- Potential for 2-3x attention layer speedup
- Repo: https://github.com/deepseek-ai/TileKernels

### LongSpec / OWL LSTM Speculative Decoding
- LSTM-based drafter (context-length-agnostic)
- Constant KV cache size
- CPU-offload drafting possible on Grace CPU
- Repo: https://github.com/sail-sg/LongSpec

### NVIDIA Forum: Qwen3.5-27B DFlash Results
- DFlash speculative decoding: 30-65 tok/s on GB10
- Config: `--speculative-config '{"method": "dflash", "model": "z-lab/Qwen3.5-27B-DFlash", "num_speculative_tokens": 15}'`
- z-lab has DFlash models for Qwen3.5, need to check Qwen3.6

### vLLM Recipes Page Findings
- `--language-model-only`: Skip vision encoder for text-only speedup
- `--performance-mode throughput`: High-concurrency optimization
- `--max-num-batched-tokens`: 4096 for chat, 32768 for throughput
- `--default-chat-template-kwarg '{"enable_thinking": false}'`: Server-side thinking disable

## CURRENT SERVER STATE
- Container: qwen36-bf16 (running, auto-restart enabled)
- Model: Qwen3.6-27B-Uncensored on port 8000
- Image: ghcr.io/aeon-7/vllm-dflash:turboquant
- Flags: --enforce-eager, --kv-cache-dtype fp8_e5m2, --enable-prefix-caching, --enable-chunked-prefill
- Status: Likely still loading (check logs before testing)

## NEXT STEPS (Priority Order)
1. **Fix container crash** - Try `--gpu-memory-utilization 0.90` or switch to `:latest` image
2. **Disable thinking server-side** - Add `--default-chat-template-kwarg '{"enable_thinking": false}'`
3. **Test DFlash** - Check if z-lab has Qwen3.6-27B-DFlash model
4. **Test --language-model-only** - Skip vision encoder loading
5. **Research TileKernels** - Deep dive into custom kernel building for GB10
6. **Research LongSpec** - LSTM-based speculative decoding for 262K context

## HACKING TARGETS
1. Custom EAGLE-3 model class for Qwen3.6 (vLLM source patch)
2. TileLang kernel for GDN attention optimization on SM121
3. LongSpec integration (LSTM drafter training)
4. DFlash model adaptation from Qwen3.5 -> 3.6

Resume: Check container status, verify model serving, then pick optimization path.
