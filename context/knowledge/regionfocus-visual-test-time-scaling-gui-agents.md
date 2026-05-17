# regionfocus-visual-test-time-scaling-gui-agents

*Researched: 2026-04-05 03:07 CDT*

# RegionFocus: Visual Test-Time Scaling for GUI Agent Grounding

**Paper:** arXiv:2505.00684 (2025)
**Authors:** Tiange Luo, Lajanugen Logeswaran, Justin Johnson, Honglak Lee (U. Michigan + LG AI Research)
**Code:** https://github.com/tiangeluo/RegionFocus

## Core Idea
Visual test-time scaling approach for VLM-powered GUI agents. Instead of single-pass grounding, RegionFocus dynamically **zooms into relevant screen regions** during inference, reducing background clutter and improving action grounding accuracy.

## Key Innovation: Image-as-Map
- Visualizes key landmarks at each zoom step, creating a transparent action record
- Enables the agent to effectively choose among action candidates across multiple zoom levels
- Functions as a visual "chain of thought" for grounding decisions

## Results
- **+28% on ScreenSpot-Pro** benchmark (over base models)
- **+24% on WebVoyager** benchmark
- **New SOTA: 61.6% on ScreenSpot-Pro** using Qwen2.5-VL-72B + RegionFocus
- Works on top of UI-TARS and Qwen2.5-VL backbones

## Why It Matters for SOMA/Agent Systems
1. **Iterative visual grounding** — mirrors how humans scan interfaces (look, zoom, act)
2. **Test-time scaling** — more compute = better accuracy, no retraining needed
3. **Applicable to any VLM backbone** — drop-in enhancement
4. **Image-as-Map mechanism** provides interpretability for grounding decisions

## Technical Details
- RegionFocus trigger: bounding-box proposal → action candidate prediction → action aggregation
- Simple region selection strategy already yields major gains
- Ablations show SAM-based region proposals and text-based RegionFocus variants
- Thinking budget is controllable (more zoom steps = more compute = better results)

## Related: GUI-Actor (Microsoft)
- Coordinate-free visual grounding for GUI agents using Qwen2-VL backbone
- Achieves SOTA on multiple GUI action grounding benchmarks
- Complementary approach to RegionFocus (coordinate-free vs zoom-based)


## Sources

- https://arxiv.org/html/2505.00684v1
- https://microsoft.github.io/GUI-Actor/
