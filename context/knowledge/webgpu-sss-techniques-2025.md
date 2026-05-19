# webgpu-sss-techniques-2025

*Researched: 2026-04-06 04:31 CDT*

# Real-Time Subsurface Scattering — 2025 State of the Art

## SIGGRAPH 2025 Advances Course (Key Paper)
- **URL:** https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- Dedicated SSS session at SIGGRAPH 2025 Advances in Real-Time Rendering course
- Hybrid ReSTIR Path Tracing + Diffusion approach for real-time SSS
- Claims significantly more skin detail with closer ground truth matching
- YouTube talk: https://www.youtube.com/watch?v=AtFBbMnUgoc

## NVIDIA RTX Skin (GDC 2025)
- One of first implementations of SSS in ray-traced gaming (via RTX Remix)
- Part of NVIDIA RTX Kit suite of neural rendering technologies
- RTX Neural Shaders: small neural networks in programmable shaders for texture/material/lighting improvement
- DirectX 12 Cooperative Vectors (Agility SDK April 2025) enables Tensor Core access from within shaders
- RTX Mega Geometry for path-tracing massive dense geometry (available in UE5 NvRTX branch)
- Zorah demo showcases: ReSTIR PT, ReSTIR DI, RTX Mega Geometry

## Practical Implementation Reference
- Jaysmito101 AdvancedVulkanDemos has open-source SSS implementation:
  https://github.com/Jaysmito101/AdvancedVulkanDemos/blob/main/resources/subsurface_scattering.md

## SOMA Application Notes
For SOMA's 3D anatomy viewer, the most practical approach remains:
1. **Screen-space SSS** (existing soma-sss-shaders skill) for mobile/WebGPU
2. **Pre-integrated skin shading** (Jimenez/Segovia method) for lightweight approx
3. For desktop: consider ReSTIR-based hybrid if WebGPU compute shaders available
4. The NVIDIA neural shader approach is DirectX-only — not applicable to WebGPU yet
5. The SIGGRAPH 2025 paper's diffusion-based approach could inform better approximations


## Sources

- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- https://developer.nvidia.com/blog/nvidia-rtx-advances-with-neural-rendering-and-digital-human-technologies-at-gdc-2025/
- https://github.com/Jaysmito101/AdvancedVulkanDemos/blob/main/resources/subsurface_scattering.md
