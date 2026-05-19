# real-time-subsurface-scattering-webgpu-2025

*Researched: 2026-04-06 19:16 CDT*

# Real-Time Subsurface Scattering for Anatomy Rendering (2025 Update)

## Key Findings

### SIGGRAPH 2025 Advances Course
- Dedicated course on "Real-Time Subsurface Scattering" at SIGGRAPH 2025 Advances
- Hybrid ReSTIR Path Tracing + Diffusion approach for real-time SSS
- Reduced reliance on precomputed separation — more dynamic approaches now viable
- Resource: https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf

### NVIDIA RTX Skin (GDC 2025)
- First implementation of SSS in ray-traced gaming via RTX Remix
- Light transmits through skin surfaces realistically
- Part of NVIDIA RTX Kit suite alongside DLSS 4, Neural Shaders
- Neural shading coming to DirectX 12 via Agility SDK Preview (April 2025)
- Cooperative Vectors in HLSL enable Tensor Core access from shaders

### Practical Implementations
- Open-source Vulkan SSS demo: github.com/Jaysmito101/AdvancedVulkanDemos
- RTX Path Tracing sample updated with full DLSS 4 + transformer model
- ReSTIR PT + ReSTIR DI for real-time path tracing with SSS

## SOMA Application
For SOMA's 3D anatomy viewer (Three.js/WebGPU):
1. **Screen-space SSS** remains most practical for mobile — SIGGRAPH 2025 diffusion approaches can be adapted
2. **Pre-integrated skin shading** (Penner-Borshukov) is still the mobile baseline; augment with texture-space blur for thicker tissues
3. Neural shader concepts (tiny networks in shaders) could eventually reach WebGPU compute shaders
4. Priority: Start with separable screen-space SSS on WebGPU compute, validate on iOS before pursuing path-traced approaches

## Sources
- SIGGRAPH 2025 Advances: advances.realtimerendering.com/s2025/
- NVIDIA GDC 2025: developer.nvidia.com/blog/nvidia-rtx-advances/
- Reddit r/GraphicsProgramming SSS thread (2025)


## Sources

- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- https://developer.nvidia.com/blog/nvidia-rtx-advances-with-neural-rendering-and-digital-human-technologies-at-gdc-2025/
- https://github.com/Jaysmito101/AdvancedVulkanDemos
