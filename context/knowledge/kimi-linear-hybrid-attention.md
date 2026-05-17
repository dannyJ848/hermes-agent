# kimi-linear-hybrid-attention

*Researched: 2026-03-31 22:57 CDT*

# Kimi Linear: Hybrid Linear Attention for 1M Token Context

## Key Insight
Kimi Linear proves you can REPLACE 75% of full attention layers with linear attention AND get better results. The hybrid 3:1 ratio (KDA:global MLA) is the sweet spot -- linear for most layers, full attention for key layers.

## Architecture
- Kimi Delta Attention (KDA): refined Gated DeltaNet with fine-grained gating
- 48B total / 3B activated params (MoE)
- 1M token context length
- Hybrid: 3 KDA layers per 1 MLA (Multi-head Latent Attention) layer
- Trained on 5.7T tokens

## Performance
- MMLU-Pro: 51.0 with similar speed as full attention
- RULER (128K): 84.3 Pareto-optimal, 3.98x speedup
- 6.3x faster TPOT than MLA at 1M tokens
- Reduces KV cache by 75%
- Outperforms full attention in both short and long context

## Why This Matters for Agents
- 1M token context = entire patient history + medical literature in one window
- 6.3x faster decoding = real-time medical consultation feel
- 75% less KV cache = runs on consumer hardware
- The hybrid approach (mostly linear, some full) is the right tradeoff

## Source
- https://github.com/MoonshotAI/Kimi-Linear (1.4k stars, MIT)


## Sources

- https://github.com/MoonshotAI/Kimi-Linear
