# real-time-sss-webgpu-2025

*Researched: 2026-04-05 16:49 CDT*

# Real-Time Subsurface Scattering for WebGPU — 2025 State of the Art

## Key Findings (SIGGRAPH 2025 + WebGPU Ecosystem)

### SIGGRAPH 2025 Advances Course: Real-Time Subsurface Scattering
- **Source**: SIGGRAPH 2025 "Advances in Real-Time Rendering in Games" course
- **URL**: https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- **Key technique**: Hybrid ReSTIR-Path Tracing & Diffusion for real-time SSS
- **Novel approach**: Combines ReSTIR path sampling with diffusion approximation for real-time translucency
- **Video**: https://www.youtube.com/watch?v=AtFBbMnUgoc

### WebGPU Real-Time Capabilities (Feb 2025)
- Three.js now has a **WebGPU renderer** — enabling high-performance SSS and fluid simulations
- MLS-MPM (Moving Least Squares Material Point Method) running in-browser on consumer hardware
- Expo 2025: Utsubo built large-scale interactive fluid simulation using Three.js WebGPU renderer
- Shallow Water Physics via virtual pipes method running entirely in-browser
- AI models (Kokoro TTS, Janus Pro, SmolVLM) running via WebGPU compute shaders

### SSS Reference Library (for SOMA implementation)
Best resources for implementing real-time SSS in WebGL/WebGPU:

1. **Separable Subsurface Scattering** (Jimenez et al.) — The practical approach for real-time: https://www.iryoku.com/separable-sss/downloads/Separable-Subsurface-Scattering.pdf
2. **Approximating Translucency** (Barre-Brisebois, GDC 2011) — Cheap, convincing SSS look
3. **GPU Gems Ch.16** — Real-time approximations to SSS: https://developer.nvidia.com/gpugems/gpugems/part-iii-materials/chapter-16-real-time-approximations-subsurface-scattering
4. **GPU Gems 3 Ch.14** — Advanced skin rendering techniques: https://developer.nvidia.com/gpugems/gpugems3/part-iii-rendering/chapter-14-advanced-techniques-realistic-real-time-skin
5. **MJP's SSS Introduction** — Practical intro: https://therealmjp.github.io/posts/sss-intro/
6. **Disney BSDF with SSS** (Burley 2015) — Physically-based approach: https://blog.selfshadow.com/publications/s2015-shading-course/burley/s2015_pbs_disney_bsdf_slides.pdf
7. **Quantized Diffusion Model** — Accurate translucent material rendering
8. **BSSRDF in PBRT** — Theory reference: https://pbr-book.org/3ed-2018/Volume_Scattering/The_BSSRDF

### Relevance to SOMA
- **Separable SSS** is the most practical approach for SOMA's WebGL renderer (can fallback from WebGPU)
- **Three.js WebGPU renderer** maturity means SOMA could target WebGPU for better SSS quality
- The cheap translucency approximation (GDC 2011) is ideal for mobile — maintains 60fps while adding convincing tissue translucency
- For the 3D anatomy viewer, skin/tissue SSS would dramatically improve realism of:
  - Skin layers (epidermis, dermis visualization)
  - Muscle tissue translucency
  - Organ surface rendering (liver, kidney, heart)
  - Blood vessel visibility beneath tissue

### Implementation Priority for SOMA
1. Start with **cheap translucency approximation** (wrap lighting + thickness map) — works in WebGL
2. Graduate to **separable SSS** with blur kernels — requires render-to-texture support
3. Consider **WebGPU path** for advanced diffusion when browser support is >90%


## Sources

- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- https://www.webgpuexperts.com/best-webgpu-updates-february-2025
- https://github.com/Jaysmito101/AdvancedVulkanDemos/blob/main/resources/subsurface_scattering.md
- https://www.iryoku.com/separable-sss/downloads/Separable-Subsurface-Scattering.pdf
