# real-time-subsurface-scattering-webgpu-medical

*Researched: 2026-04-05 12:19 CDT*

# Real-Time Subsurface Scattering for Medical Anatomy Rendering

## Key Discovery: SIGGRAPH 2025 Advances Course
- **Source**: "Real-Time Subsurface Scattering" — SIGGRAPH 2025 Advances in Real-Time Rendering course
- **PDF**: https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- **Key insight**: SSS is volume scattering after surface transmission where light scatters multiple times internally
- **Relevance to SOMA**: Directly applicable to realistic skin/tissue rendering in 3D anatomy viewer

## Hybrid ReSTIR-Path Tracing + Diffusion Approach
- Novel hybrid solution combining ReSTIR path tracing with diffusion approximation
- Video: https://www.youtube.com/watch?v=AtFBbMnUgoc
- Enables real-time SSS without expensive full path tracing

## Reference Implementations
- **Separable SSS** (Jimenez et al.): https://www.iryoku.com/separable-sss/downloads/Separable-Subsurface-Scattering.pdf — Most practical for WebGPU implementation
- **Approximating Translucency** (GDC 2011): Fast, cheap convincing SSS look — best starting point for mobile
- **GPU Gems Ch.16**: Real-time approximations — well-documented baseline

## WebGPU Feasibility
- Motion GPU framework demonstrates fullscreen shaders + multi-pass pipelines in WebGPU
- Multi-pass pipeline is critical: SSS typically needs 2-3 blur passes (separable approach)
- WebGPU compute shaders enable diffusion-profile evaluation on GPU

## SOMA Integration Path
1. Start with **Approximating Translucency** (single pass, cheapest, mobile-friendly)
2. Upgrade to **Separable SSS** (2-pass Gaussian blur, moderate cost)
3. Consider ReSTIR hybrid only on desktop WebGPU (high-end hardware)
4. Skin texture assets: https://github.com/Vulpinii/skin-texture


## Sources

- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- https://github.com/Jaysmito101/AdvancedVulkanDemos/blob/main/resources/subsurface_scattering.md
- https://www.youtube.com/watch?v=AtFBbMnUgoc
- https://www.webgpu.com/showcase/motion-gpu-webgpu-shaders/
