# ScreenSpot-Pro GUI Grounding Benchmark

*Researched: 2026-04-05 03:25 CDT*

# ScreenSpot-Pro: GUI Grounding for Professional High-Resolution Computer Use

**Published:** January 2025 (ACM DL, arXiv 2504.07981)
**Authors:** Kaixin Li, Ziyang Luo et al. (National University of Singapore)

## Summary
ScreenSpot-Pro is a benchmark evaluating GUI grounding models in professional, high-resolution environments. It contains **1,581 instructions** paired with high-res screenshots across **23 professional applications** in 5 industry categories and 3 operating systems.

## Key Findings
- **Best model (OS-Atlas-7B) achieves only 18.9% accuracy** — professional GUI grounding is still extremely hard
- **GPT-4o scores just 0.8%** — general-purpose VLMs fail badly on professional software
- **ReGround method (visual search + cropping) improves to 40.2%** — still far from production-ready
- Resolution trade-offs: downsampling helps but loses small-target precision

## Application Categories
- **Dev Tools:** VSCode, PyCharm, Android Studio, VMware
- **Creative:** Photoshop, Premiere, Illustrator, Blender, DaVinci Resolve
- **CAD/Engineering:** AutoCAD, SolidWorks, Inventor, Vivado, Quartus
- **Scientific:** MATLAB, Stata, EViews
- **Office:** Word, Excel, PowerPoint

## Why It Matters for Agent Development
- Professional software (CAD, IDEs, creative suites) is where current GUI agents fail hardest
- High-resolution screens (4K+) create tiny target elements that models can't localize
- Expert-annotated data (5+ years professional experience per annotator) ensures quality
- Highlights need for resolution-aware grounding: multi-scale cropping, zoom-in strategies

## Relevance to SOMA/Hermes
- Any medical imaging UI or professional tool interaction would face the same challenges
- Visual search methods (ReGround pattern) could improve Hermes browser automation accuracy
- Future work: train resolution-aware grounding models for medical software interfaces

## Sources

- https://huggingface.co/blog/Ziyang/screenspot-pro
- https://arxiv.org/html/2504.07981v1
- https://dl.acm.org/doi/10.1145/3746027.3755688
