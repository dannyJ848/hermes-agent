# webgpu-compute-shader-path-tracing

*Researched: 2026-04-06 05:16 CDT*

# WebGPU Compute Shader Real-Time Path Tracing

## Source: James Randall (2025)
Real-time path tracer built entirely in WebGPU compute shaders — no hardware RT cores, no ML denoisers, no engine. Runs at 60fps on Mac.

## Key Architecture Decisions
1. **Compute shaders only**: No rasterization pipeline — all rendering via WebGPU compute workgroups (threads, not pixels)
2. **BVH acceleration**: Bounding Volume Hierarchy for O(log n) ray-triangle intersection
3. **Monte Carlo integration**: Hemispherical sampling of the rendering equation (Kajiya 1986)
4. **Temporal accumulation**: Accumulate samples across frames for convergence
5. **Spatial denoising**: Post-process to reduce noise from low sample counts
6. **Doom WAD loader**: Parses original 1993 level geometry into triangle meshes

## SOMA Relevance
- **Anatomy LOD**: BVH + compute shaders could enable real-time level-of-detail for dense anatomy meshes (millions of triangles)
- **SSS Alternative**: Path tracing approach could simulate subsurface scattering physically (light transport through tissue) instead of faking it with shaders
- **Mobile Concern**: Performance notes suggest dropping resolution — confirms mobile WebGPU needs aggressive LOD
- **No dependencies**: Pure WebGPU approach aligns with SOMA's minimal dependency philosophy

## Performance Insights
- Even £1,600 GPU can't brute-force physics
- Noise → convergence tradeoff is fundamental
- Resolution scaling is the primary performance lever
- Mac (Apple Silicon) runs well at 60fps with defaults

## TU Wien Point Cloud Paper (2025)
Also found: "Rendering of Point Clouds via WebGPU" — compute shader pipeline for large point clouds in real-time. Relevant for medical scan data visualization (CT/MRI point cloud rendering).


## Sources

- https://www.jamesdrandall.com/posts/building-a-real-time-path-tracer-in-webgpu/
- https://www.cg.tuwien.ac.at/research/publications/2025/BAUER-2025-PCW/BAUER-2025-PCW-.pdf
