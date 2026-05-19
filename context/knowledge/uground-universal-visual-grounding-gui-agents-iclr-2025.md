# uground-universal-visual-grounding-gui-agents-iclr-2025

*Researched: 2026-04-05 03:10 CDT*

# UGround: Universal Visual Grounding for GUI Agents (ICLR 2025)

**Paper:** arXiv:2410.05243 (accepted ICLR 2025)
**Authors:** Boyu Gou et al. (Ohio State University + Orby AI)
**Code:** https://osu-nlp-group.github.io/UGround/

## Core Idea
Human-like embodiment for GUI agents — perceive environment **entirely visually** and perform **pixel-level operations** on GUIs. No HTML, no accessibility trees, no text-based input. Pure visual perception.

## Key Innovation
- UGround maps referring expressions of GUI elements to their **pixel coordinates** on screen
- Simple recipe: web-based synthetic data + slight LLaVA architecture adaptation
- Largest GUI visual grounding dataset: **10M GUI elements** with referring expressions over **1.3M screenshots**

## Results
- **+20% absolute improvement** over existing visual grounding models
- Agents with UGround **outperform SOTA agents** despite those agents using additional text-based input
- Evaluated on 6 benchmarks across 3 categories: grounding, offline agent, online agent
- Works across platforms: web, mobile (Android), desktop

## Why This Matters
1. **Pure visual perception** eliminates dependency on HTML/accessibility trees (which are noisy, incomplete, and computationally expensive)
2. **Pixel-level grounding** is more robust than element-id based approaches
3. **Cross-platform** — same model works on web, Android, desktop
4. **Simplicity** — just LLaVA + synthetic data, no complex architecture changes
5. **Proof that visual-only agents can match or beat text+visual agents**

## Related: Self-Evolutionary Grounding (NeurIPS 2025)
- NeurIPS 2025 poster on self-evolutionary approach to enhancing visual grounding for GUI agents
- Builds on similar premise of improving grounding without text-based aids

## Related: Aria-UI (ACL 2025)
- Visual grounding for GUI instructions
- Addresses challenge of grounding from language instructions to target elements without relying on HTML/AXTree

## Relevance to SOMA/Agents
- UGround approach could replace a11y-tree dependencies in Hermes browser tools
- Pixel-level grounding more robust for complex medical UI navigation
- Training approach (synthetic data + LLaVA) is reproducible for custom domains
- Dataset scale (10M elements / 1.3M screenshots) sets new standard for GUI grounding


## Sources

- https://arxiv.org/html/2410.05243v3
- https://openreview.net/forum?id=kxnoqaisCT
- https://neurips.cc/virtual/2025/poster/118788
