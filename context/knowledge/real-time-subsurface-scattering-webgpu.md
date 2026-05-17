# real-time-subsurface-scattering-webgpu

*Researched: 2026-04-06 01:53 CDT*

# Real-Time Subsurface Scattering for WebGPU Anatomy Rendering

## Summary
Key techniques for implementing real-time subsurface scattering (SSS) in WebGL/WebGPU, directly applicable to SOMA's 3D anatomy viewer for realistic tissue rendering.

## Core SSS Approaches (Complexity Order)

### 1. Screen-Space SSS (Jorge Jimenez, GPU Pro / Iryoku)
- **Industry standard** used by CryEngine 3, Unreal Engine 3+, Confetti RawK
- Operates in screen-space using separable Gaussian blur passes
- 6 large Gaussian kernels approximate skin diffusion profile
- Key insight: light entering translucent objects scatters and exits at different points → "light is blurred"
- Visual cues: pores filled with light, reddish gradients at light/shadow boundaries, ears/nostrils glow through thin tissue
- **SOMA applicability**: Best balance of quality/performance for mobile WebGPU

### 2. Texture-Space Diffusion (GPU Gems 3, Chapter 14)
- NVIDIA technique: render to texture space, apply diffusion as blur
- Uses diffusion profiles based on Jensen's dipole model (used for Gollum in LOTR)
- More accurate but more expensive than screen-space approach
- Requires unwrapped UV texture space rendering

### 3. ReSTIR Subsurface Scattering (Werner et al. 2024, SIGGRAPH 2025)
- **State-of-the-art** for path-traced SSS
- Combines ReSTIR path tracing with diffusion profiles
- Too expensive for mobile WebGPU currently, but technique direction for future

### 4. Pre-Integrated Skin Shading (Penner & Borshukov)
- Pre-compute scattering into LUTs (look-up textures)
- No blur passes needed — just texture lookups per pixel
- **Best for SOMA mobile**: minimal compute cost, good visual quality

## Recommended SOMA Implementation Strategy

**Phase 1 (Now - WebGL compatible):**
- Pre-integrated skin shading with LUT
- Per-pixel normal map perturbation for pore/wrinkle detail
- Wrap lighting for ears/nostrils translucency

**Phase 2 (WebGPU upgrade):**
- Screen-space separable SSS (2-pass Gaussian blur)
- Diffusion profile tuned for tissue types (skin, muscle, organ tissue)
- Separate scattering radius per tissue category

**Phase 3 (Future):**
- Full path-traced SSS with WebGPU compute shaders
- Volumetric tissue scattering for cross-section views

## Key Shader Parameters for Anatomy
- **Skin scattering radius**: 2-4mm (reddish diffusion)
- **Muscle tissue**: 1-3mm (darker red diffusion)
- **Organ tissue**: 3-8mm (varies by organ — liver very dense, lungs very translucent)
- **Fat tissue**: 4-10mm (yellowish diffusion, high translucency)
- **Cartilage**: 1-2mm (minimal scattering)

## Three.js Integration Notes
- Three.js has basic SSS example in `/examples/` but limited
- Community discussion at discourse.threejs.org shows demand for screen-space approach
- For SOMA: custom ShaderMaterial with pre-integrated LUT + wrap lighting is fastest path
- WebGPU compute shaders enable screen-space blur passes (TComputePass)

## Sources
- Jimenez screen-space SSS: iryoku.com/screen-space-subsurface-scattering
- MJP intro: therealmjp.github.io/posts/sss-intro/
- GPU Gems 3 Ch.14: developer.nvidia.com/gpugems3/part-iii-rendering/chapter-14
- ReSTIR SSS (2024): dl.acm.org/doi/abs/10.1145/3675372


## Sources

- https://www.iryoku.com/screen-space-subsurface-scattering/
- https://therealmjp.github.io/posts/sss-intro/
- https://developer.nvidia.com/gpugems/gpugems3/part-iii-rendering/chapter-14-advanced-techniques-realistic-real-time-skin
- https://discourse.threejs.org/t/skin-shading-with-screen-space-sub-surface-scattering/83939
