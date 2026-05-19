# fsc-net-fast-slow-consolidation

*Researched: 2026-04-05 06:11 CDT*

# FSC-Net: Fast-Slow Consolidation Networks for Continual Learning (Nov 2025, arXiv 2511.11707)

## Author
Mohamed El Gorrim

## Core Architecture
Dual-network system inspired by neuroscience memory consolidation:
- **Fast Network (NN1)**: Rapid adaptation to new tasks (like hippocampal fast learning)
- **Slow Network (NN2)**: Gradual knowledge consolidation via replay and distillation (like neocortical consolidation)

## Key Finding
**Methodology > Architecture.** A simple MLP outperforms complex similarity-gated variants by 1.2pp. The dual-timescale mechanism itself is what matters, not architectural embellishments.

## Surprising Result
**Pure replay outperforms replay + distillation** for consolidation. Distillation from the fast network introduces recency bias, degrading performance. This challenges the common assumption that knowledge distillation always helps.

## Results
- Split-MNIST: 91.71% ± 0.62% retention (+4.27pp over fast network alone)
- Split-CIFAR-10: 33.31% ± 0.38% retention (+8.20pp over fast network alone, but still below random — needs stronger backbones)

## Relevance to Cerebrum
- **Directly parallels Cerebrum's architecture**: episodic tier (fast) → semantic tier (slow) consolidation
- **Key insight for consolidation logic**: Pure replay (re-experiencing stored episodes) may be better than distillation (summarizing episodes into facts)
- **Practical implication**: When consolidating episodic memories into semantic facts, replay the raw episodes multiple times rather than relying on LLM-generated summaries
- **Dual-timescale principle**: Cerebrum's working memory (seconds) → episodic (hours) → semantic (permanent) already implements this. The paper validates the approach.

## Citation
El Gorrim, M. "FSC-Net: Fast-Slow Consolidation Networks for Continual Learning." arXiv:2511.11707 (Nov 2025).


## Sources

- https://arxiv.org/abs/2511.11707
