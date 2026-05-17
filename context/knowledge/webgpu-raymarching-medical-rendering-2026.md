# webgpu-raymarching-medical-rendering-2026

*Researched: 2026-04-05 21:52 CDT*

# WebGPU Ray Marching for Medical Volume Rendering (2026)

## Key Finding: Medical Holodeck Raymarch Rendering (Feb 2026)
Medical Holodeck implemented raymarch rendering for medical imaging in their VR platform. Key details:
- Applied when quality settings are above 50%
- Requires PC-VR rendering power (not mobile-ready yet)
- Delivers sharper visuals and smoother performance for examining medical data
- Helps identify fine anatomical details more accurately
- Maintains fast, responsive interaction within VR environment
- Source: https://www.medicalholodeck.com/en/news/update-february-2026/

## Mol* Web Molecular Graphics Engine (2026)
- Published in Protein Science (Rose, 2026)
- Supports three GPU compute functions: Gaussian-density accumulation, marching cubes isosurface extraction, and volumetric smoothing
- WebGPU-based molecular visualization
- Source: https://onlinelibrary.wiley.com/doi/10.1002/pro.70514

## MDPI WebGPU Volume Rendering Framework
- "The Implementation of a WebGPU-Based Volume Rendering" (Applied Sciences 15(5), 2782)
- Interactive visualization framework for scalar data
- 403 on direct access — need alternative source
- Source: https://www.mdpi.com/2076-3417/15/5/2782

## Reddit: Ray Marching with WebGPU + Svelte
- Open-source experiment with WebGPU ray marching
- Source code available
- Source: https://www.reddit.com/r/GraphicsProgramming/comments/1oid52n/

## SOMA Implications
1. **Raymarching is production-viable**: Medical Holodeck uses it in production for medical data
2. **PC-first, mobile-later**: Current raymarch needs PC-VR power — SOMA's mobile target needs LOD fallback
3. **Marching cubes remains relevant**: Mol* combines compute shaders with marching cubes isosurface extraction
4. **Three GPU compute pipeline pattern**: Gaussian-density → marching cubes → volumetric smoothing is a proven pipeline
5. **Quality threshold approach**: Medical Holodeck only uses raymarch above 50% quality — adaptive quality is the right pattern for SOMA


## Sources

- https://www.medicalholodeck.com/en/news/update-february-2026/
- https://onlinelibrary.wiley.com/doi/10.1002/pro.70514
- https://www.mdpi.com/2076-3417/15/5/2782
- https://www.reddit.com/r/GraphicsProgramming/comments/1oid52n/
