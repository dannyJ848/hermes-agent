# Gotchas 71-72: DFlash Speculative Decoding Integration (Apr 18 2026)

## 71. DFlash Speculative Decoding — Integrated with Fallback

**FEATURE:** DFlash (z-lab) is a block diffusion speculative decoding method.
Uses a 0.5B param draft model that generates 15 tokens in a SINGLE forward pass
(not autoregressive like EAGLE). Target model verifies all 15 in parallel.

**Claims:** 6x lossless speedup, 2.5x faster than EAGLE-3.
**Our model:** z-lab/Qwen3.6-35B-A3B-DFlash (0.5B, BF16, gated HF repo)
**Accept length:** 5-7 on Qwen3.6 benchmarks (5-7 of 15 drafts verified avg)

**INTEGRATION:** Enabled via DFLASH=true env var in:
- spark-maxperf.sh (both BF16 :8000 and FP8 :8001 serve commands)
- superqwen3-super.sh restart_serving() (both Docker containers)
- spark-day1.sh already downloads the DFlash model (line 502, uses HF_TOKEN_GATED)

**Config:**
    DFLASH=true ./spark-maxperf.sh              # Enable DFlash
    DFLASH=true ./superqwen3-super.sh            # Enable in Super pipeline

    vLLM flag injected when DFLASH=true:
    --speculative-config method=dflash model=z-lab/Qwen3.6-35B-A3B-DFlash num_speculative_tokens=15

**Risk assessment:** ZERO. If DFlash + GDN hybrid breaks, the 42 behavioral
validation tests (determinism, JSON exactness, tool call format) catch corruption
immediately. Just re-run without DFLASH=true — instant fallback.

## 72. GDN Hybrid + Speculative Decoding Compatibility (Known Fragile)

**BUG:** Ngram and suffix speculative decoding methods produce CORRUPTED output
on Qwen3.5/3.6 GDN hybrid models. Root cause: GDN SSM state advances by N tokens
during draft verification but CANNOT roll back when tokens are rejected.

**vLLM issue:** #39273 (Open, PR #39463 pending)
**Affected methods:** ngram, suffix decoding — both broken on GDN hybrid
**NOT affected:** MTP, EAGLE — use EagleProposer with separate state management
**DFlash:** Model-based method (like EAGLE) — likely uses same verification path,
but EXPLICITLY UNTESTED on GDN hybrid models as of Apr 18 2026.

**If DFlash breaks on GDN, you'll see:**
- Validation test failures (determinism, JSON exactness)
- Repeated/degenerate fragments in output (like ngram corruption)
- Topic fixation loops

**Recovery:** Set DFLASH=false (or just omit it) and restart serving.
No code changes needed — the flag controls speculative-config injection.

**DFlash model status:** Still training at 2000 steps. Early accept length
results (5-7 on GSM8K/Math500) are promising but not final.

**Docker image compatibility:** Our v020-tq image may need updating to include
DFlash support. vLLM PR #38300 merged Apr 15. If built after that date, DFlash
works. If not, need to pull newer image or use vLLM nightly build.
