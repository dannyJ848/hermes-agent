# Post-Training Evaluation Patterns on DGX Spark (GB10) — UPDATED May 12, 2026

Session: May 10-12, 2026 — Qwen 27B Expert Logician evaluation

## Verified Benchmark Results (May 2026, Qwen 27B BF16)

| Benchmark | Score | Runtime | Task Type | Reliability |
|-----------|-------|---------|-----------|-------------|
| MMLU | **86.57%** | ~4h 43m | loglikelihood | ✅ Reliable |
| GSM8K | **66.19%** (strict) | ~12h | generate_until | ⚠️ Needs max_new_tokens patch |
| HumanEval | **82.93%** pass@1 | ~44m | generate_until | ⚠️ Needs HF_ALLOW_CODE_EVAL=1 + --confirm_run_unsafe_code |
| BBH | TBD | ~50-80h est. | generate_until | ⚠️ Very long, monitor for silent death |
| ARC | TBD | TBD | loglikelihood | ✅ Reliable |
| WinoGrande | TBD | TBD | loglikelihood | ✅ Reliable |

### MMLU Breakdown
| Category | Score |
|----------|-------|
| Humanities | 82.27% |
| STEM | 85.98% |
| Social Sciences | 91.91% |
| Other | 88.38% |

## CRITICAL: generation_config.json Overrides ALL Token Limits

After patching task YAML and using `--gen_kwargs`, GSM8K still used `max_new_tokens=32768`. The root cause was the model's `generation_config.json`:

```bash
cat /path/to/merged/generation_config.json
# {"max_new_tokens": 32768, ...}
```

**Hierarchy of max_new_tokens resolution (strongest to weakest):**
1. **Model `generation_config.json`** — loaded by transformers, overrides everything
2. **Task YAML `generation_kwargs`** — only effective if model config doesn't specify
3. **CLI `--gen_kwargs`** — overridden by both above

**Fix:** Patch `generation_config.json` directly:
```bash
python3 -c "
import json
with open('/path/to/merged/generation_config.json', 'r') as f:
    config = json.load(f)
config['max_new_tokens'] = 512
with open('/path/to/merged/generation_config.json', 'w') as f:
    json.dump(config, f, indent=2)
"
```

**Verification:** Log should show:
```
gsm8k: Using gen_kwargs: {'until': ['Question:', '</s>', '<|im_end|>'], 'do_sample': False, 'temperature': 0.0, 'max_new_tokens': 512}
[transformers] Both `max_new_tokens` (=512) and `max_length`... `max_new_tokens` will take precedence.
```

**Impact:** Without this fix, generate_until tasks on GB10 are 60x slower (30s/it with 32K tokens vs ~0.5s/it with 512 tokens) and much more likely to OOM or die silently.

**Note:** Even with generation_config.json patched, lm-eval-harness may still show warnings:
```
[transformers] Both `max_new_tokens` (=512) and `max_length`(=1093) seem to have been set. `max_new_tokens` will take precedence.
```
This is NORMAL and SAFE. The `max_length` comes from the task YAML (prompt length + max_new_tokens), and `max_new_tokens` from generation_config.json takes precedence. The warning is informational, not an error.

## SSH Background Process Spawning (Hermes Terminal Tool)

**Hermes terminal tool FAILS with `&`, `nohup`, `setsid`, or `disown` in foreground SSH.**

Errors encountered:
- `Foreground command uses shell-level background wrappers`
- `necho` parsing bug (corrupted output)
- Process starts but terminal hangs waiting for it

**Reliable pattern:** Write script on remote host, then run via single ssh command that captures PID:

```bash
# Step 1: Write script on remote host via SSH printf
ssh djg6228@10.0.0.171 "cat > /tmp/start_benchmark.sh << 'EOF'
#!/bin/bash
cd /data/SpecForge/custom_dflash
source eval_venv/bin/activate
export HF_ALLOW_CODE_EVAL=1
lm_eval --model hf --model_args pretrained=/data/SpecForge/custom_dflash/checkpoints/final_model_merged,dtype=bfloat16 --tasks humaneval --batch_size 1 --output_path /data/SpecForge/custom_dflash/evaluation_results/humaneval --device cuda --confirm_run_unsafe_code > /tmp/lm_eval_humaneval.log 2>&1 &
echo $! > /tmp/humaneval.pid
EOF"

# Step 2: Run script and capture PID
ssh djg6228@10.0.0.171 "bash /tmp/start_benchmark.sh; sleep 5; cat /tmp/humaneval.pid"
# Returns: 1115296

# Step 3: Verify in follow-up
ssh djg6228@10.0.0.171 "ps aux | grep 1115296 | grep -v grep"
```

