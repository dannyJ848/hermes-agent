# webgpu-volumetric-ct-rendering-grenzwert

*Researched: 2026-04-05 22:48 CDT*

# WebGPU Volumetric CT Rendering for Medical Visualization

## Grenzwert — Path-Traced Volumetric CT in Browser (Jan 2026)

**Author:** Mikhail Gorobets  
**URL:** https://grenzwert.net  
**Stack:** C++ → WebAssembly + WebGPU

### Architecture
- Cross-platform C++ engine compiled to WebAssembly
- WebGPU handles GPU-side path tracing
- **Progressive mip pyramid streaming**: coarse mip level loads first, finer detail streams in progressively
- Real-time transfer function editor — adjust opacity/color while renderer keeps up
- 3D cropping — slice away volume sections interactively
- Physical light scattering through bone and soft tissue

### Key SOMA Relevance
- This proves production-quality volumetric medical rendering is possible in-browser via WebGPU
- Progressive streaming architecture mirrors what SOMA needs for large anatomy datasets
- Transfer function approach (peeling tissue layers) maps to SOMA's layer-based anatomy exploration
- Open source on GitHub — can study shader structure and streaming pipeline

### WebGPU Compute Shader Mental Model (for MRI/CT volumes)
- Workgroup = team of parallel threads (e.g., 8×8×4 = 256 workers per group)
- Dispatch = city grid of workgroups covering entire volume
- `global_id` = absolute voxel address; `local_invocation_id` = position within workgroup
- Shared memory (`var<workgroup>`) enables intra-workgroup communication
- `workgroupBarrier()` prevents race conditions during shared memory ops
- Example: 256×256×128 MRI volume → dispatch 32×32×32 workgroups of 8×8×4

### Integration Path for SOMA
1. Study Grenzwert's progressive mip streaming for anatomy model LOD
2. Use WebGPU compute shaders for real-time volume rendering of DICOM data
3. Transfer function editor pattern for tissue layer selection
4. WebAssembly + WebGPU combo for cross-platform performance


## Sources

- https://www.webgpu.com/showcase/grenzwert-volumetric-ct-rendering-webgpu/
- https://medium.com/@osebeckley/webgpu-compute-shaders-explained-a-mental-model-for-workgroups-threads-and-dispatch-eaefcd80266a
