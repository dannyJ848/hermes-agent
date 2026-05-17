# realtime-sss-techniques-webgpu-2025

*Researched: 2026-04-05 20:36 CDT*

# Real-Time Subsurface Scattering for 3D Anatomy Rendering (2025 Survey)

## Key Discovery: SIGGRAPH 2025 SSS Course
- **Source**: "Real-Time Subsurface Scattering" — SIGGRAPH 2025 Advances in Real-Time Rendering course
- **PDF**: https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- **Video**: https://www.youtube.com/watch?v=RSnZU96dV0Y
- Covers volume scattering after surface transmission with multiple internal bounces

## Hybrid RESTIR-Path Tracing + Diffusion
- **Video**: https://www.youtube.com/watch?v=AtFBbMnUgoc
- Novel hybrid solution for real-time SSS combining ReSTIR path tracing with diffusion approximation
- Relevant to SOMA: could produce realistic tissue translucency in WebGPU

## Comprehensive SSS Reference Library (Jaysmito101/AdvancedVulkanDemos)
Key papers for implementation:
1. **Separable SSS** (Jimenez et al.): https://www.iryoku.com/separable-sss/downloads/Separable-Subsurface-Scattering.pdf — The gold standard for real-time screen-space SSS. Best starting point for SOMA.
2. **Fast Translucency Approximation** (GDC 2011): Cheap convincing SSS look — ideal for mobile/WebGPU
3. **GPU Gems Ch.16**: Real-time approximations — wrapping/lighting-based approaches
4. **GPU Gems 3 Ch.14**: Advanced skin rendering — multi-layer skin model with textures
5. **Disney BSDF with Integrated SSS** (Burley 2015): Physically-based, extensible to tissue types
6. **MJP's SSS Introduction**: https://therealmjp.github.io/posts/sss-intro/ — Practical implementation guide
7. **Quantized-Diffusion Model**: More accurate than dipole, still real-time capable

## WebGPU Ecosystem (Feb 2025)
- Three.js now has WebGPU renderer with significantly improved performance
- MLS-MPM fluid simulations running smoothly on consumer hardware via WebGPU
- AI models (TTS, VLM) running entirely in-browser via WebGPU compute shaders
- Expo 2025 showcase using Three.js WebGPU renderer for large-scale interactive installations

## SOMA Application Strategy
1. **Phase 1**: Implement Separable SSS (screen-space blur) — cheapest, good visual results
2. **Phase 2**: Add fast translucency approximation for thin tissues (ears, fingers)
3. **Phase 3**: Explore Disney BSDF with BSSRDF for organ-level accuracy
4. **WebGPU Path**: Three.js WebGPU renderer now mature enough for production use
5. **Mobile concern**: Screen-space SSS blur passes may need resolution scaling on iOS

## Tags
#3d_rendering #subsurface_scattering #webgpu #anatomy #soma #siggraph2025

## Sources

- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- https://github.com/Jaysmito101/AdvancedVulkanDemos/blob/main/resources/subsurface_scattering.md
- https://www.webgpuexperts.com/best-webgpu-updates-february-2025
- https://www.youtube.com/watch?v=AtFBbMnUgoc
