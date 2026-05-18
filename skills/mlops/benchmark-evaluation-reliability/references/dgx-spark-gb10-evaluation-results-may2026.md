# DGX Spark GB10 Evaluation Results — May 2026 (Qwen 27B BF16)

## Verified Benchmark Scores

| Benchmark | Score | Runtime | Task Type | Reliability |
|-----------|-------|---------|-----------|-------------|
| MMLU | 86.57% | ~4h 43m | loglikelihood | ✅ Reliable |
| GSM8K (strict) | 66.19% | ~12h | generate_until | ✅ With patch |
| GSM8K (flexible) | 65.73% | ~12h | generate_until | ✅ With patch |
| HumanEval | 82.93% pass@1 | ~44m | generate_until | ✅ With flags |
| ARC Challenge | 60.24% | ~25m | loglikelihood | ✅ Reliable |
| WinoGrande | TBD | TBD | loglikelihood | ✅ Reliable |
| BBH | ⏸️ Skipped | ~50-80h | generate_until | ⚠️ Too long |

## Critical Patches Required

### 1. generation_config.json (MANDATORY for generate_until)

Default `max_new_tokens: 32768` causes extreme slowdown and silent death.

```bash
cat > /path/to/model/generation_config.json << 'EOF'
{
  "bos_token_id": 151643,
  "do_sample": true,
  "eos_token_id": [151643, 151645],
  "max_new_tokens": 512,
  "pad_token_id": 151643,
  "temperature": 1.0,
  "top_p": 1.0
}
EOF
```

### 2. HumanEval Safety Flags

```bash
export HF_ALLOW_CODE_EVAL=1
lm_eval --tasks humaneval --confirm_run_unsafe_code ...
```

Both required. Either alone fails with `ValueError`.

## SSH Background Process Pattern

Hermes terminal tool rejects `&`, `nohup`, `setsid` in SSH commands.

**Working pattern:**
```bash
# Write script on remote via SSH printf
ssh djg6228@10.0.0.171 "printf '%s\n' '#!/bin/bash' 'cd /project' 'source venv/bin/activate' 'lm_eval --tasks arc ... > /tmp/lm_eval_arc.log 2>&1 &' 'echo \$!' > /tmp/arc.pid"

# Execute and capture PID
ssh djg6228@10.0.0.171 "bash /tmp/arc.sh; sleep 5; cat /tmp/arc.pid"
```

## Speed Fluctuations Are Normal

GSM8K speed varied from 12s/it to 58s/it. GPU temp stable at 57-58°C.
Variation is due to problem difficulty, NOT thermal throttling.
Trust progress counter over s/it metric.

## Concurrent Process Hazard

NEVER run multiple benchmarks simultaneously on GB10.
Old zombie process + new process = GPU context conflict, system load 44+.
Always verify clean state before starting:
```bash
ps aux | grep lm_eval | grep -v grep || echo "Clean"
```

## Recommended Evaluation Order

1. MMLU (fast, reliable baseline)
2. ARC Challenge (fast, reliable)
3. WinoGrande (fast, reliable)
4. HumanEval (medium, needs safety flags)
5. GSM8K (long, needs generation_config.json patch)
6. BBH (very long, run last or skip)
