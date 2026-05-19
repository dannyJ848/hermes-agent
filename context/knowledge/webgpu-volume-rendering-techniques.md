# webgpu-volume-rendering-techniques

*Researched: 2026-04-05 19:40 CDT*

# WebGPU Volume Rendering Techniques for Medical Anatomy (2025-2026)

## Key Projects

### Grenzwert (Jan 2026)
- **Author:** Mikhail Gorobets
- **Tech:** C++/WebAssembly + WebGPU
- **Technique:** Ground-truth path tracing for volumetric CT data in browser
- **Key Innovation:** 3D MIP (Maximum Intensity Projection) pyramid streaming for responsive interaction
- **Features:** Real-time transfer function editing, volume cropping/slicing, path-traced lighting
- **Relevance to SOMA:** Proves WebGPU path tracing of medical volumes is production-viable in browser. The MIP pyramid approach is the key pattern — precompute a sparse volumetric LOD hierarchy so interaction (rotation, transfer function changes) stays 60fps while detail streams in.

### OHIF Viewer (Mar 2026)
- **Tech:** WebGL via Cornerstone3D, single shared WebGL context
- **Features:** DICOM streaming, CT/MRI/PET fusion, tumor segmentation, GPU-accelerated rendering
- **Relevance:** Production-grade radiology tools on web. Demonstrates the full medical imaging pipeline (DICOM → WebGL → clinical UI) is viable without native apps.

## Technique Summary for SOMA

### Volume Rendering Pipeline (applicable to cross-section/dissection feature)
1. **Data:** Convert DICOM/NIfTI to 3D texture (WebGPU `storageTexture` or `texture_3d`)
2. **LOD:** Build 3D MIP pyramid (half-resolution at each level) for responsive interaction
3. **Ray marching:** Compute shader casts rays through volume, sampling transfer function
4. **Transfer function:** 1D/2D lookup mapping density → color+opacity (real-time editable)
5. **Path tracing (optional):** Monte Carlo light transport for photorealistic rendering — Grenzwert proves this is viable at interactive rates

### SOMA Integration Phases
- **Phase 1 (mobile-safe):** Ray-marched volume rendering with simple transfer functions via WebGPU compute shaders. MIP pyramid for LOD. Target: CT slice viewers.
- **Phase 2 (desktop):** Add path-traced global illumination for realistic tissue appearance. Transfer function presets for bone/muscle/organ visualization.
- **Phase 3 (future):** Full hybrid mesh (surface anatomy) + volume (internal anatomy) rendering. Cross-section cuts reveal volumetric data beneath surface meshes.

### Performance Notes
- MIP pyramid reduces per-frame texture bandwidth by ~4-8x during interaction
- Path tracing requires ~64-256 samples/pixel for convergence; use progressive refinement (render 1 spp/frame, accumulate)
- Mobile WebGPU: compute shaders work but memory bandwidth is the bottleneck. Keep volume textures ≤256³ on mobile.

## Sources
- https://www.webgpu.com/tag/medical-visualization/ (Grenzwert + OHIF showcase)
- https://www.mdpi.com/2076-3417/15/5/2782 (WebGPU volume rendering framework — 403 blocked)
- https://www.linkedin.com/posts/mikesworley_grenzwert-path-traced-volumetric-ct-rendering-activity-7422583088162983936-dvs9


## Sources

- https://www.webgpu.com/tag/medical-visualization/
- https://www.linkedin.com/posts/mikesworley_grenzwert-path-traced-volumetric-ct-rendering-activity-7422583088162983936-dvs9
