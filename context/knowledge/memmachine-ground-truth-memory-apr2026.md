# memmachine-ground-truth-memory-apr2026

*Researched: 2026-04-08 11:58 CDT*

# MemMachine: Ground-Truth-Preserving Memory for AI Agents
**Paper**: arXiv:2604.04853 (April 2026)
**Authors**: Shu Wang, Edwin Yu et al.

## Key Innovation
Open-source memory system that preserves ground truth by storing entire episodes instead of lossy LLM-extracted summaries. Uses contextualized retrieval.

## Key Results
- 0.9169 on LoCoMo (gpt4.1-mini)
- 93.0% on LongMemEvalS (ICLR 2025)
- 80% fewer input tokens than Mem0
- Retrieval-stage optimizations >> ingestion-stage (5x impact)

## Retrieval Optimizations
1. Retrieval depth tuning: +4.2%
2. Context formatting: +2.0%
3. Search prompt design: +1.8%
4. Query bias correction: +1.4%
5. Adaptive routing: direct / parallel decomposed / semantic

## Applications to Evey
- Ground-truth preservation → never LLM-rewrite tips, store originals
- Contextualized retrieval → expand matches with surrounding context
- Retrieval > ingestion → invest in matching quality, not storage format
- 80% token reduction → targeted injection (5-8 tips, not all 970+)
- Adaptive routing → match retrieval strategy to query complexity


## Sources

- https://arxiv.org/abs/2604.04853
