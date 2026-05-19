# vision-gui-grounding-diffusion-2026

*Researched: 2026-04-07 10:26 CDT*

# GUI Grounding via Discrete Diffusion VLMs (Mar 2026)

**Paper:** "Towards GUI Agents: Vision-Language Diffusion Models for GUI Grounding" (arXiv:2603.26211)
**Authors:** Kumbhar et al., ASU + AWS Agentic AI

## Key Findings
- Discrete diffusion VLMs (DVLMs) can serve as viable alternative to autoregressive VLMs for GUI grounding
- Adapted LLaDA-V for single-turn action and bounding-box prediction
- Hybrid masking schedule (linear + deterministic) improves grounding accuracy by 6.1 SSR points
- Evaluated on web, desktop, and mobile interfaces
- Benefits: bidirectional attention, parallel token generation, iterative refinement

## SOMA Relevance
- Visual grounding directly applicable to anatomy model interaction (picking 3D elements)
- Bounding-box prediction could enable "point at anatomy" interactions
- Hybrid masking concept transferable to structured medical data prediction

## Sources

- https://arxiv.org/html/2603.26211v1
