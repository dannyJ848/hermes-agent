# webgpu-mri-raycast-engine

*Researched: 2026-04-06 18:55 CDT*

# WebGPU MRI Raycast Engine — Real-time Brain Reconstruction

**Date:** 2026-04-06
**Source:** Three.js Forum / GitHub
**Relevance:** HIGH — Directly applicable to SOMA's 3D anatomy rendering pipeline

## Key Technical Details

- **Pure WebGPU compute shaders** — no Three.js abstractions, built from scratch
- **Parallel reduction loops** for volume traversal
- **Tissue segmentation pipeline** running entirely on GPU
- **Performance:** ~100fps on integrated Intel graphics (Core i3 13th Gen)
- **Volume resolution:** 256×256×176 tested, up to 450×450×150 without freeze
- **Live demo:** https://webgpu-mri.vercel.app/
- **Repo:** https://github.com/Bahdmanbabzo/webgpu-mri

## Relevance to SOMA

1. **Compute shader approach** bypasses Three.js overhead for volume rendering — relevant if SOMA needs DICOM/MRI visualization
2. **GPU tissue segmentation** could replace CPU-based segmentation in anatomy models
3. **Parallel reduction loops** pattern applicable to SOMA's LOD and culling systems
4. **Integrated GPU performance** validates targeting mobile/low-end devices
5. **Memory alignment techniques** from author's Medium articles applicable to WebGPU shader optimization

## Integration Potential

- Study the compute shader architecture for SOMA's subsurface scattering implementation
- Evaluate parallel reduction for SOMA's cross-section computation
- Consider WebGPU fallback path for volume rendering if WebGL2 limits are hit on mobile Safari


## Sources

- https://discourse.threejs.org/t/webgpu-mri-raycast-engine-real-time-brain-reconstruction-in-the-browser/89988
- https://github.com/Bahdmanbabzo/webgpu-mri
