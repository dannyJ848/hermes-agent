# cvpr-2025-visual-gui-agents-showui

*Researched: 2026-04-05 03:46 CDT*

# CVPR 2025 Visual GUI Agents: ShowUI and the New Wave

## ShowUI (CVPR 2025) — Lightweight 2B VLA Model for GUI Visual Agents

**Paper:** arXiv:2411.17465 | **Authors:** Kevin Qinghong Lin et al. (Show Lab) | **GitHub:** showlab/ShowUI

### Key Innovations:
1. **UI-Guided Visual Token Selection** — Formulates screenshots as a UI connected graph, identifies redundant relationships, and uses this as criteria for token selection during self-attention blocks. Reduces 33% of redundant visual tokens during training, speeds up performance by 1.4x.
2. **Interleaved Vision-Language-Action Streaming** — Unifies diverse GUI task needs. Manages visual-action history in navigation and pairs multi-turn query-action sequences per screenshot to enhance training efficiency.
3. **Small-scale High-quality GUI Instruction Datasets** — Careful data curation with resampling strategy to address data type imbalances. Only 256K training samples needed.

### Results:
- **75.1% zero-shot screenshot grounding accuracy** with just 2B parameters and 256K data
- Evaluated on Mind2Web (web), AITW (mobile), MiniWob (online) — all navigation benchmarks
- Open-source, end-to-end, lightweight

### Why This Matters for Agent Development:
- Proves that small models (2B) can match or exceed larger models on GUI grounding when trained with smart token selection and interleaved streaming
- UI-guided token selection is transferable — the graph-based redundancy detection could apply to any visual agent architecture
- The interleaved VLA streaming pattern solves the multi-turn visual-action history problem that plagues current GUI agents

## CVPR 2025 Visual Agents Landscape (from Voxel51 Roundup)

The conference featured a wave of complementary papers tackling distinct aspects:

1. **ShowUI** — Efficient VLA model with smart token selection
2. **GUI-Xplore** — Generalizable GUI agents with exploration-based training
3. **SpiritSight Agent** — Advanced GUI agent with "one look" capability (single-screenshot grounding)
4. **ComfyBench** — Benchmarking LLM-based agents in ComfyUI for autonomously designing collaborative AI systems

### Common Trends:
- Moving from perception to interaction — agents that don't just see but act
- Novel architectures for interleaved vision-language-action sequences
- Efficient high-resolution screenshot processing without losing detail
- Precise element grounding for reliable interaction
- Cross-platform compatibility (web → mobile)
- Small, focused models outperforming large general ones on specific tasks

### Relevance to Hermes/SOMA:
- ShowUI's token selection approach could inspire efficiency improvements in browser_vision/screen-vision tools
- The interleaved VLA streaming pattern is relevant to how Hermes processes browser snapshots + actions
- SpiritSight's "one look" grounding relates to single-screenshot navigation patterns


## Sources

- https://arxiv.org/abs/2411.17465
- https://github.com/showlab/ShowUI
- https://voxel51.com/blog/visual-agents-at-cvpr-2025
