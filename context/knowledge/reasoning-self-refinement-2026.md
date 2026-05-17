# reasoning-self-refinement-2026

*Researched: 2026-04-20 04:56 CDT*

# Reasoning Self-Refinement Techniques (2026)

## Key Methods
1. **GSR (Microsoft)**: Single model generates N parallel candidates, then synthesizes superior answer. Works even when all candidates are wrong. Hybrid training (solve + refine objectives). ICLR 2026 submission.
2. **CAGSR**: Cross-attention-guided refinement via CUDA hooks in vLLM. 3% accuracy gain, 3-4x faster than RL.
3. **ASCoT**: Targets late-stage reasoning errors with positional impact scoring. Multi-perspective self-correction.
4. **SPIRIT**: Perplexity-guided step pruning. 30-50% token reduction, <2% accuracy loss.
5. **VLM-R³**: Multimodal CoT with bounding-box region refinement + GRPO training.

## Agent Implications
- Self-Refine pattern → generate multiple tool-call plans, critique, synthesize
- Perplexity pruning → skip unnecessary tool calls
- Parallel candidates → delegate_parallel, pick best result
- Positional impact → prioritize fixing late-stage workflow errors

## Sources

- https://openreview.net/forum?id=nbhDNDDZMe
- https://www.emergentmind.com/topics/chain-of-thought-self-refinement
- https://arxiv.org/html/2604.00790v1
