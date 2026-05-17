# real-time-subsurface-scattering-webgl

*Researched: 2026-04-05 19:55 CDT*

# Real-Time Subsurface Scattering for WebGL/Three.js (SOMA Application)

## Overview
Subsurface scattering (SSS) is critical for realistic medical anatomy rendering — skin, organs, and tissue all exhibit translucency where light enters, scatters internally, and exits at a different point. Without SSS, 3D anatomy models look plastic and lifeless.

## Key Techniques (Real-Time)

### 1. Screen-Space Diffusion (Separable)
- Most common real-time approach (used in AAA games for skin)
- Two-pass Gaussian blur in screen space simulates light diffusion
- Works by rendering diffusion profile as a weighted blur kernel
- **Viable in WebGL/Three.js** using post-processing passes with EffectComposer
- Reference: Unreal Engine 4 skin shading, Frostbite SSS

### 2. Pre-Integrated Skin Shading
- Approximates SSS without blur passes
- Uses precomputed lookup textures based on curvature and N·L
- Much cheaper than screen-space methods
- **Best option for SOMA mobile** — no extra render targets needed
- Reference: Penner & Borshukov 2011, "Pre-Integrated Skin Shading"

### 3. Wrap Lighting (Cheapest)
- Simple extension to Lambertian diffuse: extend the lighting wrap factor
- `diffuse = max(0, (N·L + wrap) / (1 + wrap))`
- Gives soft, waxy appearance with zero cost
- Good fallback for low-end devices

### 4. Transmission/Translucency
- For thin features (ears, fingers, organ membranes)
- Approximate with view-dependent wrap lighting from backface
- Can use thickness maps (from AO or manually authored)

## SIGGRAPH 2025 Advances
- ReSTIR-path tracing hybrid approach for RT-capable hardware
- Not applicable to WebGL but indicates industry direction
- Diffusion-based approaches still recommended for non-RT pipelines

## SOMA Implementation Recommendation
1. **Phase 1 (immediate):** Wrap lighting for all tissue materials — zero cost, visible improvement
2. **Phase 2 (near-term):** Pre-Integrated Skin Shading for skin layers — LUT textures, single-pass
3. **Phase 3 (optional):** Screen-space diffusion for high-end mode — dual blur passes via EffectComposer
4. **Phase 4 (future):** WebGPU compute-based SSS when WebGPU adoption matures

## Key Parameters for Tissue
- **Scattering radius:** 2-8mm for skin, higher for organs (10-20mm)
- **Scattering color:** Warm reddish for blood-rich tissue, yellowish for fat
- **Curvature factor:** Higher for fingers/ears (more visible SSS), lower for flat surfaces

## Sources
- MJP's SSS Introduction: https://therealmjp.github.io/posts/sss-intro/
- SIGGRAPH 2025 Advances: https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- OpenGL SSS Tutorial: https://www.reddit.com/r/gamedev/comments/1h3ia86/


## Sources

- https://therealmjp.github.io/posts/sss-intro/
- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- https://www.reddit.com/r/gamedev/comments/1h3ia86/tutorial_realtime_subsurface_scattering_in_opengl/
