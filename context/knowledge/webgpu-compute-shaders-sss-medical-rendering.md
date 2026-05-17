# webgpu-compute-shaders-sss-medical-rendering

*Researched: 2026-04-06 03:27 CDT*

# WebGPU Compute Shaders for Real-Time Subsurface Scattering in Medical 3D

## Key Findings

### Screen-Space SSS via Thickness Maps (Reddit r/GraphicsProgramming, 2025)
- Real-time SSS achievable at **<2-3ms** cost using thickness maps + diffusion profiles computed in screen space
- Technique: Calculate thickness map from depth buffer, then compute diffusion profiles per-pixel
- Very applicable to SOMA: anatomical models already have depth information, could add SSS pass for skin/organ translucency
- No precomputation needed — runs entirely in screen space

### WebGPU Compute Shader Capabilities (Codrops/Hector Arellano, Jan 2025)
- WebGPU unlocks: **Compute Shaders, Storage Buffers, 3D Textures, Indirect Draw Calls, Atomics**
- These were previously unavailable in WebGL — enables GPU-driven particle systems, marching cubes on GPU, SPH fluid simulation
- Key for medical rendering: **3D Textures** allow volumetric rendering (CT/MRI data), **Compute Shaders** enable custom lighting models like SSS
- Browser support: Chrome and Edge (WebGPU enabled), not yet universal

### RT Subsurface Scattering via Hybrid ReSTIR-Path Tracing (GDC 2025)
- Combines path-traced light transport with diffusion profiles for real-time SSS
- Uses ReSTIR (Reservoir-based Spatiotemporal Importance Resampling) for efficient light sampling
- Industry standard approach for AAA-quality skin rendering

## Application to SOMA
1. **Phase 1 (WebGL fallback):** Screen-space SSS with thickness maps — works in current Three.js/WebGL pipeline
2. **Phase 2 (WebGPU):** Full compute-shader SSS with 3D texture support for volumetric organs
3. **Performance target:** <3ms SSS pass maintains 30fps on mobile with triangle budget

## Sources
- Reddit r/GraphicsProgramming: Real-time SSS + thickness maps technique
- Codrops: WebGPU fluid simulation journey (compute shader capabilities)
- GDC Talk: RT SSS via Hybrid ReSTIR-Path Tracing


## Sources

- https://www.reddit.com/r/GraphicsProgramming/comments/1lfku5c/playing_around_with_realtime_subsurface/
- https://tympanus.net/codrops/2025/01/29/particles-progress-and-perseverance-a-journey-into-webgpu-fluids/
- https://matthewmacfarquhar.medium.com/webgpu-rendering-part-21-raytracing-shapes-0b76686ec601