**Key points:**
- The `&` is INSIDE the script, not in the SSH command
- The script writes PID to a file for later checking
- `terminal(background=true)` is NOT needed if the remote process backgrounds itself
- The SSH command returns immediately (just echoes PID), so Hermes doesn't wait

## MacBook Disk Full Recovery

When MacBook disk is full (~100% capacity):
- Hermes terminal tool FAILS with `No space left on device`
- Cannot write temporary scripts to `/tmp/` or `/var/folders/`
- Cannot use `write_file` tool (writes to local disk first)

**Workaround:** Write scripts directly on remote host via SSH:
```bash
# Instead of: write_file(path="/tmp/script.sh") → fails
# Use: ssh host "cat > /tmp/script.sh << 'EOF'...EOF"
ssh djg6228@10.0.0.171 "printf '%s\n' '#!/bin/bash' 'cd /data/...' 'command' > /tmp/script.sh"
```

**Long-term fix:** Move large directories (`~/datasets`, `~/Downloads`) to external SSD formatted as exFAT for cross-platform compatibility.

## NTFS/exFAT Cross-Platform SSD Workflow

**DGX (Ubuntu) ↔ MacBook SSD transfer workflow:**

| Format | DGX (Ubuntu) | MacBook | Recommendation |
|--------|-------------|---------|----------------|
| NTFS | ✅ Native read/write | ❌ Read-only (no native write) | DGX-only storage |
| exFAT | ✅ Native read/write | ✅ Native read/write | **Best for cross-platform** |
| APFS | ❌ Not supported | ✅ Native | Mac-only |

