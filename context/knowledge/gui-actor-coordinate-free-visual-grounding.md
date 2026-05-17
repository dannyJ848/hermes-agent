# GUI-Actor coordinate-free visual grounding

*Researched: 2026-04-05 03:37 CDT*

# GUI-Actor: Coordinate-Free Visual Grounding for GUI Agents

**Source:** Microsoft Research (NeurIPS 2025)
**Authors:** Qianhui Wu, Kanzhi Cheng, Rui Yang, et al.
**URL:** https://arxiv.org/abs/2506.03143 | https://github.com/microsoft/GUI-Actor

## Key Innovation
GUI-Actor replaces text-based coordinate generation with an **attention-based action head** that aligns a dedicated `<ACTOR>` token with relevant visual patch tokens. This is "coordinate-free" grounding — the model proposes action regions via attention, not by predicting x,y numbers.

## Architecture
1. **`<ACTOR>` token** — a contextual anchor injected into the VLM's token sequence
2. **Attention-based action head** — learns to align the ACTOR token with all relevant visual patch tokens, proposing one or more action regions in a single forward pass
3. **Grounding verifier** — evaluates and selects the most plausible action region from candidates
4. **Spatial-aware multi-patch supervision** — handles ambiguous supervision targets (single-point predictions penalize valid variations)

## Results
- **GUI-Actor-7B** achieves 40.7 (Qwen2-VL) and **44.6** (Qwen2.5-VL) on ScreenSpot-Pro
- **Outperforms UI-TARS-72B (38.1)** with 10x fewer parameters
- Only ~100M new parameters added to the VLM backbone
- **Freezing the VLM backbone and fine-tuning only the action head** achieves comparable SOTA — preserves general-purpose VLM capabilities
- Robust out-of-distribution generalization to unseen screen resolutions and layouts

## Why It Matters for SOMA / Agent Systems
1. **Coordinate-free** avoids the spatial-semantic misalignment problem of predicting raw coordinates from ViT patch features
2. **Multi-region prediction** in a single forward pass — no need for multi-step refinement
3. **Verifier** adds a confidence signal that could gate agent actions (only act when confident)
4. **Training efficiency** — fine-tuning only ~100M params on top of frozen VLM is practical for custom domains (could adapt for medical UI grounding)
5. Directly applicable to building agents that navigate medical software interfaces

## Comparison to SoM
Set-of-Mark (SoM) from 2023 overlays numbered marks on image regions and asks the LLM to pick one. GUI-Actor instead learns visual grounding end-to-end via attention — no markup overlay needed. GUI-Actor is more robust to resolution/layout changes because it doesn't depend on an external segmentation/marking step.

## Follow-up Questions
- Can the action head + verifier pattern be applied to 3D scene grounding (SOMA)?
- How does the multi-patch supervision handle overlapping UI elements?
- Is the 100M param action head portable across different VLM backbones?


## Sources

- https://arxiv.org/abs/2506.03143
- https://github.com/microsoft/GUI-Actor
- https://microsoft.github.io/GUI-Actor/
