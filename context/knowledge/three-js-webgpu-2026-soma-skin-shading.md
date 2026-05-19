# three-js-webgpu-2026-soma-skin-shading

*Researched: 2026-04-05 14:34 CDT*

# Three.js WebGPU 2026 Status for SOMA Skin Shading

**Date:** 2026-04-05
**Relevance:** SOMA 3D anatomy viewer — mobile skin subsurface scattering

## Key Findings

### Three.js r171+ (Sept 2025) — Production WebGPU
- `import { WebGPURenderer } from 'three/webgpu'` — zero-config
- **TSL (Three Shading Language)** simplifies shader development vs raw WGSL
- Compute shaders now accessible through TSL
- WebGL fallback automatic — critical for iOS <26 compatibility
- 2.7M weekly NPM downloads by March 2026

### Performance Gains
- 100x performance for LiDAR point clouds (Segments.ai case study)
- Reduced memory overhead with enhanced instancing
- Compute shaders for collision detection, real-time filtering

### SOMA Implications
1. **Pre-integrated skin shading via TSL:** Can implement the d'Eon/Weidlich pre-integrated skin profile as a TSL node-based shader — no raw WGSL needed
2. **Mobile path:** Three.js WebGPURenderer auto-falls back to WebGL2 on iOS <26. Pre-integrated SSS works on both paths (texture lookup, not compute)
3. **Architecture:** Layer 1 = pre-integrated skin (mobile/WebGL fallback), Layer 2 = WebGPU compute ReSTIR (desktop/future mobile)
4. **Implementation priority:** TSL node shader is faster to build than raw WGSL compute pipeline

### Recommended SOMA Shader Stack
- **Tier 1 (Now):** Pre-integrated skin shading via TSL — single texture lookup, works everywhere
- **Tier 2 (WebGPU devices):** Separable Gaussian blur via compute shader (TSL)
- **Tier 3 (Future):** ReSTIR volumetric path tracing for photorealistic tissue

## Sources
- https://altersquare.io/three-js-vs-webgpu-2026-large-scale-construction-viewers/


## Sources

- https://altersquare.io/three-js-vs-webgpu-2026-large-scale-construction-viewers/
