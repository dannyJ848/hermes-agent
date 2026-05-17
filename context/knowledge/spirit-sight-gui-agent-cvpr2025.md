# spirit-sight-gui-agent-cvpr2025

*Researched: 2026-04-05 02:42 CDT*

# SpiritSight Agent: Advanced GUI Agent with One Look (CVPR 2025)

**Paper:** arXiv:2503.03196 | **Authors:** Zhiyuan Huang, Ziming Cheng, Junting Pan, Zhaohui Hou, Mingjie Zhan
**Venue:** CVPR 2025 | **Date:** March 2025

## Key Innovation
SpiritSight is a vision-based, end-to-end GUI agent that achieves high accuracy across multiple GUI platforms (web, mobile, desktop) using a single screenshot — "one look" inference.

## Two Core Contributions

### 1. GUI-Lasagne Dataset
- Multi-level, large-scale, high-quality GUI interaction dataset
- Built using scalable (likely synthetic/programmatic) methods
- Provides robust GUI understanding and element grounding training data
- Addresses the data scarcity problem for GUI agents

### 2. Universal Block Parsing (UBP)
- Resolves ambiguity in dynamic high-resolution visual inputs
- Problem: high-res screenshots have too many candidate elements, causing grounding confusion
- UBP structures the visual input into parseable blocks, reducing grounding search space
- This is the key technique enabling accurate "one look" interaction

## Performance
- Outperforms other advanced methods on diverse GUI benchmarks
- Demonstrates superior cross-platform compatibility
- Maintains low latency (vision-based, no DOM/HTML access needed)

## Relevance to Hermes Agent
- **Direct application:** Our browser_vision tool does screenshot-based grounding. SpiritSight's UBP approach could improve element identification.
- **Dataset:** GUI-Lasagne could train/fine-tune grounding models for better tool accuracy.
- **Architecture pattern:** End-to-end vision → action without DOM access is what we need for iOS/macOS automation where accessibility APIs are limited.
- **Code available:** https://github.com (paper mentions available models and datasets)

## Comparison with Other CVPR 2025 GUI Agents
- **ShowUI:** 2B parameter VLA model, focuses on efficiency
- **GUI-Xplore:** Exploration-based approach for generalization
- **SpiritSight:** Focuses on grounding accuracy via UBP + data scale
- All three represent the convergence point: vision-only GUI agents achieving practical accuracy

## Key Insight for Agent Development
The "ambiguity problem in dynamic high-resolution" is exactly what limits browser_vision accuracy on complex pages. UBP's approach of structuring the visual space before grounding is applicable to any screenshot-based agent tool.


## Sources

- https://arxiv.org/abs/2503.03196
- https://voxel51.com/blog/visual-agents-at-cvpr-2025
