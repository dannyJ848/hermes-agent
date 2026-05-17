# real-time-sss-techniques-anatomy-2025

*Researched: 2026-04-06 02:26 CDT*

# Real-Time Subsurface Scattering for Anatomy Rendering (2025)

## Key Finding
SIGGRAPH 2025 published a major SSS course ("Real-Time Subsurface Scattering") at advances.realtimerendering.com/s2025/. A novel hybrid solution using **ReSTIR Path Tracing + Diffusion** was presented, combining Monte Carlo sampling with analytic diffusion profiles for real-time SSS.

## Core SSS Approaches for Web/Anatomy

### 1. Separable Subsurface Scattering (Jimenez et al.)
- Screen-space technique, 2-pass separable blur
- Can be implemented in WebGPU fragment shaders
- Reference: iryoku.com/separable-sss
- **SOMA applicability**: HIGH — runs well on mobile, minimal geometry dependency

### 2. Burley's Normalized Diffusion (Disney BSDF)
- Replaces multi-Gaussian profiles with single analytic formula
- More physically accurate, fewer texture lookups
- Reference: blog.selfshadow.com (Disney BSDF slides)
- **SOMA applicability**: HIGH — fewer taps = better mobile performance

### 3. Screen-Space SSS (2018 SIGGRAPH Advances)
- Efficient screen-space implementation using Burley's model
- 12-tap blur approximation proven effective (Hable, Uncharted 2)
- Reference: advances.realtimerendering.com/s2018
- **SOMA applicability**: HIGHEST — best performance/quality for Three.js WebGPU

### 4. RT Hybrid: ReSTIR-Path Tracing + Diffusion (SIGGRAPH 2025 NEW)
- Novel hybrid combining Monte Carlo sampling with diffusion approximation
- Best quality but requires ray tracing hardware
- **SOMA applicability**: LOW — not available on mobile WebGPU yet

## Curated Reference Library (from Jaysmito101/AdvancedVulkanDemos)
- GPU Gems Ch.16: Real-Time Approximations to SSS (nvidia.com)
- GPU Gems 3 Ch.14: Advanced Skin Rendering (nvidia.com)
- MJP's SSS Introduction: therealmjp.github.io/posts/sss-intro/
- Quantized Diffusion Model: eugenedeon.com/pdfs/qd.pdf
- Real-Time Skin Translucency: iryoku.com/translucency

## WebGPU Ecosystem (Feb 2025)
- Three.js now has native WebGPU renderer with compute shader support
- MLS-MPM fluid simulations running smoothly on older devices via WebGPU
- Key insight: Three.js WebGPU path now production-ready for SSS compute workloads

## SOMA Implementation Priority
1. **Phase 1**: Burley Normalized Diffusion in screen-space (12-tap blur) — immediate mobile viability
2. **Phase 2**: Separable SSS with tissue-specific scattering parameters — enhanced realism
3. **Phase 3**: Compute-shader SSS via Three.js WebGPU renderer — next-gen quality

## Tissue Scattering Parameters Needed
- Skin: σ_s ≈ 0.5-2.0mm, high forward scattering
- Muscle: σ_s ≈ 3-8mm, red-shifted absorption
- Fat: σ_s ≈ 10-20mm, diffuse scattering, yellow tint
- Bone: minimal scattering, high absorption, white/cream appearance


## Sources

- https://advances.realtimerendering.com/s2025/
- https://github.com/Jaysmito101/AdvancedVulkanDemos/blob/main/resources/subsurface_scattering.md
- https://www.webgpuexperts.com/best-webgpu-updates-february-2025
- https://www.reddit.com/r/GraphicsProgramming/comments/1lfku5c/playing_around_with_realtime_subsurface/
