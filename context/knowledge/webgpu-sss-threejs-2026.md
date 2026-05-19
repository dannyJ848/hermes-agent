# webgpu-sss-threejs-2026

*Researched: 2026-04-06 12:43 CDT*

# WebGPU & Subsurface Scattering for Anatomy Rendering (2026 State)

## Key Findings

### Three.js WebGPU Status (March 2026)
- Three.js r171 (Sept 2025) introduced production-ready `WebGPURenderer` with zero-config import: `import { WebGPURenderer } from 'three/webgpu'`
- 2.7M weekly NPM downloads by March 2026
- WebGPURenderer provides 100x performance gains for LiDAR point clouds and millions of particles
- Compute shaders now available for collision detection, real-time filtering
- Three.js TSL (Three Shading Language) simplifies shader development
- WebGL fallback still available for backward compatibility

### NVIDIA SIGGRAPH 2025: Hybrid Real-Time SSS
- Novel hybrid technique combining **volumetric path tracing** + **diffusion-based SSS**
- Uses ReSTIR (Reservoir-based Spatiotemporal Importance Resampling) for path tracing
- Physically-based approach captures significantly more skin detail with closer ground truth matching
- Targets real-time game rendering framerates
- Published at SIGGRAPH 2025 Advances in Real-Time Rendering course

### SOMA Architecture Implications
1. **Migration path:** Three.js r171+ WebGPURenderer is production-ready — SOMA should plan migration from WebGL
2. **SSS shaders:** The hybrid path-tracing + diffusion approach could be adapted for anatomical tissue rendering
3. **Mobile caveat:** WebGPU on mobile Safari (iOS) still has limited support — need WebGL fallback for SOMA iOS app
4. **Performance gains:** 100x improvement for large meshes means SOMA's full-body anatomy models could render without aggressive LOD
5. **TSL shaders:** Three Shading Language could simplify SOMA's custom SSS shader code (soma-sss-shaders skill)

### Sources
- SIGGRAPH 2025 Advances course: https://advances.realtimerendering.com/s2025/
- Three.js WebGPU 2026 overview: https://altersquare.io/three-js-vs-webgpu-2026-large-scale-construction-viewers/
- NVIDIA GPU Gems 3 Ch.14 (classic SSS reference): https://developer.nvidia.com/gpugems/gpugems3/part-iii-rendering/chapter-14-advanced-techniques-realistic-real-time-skin


## Sources

- https://advances.realtimerendering.com/s2025/
- https://altersquare.io/three-js-vs-webgpu-2026-large-scale-construction-viewers/
- https://developer.nvidia.com/gpugems/gpugems3/part-iii-rendering/chapter-14-advanced-techniques-realistic-real-time-skin
