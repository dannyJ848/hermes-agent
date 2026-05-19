# Post-Training Evaluation Patterns on DGX Spark (GB10)

Session: May 10-11, 2026 — Qwen 27B Expert Logician evaluation

## Key Finding: lm-eval-harness on GB10 (CORRECTED)

### Previous Misconception
Earlier sessions concluded lm-eval-harness was "not suitable for GB10" due to slow speed (~1.1s/request) and SSH timeouts. This was wrong — the issue was SSH timeout, not hardware limitation.

### Corrected Understanding
- Full MMLU (56,168 loglikelihood requests) completes in ~4h 43m on GB10
- Initial speed: ~1.1-1.3s per request (slow during warmup)
- Speed improves dramatically: reaches 7.3 it/s (~0.14s/request) by end
- **MMLU score: 86.57%** — excellent performance
- SSH sessions timeout before completion if run in foreground

### CRITICAL NEW FINDING: Silent Death on generate_until Tasks (May 11, 2026)

**Loglikelihood tasks (MMLU, ARC, WinoGrande) complete reliably.**
**generate_until tasks (GSM8K, HumanEval, BBH) can SILENTLY DIE.**

Observed on Qwen 27B BF16 (51GB) GSM8K:
- Process reached 75% (984/1319) after ~10.5 hours
- Process vanished without error message, crash dump, or exception
- No partial results saved (no `evaluation_results/gsm8k/` directory created)
- GPU went idle (0% utilization, 37°C)
- Last log entry showed normal progress at 44s/it
- Likely cause: OOM or driver timeout on long-running generate_until tasks

**Implications:**
- lm-eval-harness is SAFE for loglikelihood tasks on GB10
- lm-eval-harness is UNRELIABLE for generate_until tasks on GB10
- No resume capability — must restart from scratch
- No partial results — hours of compute lost

**Mitigation strategies:**
1. **Run benchmarks individually** (not chained in one script) — easier restart, less lost work
2. **Use direct Python evaluation for generate_until tasks** — more reliable, faster per-example
3. **Use vLLM serving + API-based evaluation** — avoids transformers pipeline issues entirely
4. **Monitor GPU temperature and utilization** — sudden drop to 0% is death signal

### Solution Pattern
Use `terminal(background=true)` with a sequential benchmark script. The tool backgrounds the SSH session itself, not processes inside it:

```bash
# CORRECT — backgrounds the entire SSH session
terminal(background=true, command="ssh djg6228@10.0.0.171 'bash -c \"cd /data/SpecForge/custom_dflash && source eval_venv/bin/activate && lm_eval --model hf --model_args pretrained=/data/SpecForge/custom_dflash/checkpoints/final_model_merged,dtype=bfloat16 --tasks mmlu --num_fewshot 5 --batch_size 1 --output_path evaluation_results/mmlu_full --device cuda 2>&1 | tee evaluation_results/benchmark_suite.log && echo MMLU_DONE && lm_eval --tasks gsm8k ... && echo GSM8K_DONE && ...\"'")
```

### Critical Pitfalls

1. **DO NOT use `&`, `nohup`, `disown`, or `setsid` in foreground SSH** — Hermes terminal tool blocks shell-level background wrappers. Use `terminal(background=true)` instead; it backgrounds the SSH session itself.
2. **DO NOT chain multiple backgrounding attempts** — repeated failures with `&` or `nohup` waste turns. Write a script to the remote host, then launch it with `terminal(background=true)` using `nohup bash /path/to/script.sh > /dev/null 2>&1 < /dev/null & echo $!`
3. **DO NOT use `limit` parameter to speed up** — user explicitly wants FULL benchmarks
4. **DO use `terminal(background=true)`** — Hermes tracks the process, survives SSH disconnect
5. **DO check progress via `ps` and log tail** — not via waiting on the background process handle
6. **DO use `execute_code` with SSH for clean status checks** — avoids log truncation issues:
   ```python
   import subprocess
   result = subprocess.run(
       ['ssh', 'djg6228@10.0.0.171',
        'ps -o pid,pcpu,pmem,etime,comm -p <PID> | tail -1 && '
        'nvidia-smi --query-gpu=utilization.gpu,temperature.gpu --format=csv,noheader,nounits && '
        'grep -o "Running loglikelihood requests: *[0-9]*%" /path/to/benchmark_suite.log | tail -1'],
       capture_output=True, text=True, timeout=15
   )
   print(result.stdout)
   ```

