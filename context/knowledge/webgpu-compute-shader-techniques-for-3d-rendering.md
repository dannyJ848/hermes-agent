# webgpu-compute-shader-techniques-for-3d-rendering

*Researched: 2026-04-05 22:46 CDT*

# WebGPU Compute Shader Techniques for 3D Rendering (2025)

## Source
Hector Arellano's 13-year journey from WebGL to WebGPU fluid simulations (Codrops, Jan 2025)

## Key Findings for SOMA

### WebGPU Features That Enable Real-Time Anatomy Rendering
1. **Compute Shaders** — Enable GPGPU on the GPU without vertex/fragment pipeline overhead. Critical for particle-based tissue simulation.
2. **Storage Buffers** — Read/write arbitrary data structures on GPU. WebGL had no equivalent (had to hack textures as data stores).
3. **3D Textures** — Native voxel data. Previously required stacking 2D texture layers in WebGL. Essential for volumetric medical data (CT/MRI).
4. **Atomics** — Thread-safe parallel operations. Needed for particle sorting, spatial hashing, mesh generation.
5. **Indirect Draw Calls** — GPU decides draw parameters without CPU round-trip. Critical for dynamic LOD where triangle counts change per frame.
6. **Indirect Dispatch** — Compute shader workgroup sizing can be GPU-driven.

### Algorithms Relevant to Anatomy Rendering
- **Smoothed Particle Hydrodynamics (SPH)** — Particle-based fluid simulation. Could simulate blood flow, tissue deformation.
- **Marching Cubes on GPU** — Generate triangle meshes from particle/voxel data in real-time. Key for converting medical scan data → renderable meshes.
- **Histopyramids** — Stream compaction on GPU. Efficient for adaptive LOD — only process visible/detailed regions.
- **Real-time Ray Tracing** — WebGPU enables basic ray tracing for subsurface scattering, reflections on tissue surfaces.

### Performance Implications for Mobile
- WebGPU compute shaders are 5-10x faster than WebGL GPGPU hacks
- Storage buffers eliminate texture-based data workarounds (significant memory savings)
- Indirect draw calls reduce CPU→GPU synchronization overhead
- Safari WebGPU support still limited (as of 2025) — need WebGL fallback path for iOS

### Architecture Recommendation for SOMA
```
WebGPU Path (Chrome/Edge):
  Compute Shaders → Mesh Generation → SSS Shaders → Display
  
WebGL Fallback (Safari/iOS):
  GPGPU via vertex shaders → Texture data → Standard shaders → Display
```

## SIGGRAPH 2025 SSS Course
SIGGRAPH 2025 "Advances in Real-Time Rendering" includes a full course on real-time subsurface scattering. The PDF covers production SSS methods that are both physically-based and artist-friendly. Directly applicable to rendering realistic skin, organs, and tissue layers in SOMA.

## Action Items
1. Implement WebGPU compute shader path for marching cubes mesh generation
2. Create WebGPU SSS shader prototype using SIGGRAPH 2025 techniques
3. Build dual pipeline: WebGPU primary + WebGL fallback for iOS compatibility
4. Benchmark SPH particle simulation feasibility on mobile GPUs


## Sources

- https://tympanus.net/codrops/2025/01/29/particles-progress-and-perseverance-a-journey-into-webgpu-fluids/
- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
