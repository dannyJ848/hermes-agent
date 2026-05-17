# webgpu-instanced-rendering-anatomy-lod

*Researched: 2026-04-06 05:52 CDT*

# WebGPU Instanced Rendering for Anatomy LOD

## Research Date: 2026-04-06

## Key Findings

### WebGPU vs WebGL for Medical Rendering
- WebGPU offers lower-level GPU control, compute shaders, and modern pipeline architecture
- Instanced rendering in WebGPU allows drawing multiple copies of anatomical structures (e.g., vertebrae, teeth) with a single draw call
- Compute shaders enable GPU-side LOD selection — calculate distance to camera on GPU and select detail level without CPU round-trip

### SOMA-Relevant Techniques
1. **GPU Instancing for Repeated Anatomy**: Vertebrae (33), teeth (32), ribs (24) are ideal candidates for instanced rendering. Single mesh + per-instance transform buffer = massive draw call reduction
2. **Compute Shader LOD Selection**: Replace CPU-based LOD switching with GPU compute pass. Each frame, compute shader evaluates camera distance per instance and writes LOD level to buffer
3. **Indirect Drawing**: `drawIndirect()` allows GPU to determine draw parameters. Combined with compute shader culling, only visible anatomy instances get drawn
4. **Memory Management**: WebGPU's buffer mapping enables efficient streaming of medical datasets that exceed GPU memory

### Implementation Path for SOMA
- Phase 1: Identify repeated anatomy meshes (vertebrae, ribs, teeth, phalanges)
- Phase 2: Create instanced mesh pipeline with per-instance transform + visibility buffer
- Phase 3: Add compute shader for frustum culling + LOD selection
- Phase 4: Benchmark against current Three.js approach (expect 3-5x draw call reduction)

### Sources Investigated
- DEV.to WebGPU 2025 guide: High-level overview, links to full guide at external site
- bioRxiv Descriptron: Multi-instance anatomical annotation platform (browser-based)
- brain2print (Nature): Web-based MRI→3D printable model pipeline
- WebGL raycasting for medical imaging (ResearchGate): Volume rendering approach

### Gap Identified
No published work found specifically on WebGPU instanced rendering for anatomy visualization. This is a green-field optimization opportunity for SOMA.


## Sources

- https://dev.to/amaresh_adak/webgpu-in-2025-the-complete-developers-guide-3foh
- https://www.biorxiv.org/content/10.64898/2026.03.10.710887v1.full-text
- https://www.nature.com/articles/s41598-025-00014-5