### Concurrent Process Hazard (May 11, 2026)

When restarting after silent death, ALWAYS verify no old processes are still running:

```bash
# Check BEFORE starting new benchmark
ps aux | grep -E 'lm_eval|python3.*benchmark' | grep -v grep

# If old process found, kill it
kill -9 <OLD_PID>

# Wait for clean state
sleep 5
ps aux | grep -E 'lm_eval|python3.*benchmark' | grep -v grep || echo "Clean"
```

**Failure mode:** Old lm_eval process was zombie/defunct but still held GPU context.
New process started, both tried to load model simultaneously. System load spiked to 44+.
GPU context conflicts, extreme slowdown, potential hangs.

**Rule:** One benchmark at a time on GB10. No concurrent model loads.

When a generate_until benchmark dies silently (no error, no partial results):

```bash
# Step 1: Write a restart script on the remote host
# (avoids shell quoting hell in SSH command)
cat > /data/SpecForge/custom_dflash/restart_benchmarks.sh << 'EOF'
#!/bin/bash
cd /data/SpecForge/custom_dflash
source eval_venv/bin/activate
lm_eval --model hf --model_args pretrained=/data/SpecForge/custom_dflash/checkpoints/final_model_merged,dtype=bfloat16 --tasks gsm8k --num_fewshot 5 --batch_size 1 --output_path evaluation_results/gsm8k --device cuda 2>&1 | tee -a evaluation_results/benchmark_suite.log
echo "GSM8K DONE" | tee -a evaluation_results/benchmark_suite.log
# ... repeat for remaining benchmarks
EOF

# Step 2: Launch via terminal(background=true)
# The SSH session itself is backgrounded, not the inner process
terminal(background=true, command="ssh djg6228@10.0.0.171 'nohup bash /data/SpecForge/custom_dflash/restart_benchmarks.sh > /dev/null 2>&1 < /dev/null & echo $!'")

# Step 3: Verify in follow-up terminal call
ssh djg6228@10.0.0.171 "ps aux | grep lm_eval | grep -v grep; tail -5 /path/to/benchmark_suite.log"

# Step 4: Kill zombie processes if old PID still shows
djg6228  3779075  0.0  0.0      0     0 ?        Zl   May11   0:00 [lm_eval] <defunct>
# Zombies are harmless — will clear on system restart. Do not chase.
```

**Key insight:** The `terminal(background=true)` tool backgrounds the ENTIRE SSH session. The `nohup` inside SSH is just insurance against SIGHUP if the SSH connection drops. The `echo $!` captures the remote PID for status checks.

### CRITICAL NEW FINDING: generation_config.json Overrides Token Limits (May 11, 2026)

After patching task YAML and using `--gen_kwargs`, GSM8K still used `max_new_tokens=32768`. The root cause was the model's `generation_config.json`:

```bash
# The model directory contains a generation_config.json with max_new_tokens: 32768
cat /path/to/merged/generation_config.json
# {"max_new_tokens": 32768, ...}
```

**Hierarchy of max_new_tokens resolution (strongest to weakest):**
1. **Model `generation_config.json`** — loaded by transformers, overrides everything
2. **Task YAML `generation_kwargs`** — only effective if model config doesn't specify
3. **CLI `--gen_kwargs`** — overridden by both above

