# webgpu-sss-fluid-rendering-techniques-2025

*Researched: 2026-04-05 19:35 CDT*

# WebGPU Subsurface Scattering & Fluid Rendering Techniques (2025)

## Key Finding: SIGGRAPH 2025 Real-Time SSS Course

SIGGRAPH 2025 "Advances in Real-Time Rendering" course includes a dedicated **Real-Time Subsurface Scattering** presentation. The course covers modern SSS techniques that capture significantly more skin detail with closer ground truth matching. This is the state-of-the-art reference for real-time SSS.

**Source:** advances.realtimerendering.com/s2025 (PDF available but binary)

## Key Finding: WebGPU Fluids with SSS by Hector Arellano (Codrops, Jan 2025)

### Evolution WebGL → WebGPU for Complex Rendering
- **13-year journey** from WebGL hacks to native WebGPU implementations
- WebGL limitations required hacks: no atomics, no storage buffers, no 3D textures, no compute shaders, no indirect draw calls
- WebGPU provides all modern GPU API features natively

### Techniques Implemented in WebGPU
1. **Smoothed Particle Hydrodynamics (SPH)** for fluid simulation
2. **Marching Cubes on GPU** — generate mesh triangles from particle data
3. **Hybrid Ray Tracing** — marching cubes for primary triangles + raytracer for secondary rays (reflections, refractions)
4. **Caustic Effects** via ray tracer traversing acceleration structure
5. **Subsurface Scattering** using thickness textures (baked for static geometry, computed for fluids)

### Key WebGPU Features Used
- **Compute Shaders** for GPGPU (particle simulation, marching cubes)
- **Atomics** for neighborhood search and stream compaction
- **Storage Buffers** for flexible data access
- **3D Textures** for volumetric data
- **Indirect Dispatch** for dynamic triangle generation
- **Histopyramids** for stream compaction

### Performance Insights
- WebGL version required NVidia 1080GTX — not viable for mobile
- WebGPU version is significantly more efficient with native features
- Mobile viability still depends on triangle budgets and shader complexity

## Relevance to SOMA

### Direct Applications
1. **Skin rendering:** SIGGRAPH 2025 SSS techniques can be adapted for anatomy viewer skin layers
2. **Organ transparency:** Hybrid ray tracing approach for semi-transparent organ visualization
3. **Mobile optimization:** WebGPU's compute shaders replace WebGL hacks, improving mobile performance
4. **Thickness maps:** Pre-computed thickness textures for SSS on static anatomy meshes

### Architecture Recommendations
- Use WebGPU compute shaders for any real-time mesh processing (decimation, LOD)
- Pre-bake thickness maps for SSS during asset pipeline (DICOM → glTF conversion)
- Consider hybrid ray tracing for cross-section views where refraction/reflection matters
- Monitor WebGPU browser adoption — Chrome/Edge supported, Safari in development

## Sources
- SIGGRAPH 2025 Advances: https://advances.realtimerendering.com/s2025/
- Codrops WebGPU Fluids: https://tympanus.net/codrops/2025/01/29/particles-progress-and-perseverance-a-journey-into-webgpu-fluids/
- ReSTIR Path Tracing + Diffusion: https://www.youtube.com/watch?v=AtFBbMnUgoc


## Sources

- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- https://tympanus.net/codrops/2025/01/29/particles-progress-and-perseverance-a-journey-into-webgpu-fluids/
- https://www.youtube.com/watch?v=AtFBbMnUgoc
