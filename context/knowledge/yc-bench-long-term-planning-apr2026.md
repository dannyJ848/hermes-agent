# yc-bench-long-term-planning-apr2026

*Researched: 2026-04-08 11:55 CDT*

# YC-Bench: Long-Term Planning and Consistent Execution
**Paper**: arXiv:2604.01212 (April 2026)
**Authors**: Muyu He, Adit Jain et al. (Nazneen Rajani group)

## Key Innovation
Benchmark for evaluating strategic coherence over long horizons. Agents run a simulated startup over 1 year (hundreds of turns). 12 models evaluated.

## Critical Findings
1. **Scratchpad is the strongest predictor of success** — persisting info across context truncation
2. **Adversarial client detection = 47% of bankruptcies** — primary failure mode
3. **Only 3 of 12 models surpass $200K starting capital**
4. Claude Opus 4.6: $1.27M, GLM-5: $1.21M at 11x lower cost
5. Over-planning without execution is a distinct failure mode

## Applications to Evey
- Scratchpad → our distilled tips ARE the scratchpad for cross-session persistence
- Adversarial detection → sanitize all inputs before DB writes
- Compounding errors → bad tips compound when upvoted; validate before injection
- GLM-5 cost efficiency → relevant to our model selection


## Sources

- https://arxiv.org/abs/2604.01212
