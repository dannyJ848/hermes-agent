# realtime-subsurface-scattering-webgpu-anatomy

*Researched: 2026-04-06 19:58 CDT*

# Real-Time Subsurface Scattering for Medical Anatomy Rendering

## Key Techniques (from NVIDIA GPU Gems Ch.16 + SIGGRAPH 2025)

### 1. Wrap Lighting (Simplest Approximation)
- Modifies Lambert diffuse to "wrap" light beyond normal terminator
- `wrap_diffuse = max(0, (dot(L,N) + wrap) / (1 + wrap))` where wrap ∈ [0,1]
- Reduces contrast, simulates light bleeding through thin tissue (ears, nostrils)
- Can encode in texture lookup with red color shift at low light = cheap skin scattering

### 2. Texture-Space Diffusion (Medium Complexity)
- Render irradiance to texture in UV space
- Apply Gaussian blur kernels with different widths per RGB channel
- Red scatters wider than green, green wider than blue (skin absorption)
- Compositing blurred channels produces realistic skin translucency

### 3. SIGGRAPH 2025 Advances
- ReSTIR-Path Tracing combined with diffusion profiles for real-time SSS
- Hybrid approach: path trace primary rays, use diffusion approximation for multi-scatter
- WebGPU path tracer for CT volumes already demonstrated in Chrome (HN item 46933474)

### SOMA Application
- For anatomy viewer, wrap lighting is the cheapest starting point (single shader change)
- Texture-space diffraction viable with WebGPU compute shaders on mobile
- Layered approach: wrap for thin skin areas, texture-space for close-up organs, path-traced for desktop
- Key insight: medical anatomy already has known scattering coefficients per tissue type — can hardcode diffusion profiles for bone, muscle, skin, fat

### Performance Targets
- Wrap lighting: ~0.1ms GPU cost (negligible)
- Texture-space diffusion: ~2-5ms depending on blur kernel count
- Path tracing: 30+ FPS demonstrated on WebGPU for CT volumes


## Sources

- https://developer.nvidia.com/gpugems/gpugems/part-iii-materials/chapter-16-real-time-approximations-subsurface-scattering
- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- https://news.ycombinator.com/item?id=46933474
