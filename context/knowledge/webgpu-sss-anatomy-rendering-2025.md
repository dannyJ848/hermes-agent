# webgpu-sss-anatomy-rendering-2025

*Researched: 2026-04-06 01:07 CDT*

# WebGPU Subsurface Scattering for 3D Anatomy Rendering (2025)

## SIGGRAPH 2025 Advances in Real-Time SSS
- **Paper**: `advances.realtimerendering.com/s2025/sss-siggraph-2025-advances-published.pdf`
- Hybrid ReSTIR-Path Tracing + Diffusion for real-time SSS
- Key insight: SSS is volume scattering after surface transmission with multiple internal bounces
- Relevant for SOMA: realistic skin/organ translucency in real-time WebGPU

## SSS Reference Library (Jaysmito101/AdvancedVulkanDemos)
Comprehensive list of SSS techniques ranked by complexity:

### Fast/Cheap (SOMA Tier 1 — Mobile-ready):
- **Approximating Translucency** (GDC 2011, Colin Barre-Brisebois): Fast, cheap, convincing SSS look. Best starting point for mobile.
- **GPU Gems Ch.16**: Real-time approximations — wrap lighting + texture-based approaches

### Medium (SOMA Tier 2 — Desktop):
- **Separable SSS** (Jimenez et al., iryoku.com): 2-pass separable blur, industry standard for games. Ported to WebGPU should be feasible.
- **MJP's Intro to SSS** (therealmjp.github.io): Practical implementation guide

### Advanced (SOMA Tier 3 — Future):
- **Disney BSDF with Integrated SSS** (Burley 2015): Physically-based, used in film
- **Quantized-Diffusion Model** (d'Eon): Accurate but computationally heavy
- **BSSRDF Importance Sampling** (Sony Pictures): Path-traced approach

## WebGPU Ecosystem (Feb 2025 Highlights)
- **Three.js WebGPU Renderer**: Production-ready — Utsubo using it for Expo 2025 interactive installations
- **MLS-MPM Fluid Simulations**: Real-time on consumer hardware via WebGPU compute shaders
- **Kokoro TTS**: WebGPU-accelerated browser-native TTS (relevant for SOMA bilingual audio)
- **SmolVLM**: Efficient AI model running in-browser via WebGPU

## SOMA Integration Recommendations
1. **Immediate**: Implement wrap lighting SSS approximation (Tier 1) — 10 lines of WGSL shader code
2. **Phase 2**: Separable SSS blur — 2-pass approach, needs compute shader support
3. **Phase 3**: Disney BSDF when WebGPU ray-tracing extensions land
4. **Audio**: Investigate Kokoro TTS for SOMA's EN/ES bilingual voice annotations
5. **Three.js WebGPU**: Migration path validated by Utsubo's Expo 2025 work

## Sources
- SIGGRAPH 2025 Real-Time Rendering Course
- Jaysmito101/AdvancedVulkanDemos SSS references
- WebGPU Experts Feb 2025 roundup


## Sources

- https://advances.realtimerendering.com/s2025/sss-siggraph-2025-advances-published.pdf
- https://github.com/Jaysmito101/AdvancedVulkanDemos/blob/main/resources/subsurface_scattering.md
- https://www.webgpuexperts.com/best-webgpu-updates-february-2025
