# gui-grounding-diffusion-vlms-cvpr2025

*Researched: 2026-04-05 02:40 CDT*

# GUI Grounding with Vision-Language Diffusion Models (CVPR 2025 / arXiv Mar 2026)

## Paper: "Towards GUI Agents: Vision-Language Diffusion Models for GUI Grounding"
- **Authors:** Shrinidhi Kumbhar (ASU), Haofu Liao, Srikar Appalaraju, Kunwar Yashraj Singh (AWS Agentic AI)
- **arXiv:** 2603.26211v1 (March 27, 2026)
- **Key insight:** Discrete diffusion VLMs (DVLMs) can match autoregressive VLMs for GUI grounding — a previously unexplored application.

## Technical Approach
- Adapts **LLaDA-V** (discrete diffusion VLM) for single-turn action + bounding-box prediction
- Frames GUI grounding as text generation from multimodal input (screenshot + instruction → coordinates)
- **Hybrid masking schedule** combines linear masking (for coarse grounding) + full deterministic masking (for bounding-box extent)
  - Linear masking phase: randomly masks action/anchor tokens during training
  - Deterministic masking phase: all response tokens fully masked; model predicts bbox extent during denoising

## Results
- Hybrid masking improves grounding accuracy by up to **6.1 points SSR** (Step Success Rate)
- Evaluated on 4 datasets spanning web, desktop, and mobile interfaces
- Expanding training data with diverse GUI domains: **+20 points** average accuracy improvement, **-1.3s latency reduction**
- Performs competitively with autoregressive counterparts despite limited pretraining
- Trade-off: more diffusion steps = better accuracy but higher latency; plateaus beyond a threshold

## Why This Matters for Agents
1. **Bidirectional attention** in diffusion models captures global GUI context better than left-to-right autoregressive
2. **Parallel token generation** enables potentially faster inference for coordinate prediction
3. **Iterative refinement** is natural to diffusion — can progressively refine grounding predictions
4. This is the first work showing DVLMs as viable for GUI grounding — opens a new modeling paradigm

## CVPR 2025 Visual Agents Landscape (from Voxel51 roundup)
Key papers in the visual agent space at CVPR 2025:
- **ShowUI:** Vision-Language-Action model for GUI interactions (2B params)
- **GUI-Xplore:** Generalizable GUI agents with exploration-based training
- **SpiritSight Agent:** "One Look" GUI agent — single-pass grounding
- **ComfyBench:** Benchmarking LLM agents in ComfyUI for collaborative AI systems
- **Generalist Embodied Agents survey:** Methods and lessons from multimodal LLMs

The field is moving from perception-only to **perception+interaction** — agents that can see AND act on visual interfaces.

## Implications for SOMA/Hermes
- Diffusion-based grounding could improve browser automation accuracy (browser_vision tool)
- Hybrid masking's coarse→fine approach mirrors how human agents scan screens
- The bidirectional attention advantage is relevant for understanding complex medical UIs in SOMA


## Sources

- https://arxiv.org/html/2603.26211v1
- https://voxel51.com/blog/visual-agents-at-cvpr-2025
