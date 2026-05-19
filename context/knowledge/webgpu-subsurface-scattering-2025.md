# webgpu-subsurface-scattering-2025

*Researched: 2026-04-06 03:47 CDT*

# Real-Time Subsurface Scattering Advances (SIGGRAPH 2025 / GDC 2025)

## Key Developments

### SIGGRAPH 2025 Advances Course — SSS Session
- Dedicated session on **real-time subsurface scattering** at SIGGRAPH 2025 Advances in Real-Time Rendering course
- Hybrid approach: **ReSTIR Path Tracing + Diffusion** for RT subsurface scattering
- Claims significantly better skin detail with closer ground truth matching than prior methods
- Paper: `advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf`

### NVIDIA RTX Skin (GDC 2025)
- One of the first implementations of **subsurface scattering in ray-traced gaming** (RTX Remix)
- Light transmits and scatters through skin realistically using RT cores
- Part of NVIDIA RTX Kit suite of neural rendering technologies

### Neural Shading for SSS
- DirectX 12 Agility SDK (April 2025) adds **Cooperative Vectors** — Tensor Core access from HLSL shaders
- Enables neural networks inside shaders for material/lighting approximation
- Could dramatically simplify SSS implementation by replacing analytical diffusion profiles with learned neural approximations

### RTX Texture Streaming
- Tiles textures for on-demand loading, reducing memory overhead
- Complements neural texture compression — only decompresses accessed portions
- Relevant for SOMA: medical texture streaming on mobile could use similar tiling

## Relevance to SOMA
1. **Neural SSS shaders**: When WebGPU gets cooperative vector support, we could replace our screen-space SSS with a small neural network for better accuracy at lower cost
2. **ReSTIR hybrid**: The path-tracing + diffusion hybrid is the state of the art. For pre-computed lightmaps on anatomy models, diffusion-based SSS would be more accurate than our current Gaussian approximation
3. **Texture tiling**: RTX Texture Streaming's tile-based approach maps directly to medical texture streaming on mobile WebGPU

## Sources
- SIGGRAPH 2025 Advances course: https://advances.realtimerendering.com/s2025/
- NVIDIA GDC 2025 blog: https://developer.nvidia.com/blog/nvidia-rtx-advances-with-neural-rendering-and-digital-human-technologies-at-gdc-2025/
- Reddit r/GraphicsProgramming: https://www.reddit.com/r/GraphicsProgramming/comments/1lfku5c/


## Sources

- https://advances.realtimerendering.com/s2025/
- https://developer.nvidia.com/blog/nvidia-rtx-advances-with-neural-rendering-and-digital-human-technologies-at-gdc-2025/
