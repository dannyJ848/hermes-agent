# grenzwert-webgpu-ct-volume-rendering

*Researched: 2026-04-07 00:22 CDT*

# Grenzwert: Path-Traced Volumetric CT Rendering in WebGPU

**Date:** 2026-04-07
**Author:** Mikhail Gorobets
**URL:** https://grenzwert.net
**Source:** https://www.webgpu.com/showcase/grenzwert-volumetric-ct-rendering-webgpu/

## Key Technical Details
- **Core:** Cross-platform C++ engine compiled to WebAssembly + WebGPU compute/render pipeline
- **Rendering:** Ground-truth path tracing of volumetric CT data in the browser
- **Streaming:** Progressive 3D mip pyramid — coarse level first, fine detail on idle
- **Interaction:** Real-time transfer function editor (opacity/color), 3D cropping, progressive refinement
- **Performance:** Interactive despite path tracing complexity; never blank screen

## Relevance to SOMA
- **Architecture pattern:** C++/WASM + WebGPU is viable for browser-based medical volume rendering
- **Streaming approach:** Mip pyramid progressive loading solves mobile bandwidth concerns
- **Transfer functions:** Same concept needed for SOMA tissue classification (bone/muscle/organ separation)
- **Open source:** GitHub repo available for shader structure and streaming pipeline reference

## Integration Ideas
1. Study the mip pyramid streaming pipeline for SOMA's DICOM/NIfTI loading
2. Transfer function editor pattern directly applicable to SOMA's tissue layer controls
3. Progressive refinement approach ideal for mobile — render coarse first, refine on idle
4. WebAssembly compute bridge pattern useful for heavy medical computations off main thread

## Also Noted
- Chrome 139 added native `texture_3d` support in WebGPU (official sample: "Volume Rendering - Texture 3D")
- MDPI paper on WebGPU volume rendering for ocean scalar data (similar compute shader patterns)


## Sources

- https://www.webgpu.com/showcase/grenzwert-volumetric-ct-rendering-webgpu/
- https://developer.chrome.com/blog/new-in-webgpu-139
