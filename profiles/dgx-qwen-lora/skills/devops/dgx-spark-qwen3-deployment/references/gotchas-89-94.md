# Gotchas 89-94: Launch Day Optimizations

## 89. NGRAM REMOVED — BROKEN on GDN hybrid models (SUPERSEDED, Apr 19 2026)

**CRITICAL:** Ngram speculative decoding produces CORRUPTED output on Qwen3.6 GDN hybrid models.
vLLM issue #39273 — PR #39463 under review, NOT merged as of Apr 19 2026.

Root cause: SSM recurrent state misplacement after token rejection. When ngram rejects
draft tokens, the GDN state can't roll back correctly — stale state from position 0 is
read instead of the accepted state, causing progressive output corruption (repeated
fragments, degenerate text, topic fixation). NO crash, NO error — silent corruption.

This affects ALL ngram/suffix methods on GDN hybrid models (Qwen3.5, Qwen3.6).
NOT affected: DFlash (model-based, like EAGLE), MTP (separate state management).

**Action taken (Apr 19 audit):** All ngram flags REMOVED from all 4 scripts.
- spark-day1.sh: DFlash wired in via $SPEC_BF16/$SPEC_FP8 variables
- deploy-spark-day1.sh: ngram fallback replaced with no-spec (safe baseline), SPEC_ARG=""
- superqwen3-super.sh: ngram_arg variables set to empty ""
- spark-maxperf.sh: already clean (no ngram references)

**Safe fallback chain:** DFlash (ON by default) → no speculative decoding (safe).
Do NOT re-enable ngram until vLLM #39463 is merged AND verified on GDN hybrid.

## 90. Shell comment bug in docker run commands (Apr 19 2026)

NEVER put `# comment` lines inside a `docker run` command after `\` line continuation.
The `\` makes the next line part of the command, so `# MTP disabled...` gets passed as
literal arguments to docker/vLLM. This was a pre-existing bug in spark-day1.sh (2x)
and deploy-spark-day1.sh (2x, fixed earlier).

**WRONG:**
```bash
docker run ... \
    --language-model-only \
    # This comment becomes a docker arg!
    2>&1 >> "$LOG_FILE"
```

**RIGHT:**
```bash
docker run ... \
    --language-model-only \
2>&1 >> "$LOG_FILE"
# This comment is outside the command
```

Fixed in all scripts during Apr 19 audit.

## 91. SGLang 29% faster than vLLM for MoE throughput (Apr 19 2026)

SGLang delivers ~29% higher throughput than vLLM on MoE models (community benchmarks H100).
DGX Spark docker image available: `scitrera/dgx-spark-sglang:0.5.9-t5` (pulled in spark-day1.sh).
Not wired into launch commands yet — available as fallback/upgrade path.

## 92. FP8 KV cache silently corrupts on SOME models/Blackwell combos (Apr 19 2026)

Reddit: `fp8_e4m3` KV cache on Qwen3.5-122B doesn't crash — it silently produces corrupt output.
No error, no warning. vLLM issue #37618: root cause is DeepGEMM E8M0 scale format on non-MoE FP8.
For Qwen3.6-35B-A3B specifically, DGX Spark forum shows `fp8_e5m2` KV cache working correctly.
Always verify output quality after enabling FP8 KV cache — don't assume no errors = correct.

## 93. vLLM ngram spec decode accepts --speculative-decoding-method CLI flag (SUPERSEDED)

~~Confirmed working in vLLM v0.20+~~ SUPERSEDED by gotcha #89 — ngram is BROKEN on GDN hybrid.
Do NOT use ngram on Qwen3.6 until vLLM #39273 is fixed.

## 94. MiMo V2 Pro free on Nous Portal (14-day trial, Apr 19 2026)

Nous Research partnered with Xiaomi for 14-day free MiMo V2 Pro access via Nous Portal.
Good for: compression tasks, vision, auxiliary routing. Community reports competitive with
Kimi K2.5 on OpenRouter. Can wire as free-tier auxiliary model in Hermes config while trial lasts.