**If SSD is NTFS and you need Mac write access:**
- `ntfs-3g` requires Linux (won't install on macOS via Homebrew)
- macOS experimental NTFS write (`mount -t ntfs -o rw`) is removed in recent versions
- Third-party tools (Mounty, macFUSE) may work but require kernel extensions and user approval
- If filesystem is corrupted (Invalid BS_jmpBoot in boot block), these tools silently fail

**Recommendation:** Reformat SSD to exFAT for seamless Mac ↔ DGX transfers:
```bash
# On MacBook
diskutil eraseDisk exFAT SSD8TB disk6
```

## Silent Death on generate_until Tasks

**Loglikelihood tasks (MMLU, ARC, WinoGrande) complete reliably.**
**generate_until tasks (GSM8K, HumanEval, BBH) can SILENTLY DIE.**

Observed on Qwen 27B BF16 (51GB) GSM8K:
- Process reached 75% (984/1319) after ~10.5 hours
- Process vanished without error message, crash dump, or exception
- No partial results saved
- GPU went idle (0% utilization, 37°C)
- Likely cause: OOM or driver timeout on long-running generate_until tasks

**Mitigation:**
1. Run benchmarks individually (not chained)
2. Use direct Python evaluation for generate_until tasks
3. Monitor GPU temperature and utilization — sudden drop to 0% is death signal
4. Check for zombie processes before restarting: `ps aux | grep lm_eval | grep -v grep`

## Concurrent Process Hazard

When restarting after silent death, ALWAYS verify no old processes are still running:

```bash
ps aux | grep -E 'lm_eval|python3.*benchmark' | grep -v grep
# If old process found, kill it
kill -9 <OLD_PID>
sleep 5
ps aux | grep -E 'lm_eval|python3.*benchmark' | grep -v grep || echo "Clean"
```

**Failure mode:** Old lm_eval process was zombie/defunct but still held GPU context.
New process started, both tried to load model simultaneously. System load spiked to 44+.
GPU context conflicts, extreme slowdown, potential hangs.

**Rule:** One benchmark at a time on GB10. No concurrent model loads.

## Speed Fluctuations Are Normal — NOT Thermal Throttling

**Observation (May 2026, GSM8K on GB10):** Generation speed fluctuated wildly during the run:

| Progress | Speed | Notes |
|----------|-------|-------|
| 0-150 | 37s/it | Initial warmup |
| 150-217 | 12s/it | Faster problems |
| 217-280 | 48s/it | Slower problems |
| 280-493 | 15s/it | Fast again |
| 493-625 | 43s/it | Slow again |
| 625-676 | 12s/it | Fast |
| 676-850 | 41s/it | Slow |
| 850-966 | 12s/it | Fast |
| 966-1070 | 16s/it | Fast |

**GPU temperature throughout:** 57-58°C, P0 performance state, no thermal throttling.

**Conclusion:** Speed variation is due to **problem difficulty**, not hardware issues. GSM8K problems vary in complexity — some require multi-step reasoning (slow), others are simple (fast). The model generates until it hits a stop token, so complex problems take more tokens and more time.

**Do NOT kill the process during speed fluctuations.** Trust the progress counter over the `s/it` metric.

## HumanEval Requirements

HumanEval is marked as UNSAFE in lm-eval-harness. Two requirements:

1. **Environment variable:** `export HF_ALLOW_CODE_EVAL=1`
2. **CLI flag:** `--confirm_run_unsafe_code`

Without BOTH, the task fails immediately after model load with:
```
ValueError: Attempted to run task: humaneval which is marked as unsafe. Set confirm_run_unsafe_code=True to run this task.
```

## BBH Performance Reality

BBH is a generate_until task with 6511 examples. At ~30-45s per example on GB10:
- **Estimated runtime: 50-80 hours**
- This is NORMAL for a 27B model on single GB10
- Do NOT kill prematurely — progress counter is trustworthy

### BBH Speed Degradation Over Time

**Observed (May 2026):** BBH started at ~24s/it but degraded to 76s/it after 3+ hours.
At 76s/it, runtime extends to **5+ days** — impractical.

**Cause:** Unknown — possibly memory fragmentation, KV cache accumulation, or
increasingly complex reasoning chains as easier examples are exhausted.

**Mitigation:**
1. Monitor speed in first 100 examples — if >40s/it, consider skipping
2. Run BBH LAST (after all other benchmarks)
3. Use vLLM-based evaluation for BBH (5-10x faster)
4. Accept that BBH on single GB10 may be impractical for full run

### Benchmark Prioritization Strategy

When running multiple benchmarks and some are very slow:

| Priority | Benchmark | Type | Speed | Action |
|----------|-----------|------|-------|--------|
| 1 | MMLU | loglikelihood | ~5h | Run first — reliable, fast |
| 2 | ARC Challenge | loglikelihood | ~30m | Run second — reliable |
| 3 | WinoGrande | loglikelihood | ~15m | Run third — reliable |
| 4 | HumanEval | generate_until | ~45m | Run fourth — needs unsafe flag |
| 5 | GSM8K | generate_until | ~12h | Run fifth — needs gen_config patch |
| 6 | BBH | generate_until | 50-80h+ | Run LAST or skip — very slow |

**User preference:** Skip impractically slow benchmarks, return to them later.
Do NOT argue about time when user says "run all benchmarks, i dont care how long it takes".
DO launch immediately, DO provide status updates, DO have recovery plan.

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
```

**CRITICAL: Direct Python is NOT faster than lm-eval-harness for full benchmarks.**
Both use the same transformers generate() path. The slowness is the model, not the harness.

**When to use direct Python:**
- Quick sanity checks (10-50 examples)
- When lm-eval-harness is broken for a specific task
- Custom evaluation logic that lm-eval-harness doesn't support

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

## User Preference Signal

When user says "run all benchmarks, i dont care how long it takes":
- Do NOT argue about time
- Do NOT suggest partial/limit runs
- Do NOT suggest faster alternatives
- DO launch full benchmarks immediately via background process
- DO provide periodic status updates
- DO have a recovery plan for silent death

## Post-Training Dataset Management

After a model is trained, the training datasets are **for archive only**.

**Do NOT retrain on the same data:**
- Fine-tuning again on identical data → overfitting, no new learning
- Continued training on same data → catastrophic forgetting
- Datasets are only useful for: training a NEW model from scratch, or as reference

**Storage strategy:**
- Keep datasets on external SSD (exFAT for Mac+DGX compatibility)
- Free up MacBook local disk by deleting `~/datasets` after SSD backup
- On DGX, store in `/mnt/bigssd/` or `/data/` only if actively training
- 337GB of training data on MacBook local disk is wasteful — move to SSD

**When datasets ARE useful again:**
- Starting a new training run with different architecture
- Distilling to a smaller model
- Creating a derivative dataset (mixing with new data)
- Regulatory/compliance audit requiring training data provenance
