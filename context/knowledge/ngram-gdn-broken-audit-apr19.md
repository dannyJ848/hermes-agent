# ngram-gdn-broken-audit-apr19

*Researched: 2026-04-19 22:17 CDT*

# Ngram Speculative Decoding BROKEN on Qwen3.6 GDN Hybrid — Audit Results

**Date:** April 19, 2026
**Severity:** CRITICAL (output corruption, no errors raised)

## Bug Status (Live Check)
- vLLM #39273: **OPEN** — ngram produces corrupted output on hybrid GDN models
- PR #39463: **UNDER REVIEW, NOT MERGED** — proposed fix has 3 high-priority code review issues
- vLLM #38196: **FIXED** (PR #34871, merged Mar 16) — fixes CRASH but NOT corruption
- vLLM #38182 (MTP): **OPEN** — no fix yet, volunteer assigned Apr 14
- DFlash (#32094, PR #36847): **MERGED Apr 7** — available in vLLM 0.19.1+ and v020-tq image

## Root Cause
SSM recurrent state misplacement after token rejection. GDN layers advance state by N tokens
during draft verification but CANNOT roll back when tokens are rejected. Non-spec kernel then
reads stale state from position 0 instead of accepted state, causing progressive corruption.

## Scripts Fixed
All 4 launch scripts patched:
1. **spark-day1.sh** — Removed inline comment bugs (2x), added DFlash with $SPEC_BF16/$SPEC_FP8 variables
2. **deploy-spark-day1.sh** — Removed ngram fallback, replaced with no-spec safe baseline
3. **superqwen3-super.sh** — Set ngram_arg_bf16/fp8 to empty "", added GDN warning comments
4. **spark-maxperf.sh** — Already clean (no ngram references)

## Safe Speculative Decoding Chain
DFlash (ON by default) → no speculative decoding (safe baseline)
NEVER use ngram/suffix on Qwen3.6 until #39463 merges and is verified on GDN hybrid.

## Sources

- https://github.com/vllm-project/vllm/issues/39273
- https://github.com/vllm-project/vllm/pull/39463
- https://github.com/vllm-project/vllm/issues/38182
- https://github.com/vllm-project/vllm/issues/32094