**Fix:** Patch `generation_config.json` directly:
```bash
cat > /path/to/merged/generation_config.json << 'EOF'
{
  "bos_token_id": <your_bos>,
  "do_sample": true,
  "eos_token_id": [<your_eos>],
  "max_new_tokens": 512,
  "pad_token_id": <your_pad>,
  "temperature": 1.0,
  "top_p": 1.0
}
EOF
```

After patching, verify in logs:
```
gsm8k: Using gen_kwargs: {'until': ['Question:', '</s>', '<|im_end|>'], 'do_sample': False, 'temperature': 0.0, 'max_new_tokens': 512}
[transformers] Both `max_new_tokens` (=512) and `max_length`... `max_new_tokens` will take precedence.
```

**Impact:** Without this fix, generate_until tasks on GB10 are 60x slower (30s/it with 32K tokens vs ~0.5s/it with 512 tokens) and much more likely to OOM or die silently.

### vLLM Qwen3.5 Text-Only Config Bug (May 11, 2026)

**vLLM 0.20.2 cannot load Qwen3.5 text-only models.** The model handler hardcodes multimodal `Qwen3_5Config` but text-only models use `Qwen3_5TextConfig`.

**Error:** `TypeError: Invalid type of HuggingFace config. Expected type: Qwen3_5Config, but found type: Qwen3_5TextConfig`

**Root cause:** vLLM's `Qwen3_5ProcessingInfo.get_hf_config()` demands `Qwen3_5Config` (multimodal parent). Text-only models have `model_type: "qwen3_5_text"` → transformers returns `Qwen3_5TextConfig` → type mismatch.

**Workarounds attempted (all failed):**
- Config swap to `Qwen3_5Config` with dummy vision_config → next error: `Can't load image processor`
- Dummy `preprocessor_config.json` → process hangs during vision processor init
- Monkey-patch multimodal registry → error occurs before registry check
- Monkey-patch `get_hf_config` → `'dict' object has no attribute 'spatial_merge_size'`
- vLLM 0.19.0 downgrade → `ImportError: libcudart.so.12` (CUDA 13.0 mismatch)

**Resolution:** Do NOT use vLLM ≤0.20.2 for Qwen3.5 text-only models. Use direct Python or wait for vLLM 0.21.0+.

**This affects:** Any text-only Qwen3.5 variant (27B dense, 14B, 7B, etc.) when served via vLLM.

## HumanEval Requirements (May 12, 2026)

HumanEval is marked as UNSAFE in lm-eval-harness. Two requirements:

1. **Environment variable:** `export HF_ALLOW_CODE_EVAL=1`
2. **CLI flag:** `--confirm_run_unsafe_code`

Without BOTH, the task fails immediately after model load with:
```
ValueError: Attempted to run task: humaneval which is marked as unsafe. Set confirm_run_unsafe_code=True to run this task.
```

**Verified result on Qwen 27B BF16:** pass@1 = 82.93% (excellent for 27B)

## BBH Performance Reality (May 12, 2026)

BBH is a generate_until task with 6511 examples. At ~30-45s per example on GB10:
- **Estimated runtime: 50-80 hours**
- This is NORMAL for a 27B model on single GB10
- Do NOT kill prematurely — progress counter is trustworthy

## Direct Python Evaluation (Fast Verification)

For rapid post-training verification (~5 minutes), direct `transformers` evaluation works reliably:

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

