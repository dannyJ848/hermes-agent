# visual-agents-cvpr-2025

*Researched: 2026-04-07 10:23 CDT*

# Visual Agents at CVPR 2025 — Key Papers & Techniques

## Summary
CVPR 2025 featured a major wave of Visual Agent papers moving from perception to interaction. Key systems:

### ShowUI — Vision-Language-Action for GUI
- Advanced VLA model for GUI interactions
- Handles screen understanding + action generation end-to-end

### GUI-Xplore — Generalizable GUI Agents
- One-exploration approach to generalize across GUI environments
- Reduces per-app training data needs

### SpiritSight Agent — One-Look GUI Agent
- Processes entire screen in one forward pass
- Strong visual grounding for element detection

### ComfyBench — LLM Agents in Visual Workflows
- Benchmarks LLM-based agents in ComfyUI
- Tests autonomous design of collaborative AI systems

### Key Takeaway for SOMA
The field is converging on **Vision-Language-Action (VLA)** models that perceive screens and generate actions directly. For SOMA's 3D anatomy viewer, this means:
1. Three.js element picking + visual feedback is the right architecture
2. Visual grounding (mapping language to screen coordinates) is the core unsolved problem
3. Error recovery from visual feedback is a gap opportunity

### Universal Visual Grounding (ICLR 2026)
- Human-like embodiment for GUI agents
- Perceive environment entirely visually
- Direct pixel-level operations (no DOM dependency)

## Sources
- Voxel51 blog: https://voxel51.com/blog/visual-agents-at-cvpr-2025
- ICLR 2026 poster: https://iclr.cc/virtual/2025/poster/32062
- arXiv GUI Grounding: https://arxiv.org/abs/2603.26211


## Sources

- https://voxel51.com/blog/visual-agents-at-cvpr-2025
- https://iclr.cc/virtual/2025/poster/32062
- https://arxiv.org/abs/2603.26211
