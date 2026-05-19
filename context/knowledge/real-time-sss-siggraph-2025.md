# real-time-sss-siggraph-2025

*Researched: 2026-04-06 20:34 CDT*

# Real-Time Subsurface Scattering: State of the Art (2025)

## Key Developments

### NVIDIA RTX Skin (GDC 2025)
- One of the first implementations of subsurface scattering in ray-traced gaming
- Part of RTX Remix toolkit — enables light transmission through skin surfaces
- Uses neural rendering via RTX Neural Shaders (small neural networks inside programmable shaders)
- DirectX 12 support via Agility SDK Preview (April 2025) — Cooperative Vectors for Tensor Core access from HLSL

### SIGGRAPH 2025 Advances Course
- Hybrid ReSTIR-Path Tracing + Diffusion approach for real-time SSS
- Claimed significantly closer ground truth matching with more detail capture
- Reduces reliance on precomputed diffusion profiles
- Paper: https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf

### Practical Implementations
- Open-source Vulkan SSS demo: github.com/Jaysmito101/AdvancedVulkanDemos (subsurface_scattering.md)
- Community actively experimenting with screen-space + path tracing hybrids

## Relevance to SOMA
For medical anatomy rendering, SSS is critical for realistic tissue appearance:
1. **Skin layers**: epidermis/dermis translucency makes anatomy models feel alive
2. **Organ tissue**: liver, kidney, heart all have distinctive subsurface scattering profiles
3. **Mobile challenge**: WebGPU compute shaders could implement simplified diffusion approximation
4. **Practical path**: Screen-space SSS (separable Gaussian blur) → acceptable quality on mobile, then upgrade to path-traced SSS on desktop

## Implementation Strategy
- Start with Jimenez 2015 separable SSS (screen-space, fast)
- Map tissue types to scattering parameters (mean free path, absorption coefficients)
- Use WebGPU compute shaders for the blur passes
- Reserve full path-traced SSS for desktop/high-end devices


## Sources

- https://developer.nvidia.com/blog/nvidia-rtx-advances-with-neural-rendering-and-digital-human-technologies-at-gdc-2025/
- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- https://github.com/Jaysmito101/AdvancedVulkanDemos
