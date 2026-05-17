# visual-grounding-agents-cvpr-2025

*Researched: 2026-04-07 03:24 CDT*

## Visual Grounding Agents (CVPR 2025 / ICLR 2025)

### Key Papers
1. **FocusUI** (NUS/Oxford, Jan 2026) — Position-Preserving Visual Token Selection for efficient UI grounding. Reduces 4700 tokens at 2K resolution by selecting instruction-relevant patches. Uses UI-Graph saliency to down-weight homogeneous regions. Base: Qwen2.5-VL/Qwen3-VL.
2. **ShowUI** (CVPR 2025) — Vision-Language-Action model for GUI interactions
3. **GUI-Xplore** (CVPR 2025) — Exploration-based cross-platform GUI agent generalization
4. **SpiritSight Agent** (CVPR 2025) — "One Look" minimal-input GUI grounding
5. **Universal Visual Grounding** (ICLR 2025) — Pure pixel-level operations, no DOM reliance

### Cross-Paper Patterns
- Token efficiency is the dominant concern (high-res screenshots = thousands of tokens)
- Position-aware token selection preserves spatial accuracy
- Pure visual pipelines replacing DOM/HTML parsing
- Instruction-conditioned saliency for selective attention
- Cross-platform generalization as key benchmark

### SOMA Applications
- FocusUI token selection → Three.js raycast optimization on anatomy regions
- Visual grounding → 3D element picking for anatomy viewer
- Position-preserving selection → LOD strategies for mobile 3D performance
- Pure visual pipelines → mobile-first architecture (no DOM for 3D scenes)

## Sources

- https://arxiv.org/html/2601.03928v1
- https://voxel51.com/blog/visual-agents-at-cvpr-2025
- https://iclr.cc/virtual/2025/poster/32062
