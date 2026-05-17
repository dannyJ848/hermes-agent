# real-time-sss-techniques-2025

*Researched: 2026-04-06 14:05 CDT*

# Real-Time Subsurface Scattering: 2025 State of the Art

## SIGGRAPH 2025 Advances Course
- Dedicated course on real-time SSS at SIGGRAPH 2025 Advances in Real-Time Rendering
- Hybrid ReSTIR Path Tracing + Diffusion approach for real-time SSS
- Key paper: "RT Subsurface Scattering via Hybrid ReSTIR-Path Tracing & Diffusion" (SIGGRAPH 2025)
- PDF: https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf

## NVIDIA RTX Skin (GDC 2025)
- RTX Remix introduces "RTX Skin" — first SSS implementation in ray-traced gaming
- Part of NVIDIA RTX Kit neural rendering suite
- Neural Shaders coming to DirectX 12 via Agility SDK Preview (April 2025)
- Cooperative Vectors in HLSL enable tensor core access from shaders
- Key implication: neural-network-based SSS approximation possible in real-time shaders

## Classical SSS Reference Pipeline (for WebGPU adaptation)
1. **Separable SSS** (Jimenez et al.) — Screen-space blur in 2 passes. Most practical for WebGPU.
2. **Approximating Translucency** (Barre-Brisebois, GDC 2011) — Cheap wrap lighting + thickness map
3. **GPU Gems Ch.16** — Real-time approximations using depth maps and wrapped diffuse
4. **BSSRDF** (PBRT) — Ground truth reference, too expensive for real-time

## SOMA Integration Path
For SOMA's anatomy viewer, the most practical approach remains:
1. Screen-space separable SSS blur (2-pass Gaussian with skin diffusion profiles)
2. Thickness map from depth buffer (cheap translucency)
3. Pre-integrated skin shading (Penner-Borshukov)
4. Future: WebGPU compute shaders could implement neural SSS once tensor cores are accessible via WebGPU

## Sources
- SIGGRAPH 2025 Advances: https://advances.realtimerendering.com/s2025/
- NVIDIA RTX Blog: https://developer.nvidia.com/blog/nvidia-rtx-advances-with-neural-rendering-and-digital-human-technologies-at-gdc-2025/
- Separable SSS Paper: https://www.iryoku.com/separable-sss/downloads/Separable-Subsurface-Scattering.pdf
- Vulkan SSS Demos: https://github.com/Jaysmito101/AdvancedVulkanDemos/blob/main/resources/subsurface_scattering.md

## Sources

- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- https://developer.nvidia.com/blog/nvidia-rtx-advances-with-neural-rendering-and-digital-human-technologies-at-gdc-2025/
- https://github.com/Jaysmito101/AdvancedVulkanDemos/blob/main/resources/subsurface_scattering.md
