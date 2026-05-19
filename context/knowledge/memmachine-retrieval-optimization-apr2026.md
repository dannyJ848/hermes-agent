# MemMachine Retrieval Optimization Breakdown
**Paper**: arXiv:2604.04853 (April 2026)
**Authors**: Shu Wang, Edwin Yu et al.

## Key Insight
Retrieval-stage optimizations outperform ingestion-stage optimizations by 5x.

## Retrieval-Stage Rankings (by improvement)
1. Retrieval depth tuning: +4.2%
2. Context formatting: +2.0%
3. Search prompt design: +1.8%
4. Query bias correction: +1.4%

vs Ingestion-stage:
- Sentence chunking: +0.8%

## Applications to Evey Tip Injection
- Increase tip retrieval depth from 5-8 to 10-15 for complex tasks
- Format tips with structured tags ([TIP]...[/TIP])
- Extract keywords from last tool result + error, not just user message
- Add semantic similarity to overcome keyword bias
- Diversity constraint: max 2 tips per domain per injection

## Cost Efficiency
GPT-5-mini beats GPT-5 by 2.6% with optimized prompts — smaller models with better retrieval beat larger models with worse retrieval.

