# Gotchas 73-76: Audit Consistency Fixes (Apr 18 2026)

## 73. Silent Patch Failure in execute_code content.replace()

**BUG:** When using `execute_code` with Python `content.replace(old, new)`, the
replacement can silently fail if `old` string doesn't match the actual file content.
This happens due to:
- Whitespace differences (tabs vs spaces, trailing newlines)
- Previous edits that changed the exact text
- Multi-line strings that look identical but differ in indentation

**Symptom:** `replace()` returns the unchanged content, no error raised. Your code
writes the unchanged file back. Memory records "fixed" but the fix was never applied.

**REAL EXAMPLES from Apr 18 audit:**
1. `UNSLOTH_MOE_BACKEND=grouped_mm` recorded as "added" but replacement failed silently
2. `superqwen3-super.sh` MARLIN + HF_PARALLEL first replacement had too many lines
3. `spark-grpo-train.sh` PYTORCH_TUNABLEOP first patch didn't take

**FIX: ALWAYS verify patches with immediate grep/count check:**
```python
before = content.count('grouped_mm')
content = content.replace(old, new, 1)
after = content.count('grouped_mm')
with open(path, 'w') as f:
    f.write(content)
assert after > before, f"Patch failed! {before} -> {after}"
```

**Also:** Use the shortest, most unique anchor string possible for `old`. Long
multi-line blocks have more chances of whitespace mismatch.

## 74. Docker Env Vars Must Be in ALL Docker Containers

**BUG:** New Docker environment variables added to some scripts but not others.
Scripts that create Docker containers independently each need the env vars explicitly.

**REQUIRED Docker env vars for ALL Qwen3.6 vLLM containers:**
- `-e VLLM_MARLIN_USE_ATOMIC_ADD=1` — atomic GEMM for quantized inference
- `-e PYTORCH_TUNABLEOP_TUNING=1` — auto-tune CuBLAS for Grace Hopper
- `-e HF_ENABLE_PARALLEL_LOADING=1` — 6.6x MoE load speedup (Transformers v5+)

**Verification command:**
```bash
for f in spark-day1.sh spark-maxperf.sh spark-grpo-train.sh superqwen3-super.sh deploy-spark-day1.sh; do
    echo "$f: MARLIN=$(grep -c MARLIN_USE_ATOMIC $f) TUNABLE=$(grep -c TUNABLEOP $f) HF=$(grep -c PARALLEL_LOADING $f)"
done
```

## 75. DFlash Model Uses Local Path, Not HF Repo ID

**BUG:** DFlash speculative-config originally referenced HF repo ID
`z-lab/Qwen3.6-35B-A3B-DFlash` but the model was downloaded via `--local-dir`
(not HF cache format). Docker containers couldn't find it.

**FIX:** Use local path in config + add `HF_HOME=/data/models` to Docker:
```
DFLASH_MODEL="/data/models/Qwen3.6-35B-A3B-DFlash"
```

## 76. All vLLM Serve Commands Need Complete GDN Safety Checklist

**BUG:** spark-day1.sh was missing 3 GDN flags that other scripts had.

**Complete GDN safety checklist for ANY vLLM serve command:**
- `--max-num-seqs 512` (NOT default 1024 — GDN Mamba cache overflow)
- `--chat-template-kwargs '{"preserve_thinking": true, "enable_thinking": true}'`
- `--kv-cache-dtype fp8_e5m2` (NOT bare `fp8`, NOT `turboquant_*`)
- NEVER `--calculate-kv-scales` (vLLM #37554 — GDN corruption)
- `-e VLLM_MARLIN_USE_ATOMIC_ADD=1`
- `-e PYTORCH_TUNABLEOP_TUNING=1`
- `-e HF_ENABLE_PARALLEL_LOADING=1`

**When adding new flags, search ALL scripts** — not just the "main" ones.
