# siggraph-2025-real-time-sss-techniques

*Researched: 2026-04-05 20:08 CDT*

# SIGGRAPH 2025: Real-Time Subsurface Scattering Advances

## Key Discovery: Hybrid ReSTIR-Path Tracing + Diffusion for SSS

SIGGRAPH 2025 "Advances in Real-Time Rendering" course features a major new approach to real-time subsurface scattering:

### Core Technique
- **Hybrid ReSTIR-Path Tracing & Diffusion**: Combines traditional diffusion approximations with modern ReSTIR (Reservoir-based Spatiotemporal Importance Resampling) path tracing
- Traditional real-time SSS relies on diffusion approximations (screen-space blur techniques)
- New hybrid method delivers high-quality SSS "fast enough for current generation pipelines"
- Published as part of SIGGRAPH 2025 Advances course

### Reference Pipeline (from Jaysmito101/AdvancedVulkanDemos)
Practical SSS implementation references:
1. **Separable Subsurface Scattering** (Jimenez et al., iryoku.com) — the classic real-time technique
2. **Approximating Translucency** (GDC 2011, Colin Barre-Brisebois) — fast, cheap convincing SSS look
3. **GPU Gems Ch.16** — Real-time approximations to subsurface scattering (NVIDIA)
4. **PBRT BSSRDF** — physically-based reference implementation
5. **Rendering Translucent Materials** (Stanford, Henrik Jensen) — foundational theory

### Relevance to SOMA
SOMA's 3D anatomy viewer needs realistic tissue rendering. Skin, organs, and other biological tissues all exhibit subsurface scattering. Current approach uses native GLSL SSS shaders (see soma-sss-shaders skill). 

**Action items for SOMA:**
1. Evaluate if ReSTIR hybrid approach can be adapted to WebGL/WebGPU (currently game-engine focused)
2. The Separable SSS technique remains the most practical for web-based rendering
3. Watch for WebGPU compute shader implementations of ReSTIR — would enable higher quality
4. Three.js now has WebGPU renderer support (confirmed Feb 2025), opening path to compute-based SSS

### WebGPU Ecosystem Status (Feb 2025)
- Three.js WebGPU renderer now production-ready
- MLS-MPM fluid simulations running smoothly on consumer hardware via WebGPU
- WebGPU enabling compute-heavy simulations (MPM, SPH) entirely in-browser
- AI models (TTS, multimodal) running on WebGPU — proves compute shader maturity

## Sources
- SIGGRAPH 2025 Advances course: https://advances.realtimerendering.com/s2025/
- ReSTIR SSS paper: https://dl.acm.org/doi/abs/10.1145/3675372
- SSS reference collection: https://github.com/Jaysmito101/AdvancedVulkanDemos/blob/main/resources/subsurface_scattering.md
- WebGPU ecosystem: https://www.webgpuexperts.com/best-webgpu-updates-february-2025


## Sources

- https://advances.realtimerendering.com/s2025/
- https://dl.acm.org/doi/abs/10.1145/3675372
- https://github.com/Jaysmito101/AdvancedVulkanDemos/blob/main/resources/subsurface_scattering.md
- https://www.webgpuexperts.com/best-webgpu-updates-february-2025
