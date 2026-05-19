# grenzwert-webgpu-ct-rendering

*Researched: 2026-04-19 19:39 CDT*

# Grenzwert: Path-Traced Volumetric CT Rendering in WebGPU

**Source:** https://www.webgpu.com/showcase/grenzwert-volumetric-ct-rendering-webgpu/
**GitHub:** https://github.com/MikhailGorobets/VolumeRender (C++, 64 stars)
**Demo:** https://grenzwert.net
**Author:** Mikhail Gorobets

## Architecture
- Cross-platform C++ engine compiled to WebAssembly, with WebGPU for GPU rendering
- Progressive streaming: coarse mip level first, then finer detail loads progressively
- Path tracing volumetric CT data with ground-truth fidelity
- Interactive transfer function editor (real-time opacity/color mapping)
- 3D cropping to slice away volume sections

## Key Techniques for SOMA
- **Progressive mip pyramid streaming** — respects network and user patience, coarse-to-fine rendering
- **C++/WASM core** — performance-critical path tracing in compiled code, not pure JS
- **Transfer function editing** — allows peeling tissue layers in real time
- **WebGPU path tracing** — physically accurate light scattering through bone and soft tissue

## SOMA Integration Potential
- Mip-pyramid streaming could be adapted for SOMA's anatomy model LOD system
- Transfer function approach maps to SOMA's tissue layer transparency controls
- C++/WASM rendering core pattern could improve SOMA's shader performance on mobile

## Sources

- https://www.webgpu.com/showcase/grenzwert-volumetric-ct-rendering-webgpu/
- https://github.com/MikhailGorobets/MedicalDataRenderingShowcase
