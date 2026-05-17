# attention-residuals-attnres

*Researched: 2026-03-31 22:57 CDT*

# Attention Residuals (AttnRes): Smarter Skip Connections

## Key Insight
Standard residual connections (add layer output to running sum) are dumb -- they weight all layers equally. AttnRes replaces this with learned, input-dependent attention over depth. Each layer selectively attends to the most relevant PREVIOUS layer outputs, not just the last one.

## Architecture
- Full AttnRes: softmax attention over all preceding layer outputs, using a learned pseudo-query per layer
- Block AttnRes: partitions layers into ~8 blocks, attention only over block-level reps (practical overhead reduction)
- Drop-in replacement -- same interface as standard residuals

## Why Standard Residuals Fail
- Uniform accumulation dilutes each layer's contribution
- Hidden-state magnitudes grow unboundedly (PreNorm problem)
- Deeper models = more dilution

## AttnRes Fix
- Each layer gets selective, content-aware access to earlier representations
- Learned weights (alpha_i) control which previous layers matter most
- Block version: O(Nd) memory instead of O(Ld)

## Relevance
- Could improve ANY transformer-based model including agent LLMs
- The "selective aggregation" principle applies to multi-agent communication too
- Block AttnRes pattern could improve how agents aggregate information from parallel sub-agents

## Source
- https://github.com/MoonshotAI/Attention-Residuals (2.9k stars, MIT)
- Paper: arXiv 2603.15031


## Sources

- https://github.com/MoonshotAI/Attention-Residuals
