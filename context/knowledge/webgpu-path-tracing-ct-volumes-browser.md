# webgpu-path-tracing-ct-volumes-browser

*Researched: 2026-04-06 03:19 CDT*

# Real-time Path Tracing of Medical CT Volumes in Browser via WebGPU

## Source
Hacker News Show HN by MickGorobets (Feb 2026), running at grenzwert.net

## Key Technical Architecture
- **GPU path tracer** for volumetric medical data running entirely in Chrome via **WebGPU + WebAssembly (C++/Emscripten)**
- **Delta tracking (Woodcock null-collision algorithm)** for unbiased volume rendering
- **Cook-Torrance GGX BRDF** + **Henyey-Greenstein phase function** for realistic light scattering
- **MacroGrid acceleration**: DDA empty-space skipping + GPU tile culling for performance
- **Progressive frame accumulation** — noisy at first, converges to ground truth
- **HDR pipeline**: bloom, auto-exposure, PBR Neutral / ACES tone mapping
- **Async mip-level streaming** with gzip decompression for large volumes

## Framework
Built on **Diligent Engine** (contributor to its WebGPU backend)

## SOMA Relevance
- Directly applicable to SOMA's 3D anatomy viewer — could replace ray-marching with path tracing for photorealistic tissue rendering
- The Woodcock delta tracking approach handles heterogeneous media (bone, tissue, fat) naturally
- Mip-level streaming pattern useful for LOD of large DICOM volumes
- Henyey-Greenstein phase function ideal for subsurface scattering simulation in anatomical tissue
- WASM + WebGPU pattern confirms our architecture choice for SOMA mobile

## Browser Support
Chrome only (WebGPU required). Works on discrete and integrated GPUs.


## Sources

- https://news.ycombinator.com/item?id=46933474
- https://grenzwert.net
