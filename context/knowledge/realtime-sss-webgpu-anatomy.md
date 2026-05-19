# realtime-sss-webgpu-anatomy

*Researched: 2026-04-06 06:20 CDT*

# Real-Time Subsurface Scattering for Anatomy Rendering

## SIGGRAPH 2025 State of the Art

### Key Discovery: ReSTIR-SSS (SIGGRAPH 2025 Advances)
- **Paper**: "RT Subsurface Scattering via Hybrid ReSTIR-Path Tracing" (SIGGRAPH 2025 Advances course)
- Combines path-traced light transport with diffusion profiles for real-time SSS
- Hybrid approach: coarse path tracing for primary scattering + diffusion approximation for multi-scatter
- Targets RTX-class hardware but techniques are adaptable

### Screen-Space SSS (Jorge Jimenez / Activision)
- **Reference**: https://www.iryoku.com/screen-space-subsurface-scattering/
- Industry standard for real-time skin in games
- Uses screen-space diffusion profiles (Gaussian sums)
- **Cost**: ~2-3ms on modern GPUs (from Reddit r/GraphicsProgramming)
- Requires: thickness map + depth buffer
- Thickness map generation can be expensive but pre-computation works for static anatomy meshes

### Practical Implementation for SOMA (Three.js/WebGPU)

**Recommended approach**: Screen-space SSS with pre-computed thickness maps

1. **Pre-compute thickness maps** for anatomy models (offline)
   - Ray-march from back-faces to front-faces
   - Store as greyscale texture per mesh
   - Static meshes = compute once, no runtime cost

2. **Runtime shader** (WGSL for WebGPU):
   - Sample thickness map at fragment
   - Compute diffusion profile (sum of Gaussians)
   - Apply to lighting calculation
   - Works in screen-space with depth buffer

3. **Fallback for WebGL2**:
   - Three.js `MeshPhysicalMaterial` with transmission + thickness
   - Less accurate but zero custom shader cost
   - Enable `transmission: 0.3, thickness: 2.0` for soft tissue

### MJP's SSS Introduction
- **Reference**: https://therealmjp.github.io/posts/sss-intro/
- Best overview of SSS techniques: texture-space vs screen-space
- Diffusion profiles: dipole (Jensen), separable SS (Jimenez), normalized diffusion
- For anatomy: separable screen-space is the sweet spot (quality vs performance)

### SOMA Integration Path
1. Start with `MeshPhysicalMaterial` transmission for MVP
2. Add custom WGSL screen-space SSS shader for WebGPU path
3. Pre-compute thickness maps during GLB import pipeline
4. Profile: target <3ms SSS pass on mobile GPU (A15+)
5. Long-term: evaluate ReSTIR-SSS techniques as WebGPU compute matures


## Sources

- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- https://www.iryoku.com/screen-space-subsurface-scattering/
- https://therealmjp.github.io/posts/sss-intro/
- https://www.reddit.com/r/GraphicsProgramming/comments/1lfku5c/playing_around_with_realtime_subsurface/