model = AutoModelForCausalLM.from_pretrained(
    "/path/to/merged",
    torch_dtype=torch.bfloat16,
    device_map="auto",
    trust_remote_code=True
)
# ~5 min load time for 51GB BF16 model on GB10
# GPU utilization hits 94-95% once loaded
```

**CRITICAL: Direct Python is NOT faster than lm-eval-harness for full benchmarks.**
Both use the same transformers generate() path. The slowness is the model, not the harness.
A 27B model on GB10 takes ~30-60s per GSM8K example (max_new_tokens=256). At 1319 examples,
that's 11-22 hours for GSM8K alone. Direct Python has the same bottleneck.

**When to use direct Python:**
- Quick sanity checks (10-50 examples)
- When lm-eval-harness is broken for a specific task
- Custom evaluation logic that lm-eval-harness doesn't support

**When NOT to use direct Python:**
- Full benchmark suites (same speed, more code to maintain)
- When vLLM is available (vLLM is 5-10x faster)

## vLLM-Based Evaluation (RECOMMENDED for Speed)

For full benchmark suites, serve the model with vLLM and use API-based evaluation:

```bash
# Start vLLM server (one-time, stays up)
vllm serve /path/to/merged --dtype bfloat16 --max-model-len 4096 --gpu-memory-utilization 0.9

# Run benchmarks via API (much faster)
lm_eval --model vllm --model_args pretrained=/path/to/merged,dtype=bfloat16 \
  --tasks gsm8k --batch_size auto --output_path results/gsm8k
```

**vLLM vs transformers quality:** For greedy decoding (temperature=0, do_sample=False),
outputs are IDENTICAL. vLLM uses PagedAttention for memory efficiency and continuous
batching for throughput — same logits, same tokens, same answers.

**Speedup:** 5-10x faster on single GPU. GSM8K drops from ~20h to ~2-4h.

**Setup cost:** ~10-15 minutes to start vLLM server. Worth it for any benchmark >100 examples.

### Tokenizer Files Requirement
After LoRA merge, copy tokenizer files from base model to merged directory:
```bash
cp /data/models/Qwen3.6-27B-Uncensored/tokenizer* /path/to/merged/
cp /data/models/Qwen3.6-27B-Uncensored/vocab.json /path/to/merged/ 2>/dev/null || true
```

## Evaluation Results Storage

| Benchmark | Output Path | Status Check |
|-----------|-------------|--------------|
| MMLU | `results/mmlu/` | `ls results/mmlu/*.json` |
| GSM8K | `results/gsm8k/` | `ls results/gsm8k/*.json` |
| HumanEval | `results/humaneval/` | `ls results/humaneval/*.json` |
| BBH | `results/bbh/` | `ls results/bbh/*.json` |
| ARC | `results/arc/` | `ls results/arc/*.json` |
| WinoGrande | `results/winogrande/` | `ls results/winogrande/*.json` |

## Performance Characteristics (GB10, 51GB BF16 Qwen 27B)

| Metric | Value |
|--------|-------|
| Model Load Time | ~5 minutes |
| GPU Utilization | 92-95% during inference |
| VRAM Usage | ~57GB |
| Inference Speed (batch=1) | 1.1s/request initially, improves to 0.14s/request |
| System RAM | 121GB total, 102GB used during load |
| Temperature | 75-80°C sustained |
| MMLU Full Runtime | ~4h 43m |
| MMLU Score | 86.57% |
| GSM8K Score | 66.19% (strict-match) |
| HumanEval Score | 82.93% pass@1 |

## Verified Benchmark Results (May 2026, Qwen 27B BF16)

| Benchmark | Score | Runtime | Notes |
|-----------|-------|---------|-------|
| MMLU | 86.57% | ~4h 43m | loglikelihood, reliable |
| GSM8K | 66.19% | ~12h | generate_until, needs max_new_tokens patch |
| HumanEval | 82.93% | ~44m | generate_until, needs HF_ALLOW_CODE_EVAL=1 + --confirm_run_unsafe_code |
| BBH | TBD | ~50-80h | generate_until, 6511 examples |
| ARC | TBD | TBD | loglikelihood, reliable |
| WinoGrande | TBD | TBD | loglikelihood, reliable |

## User Preference Signal

When user says "run all benchmarks, i dont care how long it takes":
- Do NOT argue about time
- Do NOT suggest partial/limit runs
- Do NOT suggest faster alternatives
- DO launch full benchmarks immediately
- DO use background process to survive disconnects
- DO provide periodic status updates
