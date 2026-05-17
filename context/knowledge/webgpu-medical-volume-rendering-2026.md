# webgpu-medical-volume-rendering-2026

*Researched: 2026-04-06 02:10 CDT*

# WebGPU Medical Volume Rendering — Key Projects (Apr 2026)

## Grenzwert — Path-Traced Volumetric CT in WebGPU
- **Author:** Mikhail Gorobets (graphics engineer)
- **URL:** https://grenzwert.net | Source on GitHub
- **Architecture:** C++ engine → WebAssembly + WebGPU compute/render pipeline
- **Key technique:** Progressive 3D mip-pyramid streaming — coarse level loads first, refines on idle
- **Features:** Real-time transfer function editing, 3D cropping, physically-accurate light scattering through bone/tissue
- **SOMA relevance:** ⭐⭐⭐ HIGH — Progressive streaming architecture is directly applicable to SOMA's mobile anatomy viewer. Transfer function approach could replace mesh-only rendering with hybrid volume rendering for CT/DICOM data.

## Ossium — DICOM Volume Renderer in WebGPU
- **Repo:** https://github.com/fraserlove/ossium (13 stars, MIT license, TypeScript + WebGPU)
- **Rendering modes:** Multi-Planar Reformatting (MPR) via max intensity projection + Shaded Volume Rendering (SVR) with Blinn-Phong lighting
- **Stack:** TypeScript, WebGPU, Webpack, DICOM parsing
- **SOMA relevance:** ⭐⭐⭐ HIGH — TypeScript codebase compatible with SOMA's stack. MPR + SVR rendering modes are exactly what a medical anatomy viewer needs. Could be adapted for anatomy cross-sections.

## MDPI Paper: WebGPU-Based Volume Rendering Framework
- **URL:** https://www.mdpi.com/2076-3417/15/5/2782
- **Topic:** Interactive visualization of ocean scalar data using WebGPU ray casting
- **SOMA relevance:** ⭐⭐ MEDIUM — Ray casting techniques transferable to medical volume rendering

## Integration Notes for SOMA
1. **Progressive mip-pyramid streaming** (from Grenzwert) solves mobile bandwidth constraints — load low-res first, refine on WiFi
2. **MPR rendering** (from Ossium) enables SOMA cross-section feature without pre-slicing meshes
3. **Transfer function editing** allows real-time tissue layer toggling (bone → muscle → skin)
4. Both projects prove WebGPU is production-ready for medical volume rendering in browsers
5. Ossium's TypeScript codebase could be forked/integrated directly into SOMA's Three.js pipeline

## Sources

- https://github.com/fraserlove/ossium
- https://www.webgpu.com/showcase/grenzwert-volumetric-ct-rendering-webgpu/
- https://www.mdpi.com/2076-3417/15/5/2782
