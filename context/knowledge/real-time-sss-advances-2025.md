# real-time-sss-advances-2025

*Researched: 2026-04-05 21:28 CDT*

# Real-Time Subsurface Scattering: 2025 State of the Art

## SIGGRAPH 2025 — Major SSS Course Published
- **"Real-Time Subsurface Scattering"** — SIGGRAPH 2025 Advances in Real-Time Rendering course
- Source: `advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf`
- Introduces **hybrid ReSTIR-Path Tracing + Diffusion** approach for real-time SSS
- Claims significantly more detail capture with much closer ground truth matching vs prior methods
- Companion video: youtube.com/watch?v=AtFBbMnUgoc

## NVIDIA RTX Skin (GDC 2025)
- One of the first implementations of SSS in **ray-traced gaming** (via RTX Remix)
- Light can now transmit and scatter through skin geometry in real-time
- Part of NVIDIA's broader neural rendering push (RTX Neural Shaders, DLSS 4)
- Neural shading support coming to DirectX 12 via Agility SDK Preview (April 2025)
- Enables accessing RTX Tensor Cores from within shaders for neural SSS

## Key Techniques for SOMA (WebGPU/Mobile Context)
Since NVIDIA's hardware path-tracing isn't available on mobile, the practical approaches for SOMA are:

### 1. Separable SSS (Jimenez et al.)
- Classic screen-space technique, well-suited to WebGL/WebGPU
- Reference: iryoku.com/separable-sss
- Two-pass blur in screen space — O(1) per pixel regardless of scattering radius
- **Best fit for SOMA** — runs on any GPU, predictable performance

### 2. Approximating Translucency (Barre-Brisebois, GDC 2011)
- Fast, cheap, convincing SSS look without actual subsurface simulation
- Wraps lighting around surface normals
- **Good for SOMA mobile** — minimal GPU cost

### 3. Pre-Integrated Skin Shading (Penner & Borshukov)
- Pre-compute scattering lookup textures for different curvature radii
- Evaluate at runtime with just a texture lookup
- Works great for anatomy models with known mesh curvature

### 4. GPU Gems Chapter 16 Approach
- Real-time approximations using modified Fresnel and diffuse wrap
- Vertex-based thickness estimation for translucency

## Actionable for SOMA
- **Priority**: Implement Separable SSS shader in WGSL (WebGPU Shading Language)
- **Fallback**: Wrap lighting for devices without WebGPU
- **Resources**: Jaysmito101/AdvancedVulkanDemos has Vulkan SSS implementation code to port
- **Textures**: Vulpinii/skin-texture repo has skin albedo/normal maps for testing

## Sources
- SIGGRAPH 2025 Advances course: advances.realtimerendering.com/s2025
- NVIDIA GDC 2025 blog: developer.nvidia.com/blog/nvidia-rtx-advances-...
- Jaysmito101 SSS reference: github.com/Jaysmito101/AdvancedVulkanDemos/.../subsurface_scattering.md
- GPU Gems Ch.16: developer.nvidia.com/gpugems/gpugems/part-iii-materials/chapter-16


## Sources

- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- https://developer.nvidia.com/blog/nvidia-rtx-advances-with-neural-rendering-and-digital-human-technologies-at-gdc-2025/
- https://github.com/Jaysmito101/AdvancedVulkanDemos/blob/main/resources/subsurface_scattering.md
