# webgpu-volume-rendering-ecosystem-2026

*Researched: 2026-04-05 22:28 CDT*

# WebGPU Volume Rendering Ecosystem (2026)

## Key Projects & Papers

### 1. Mol* Web Molecular Graphics Engine (Rose et al., 2026)
- **Paper:** Protein Science, April 2026 (doi: 10.1002/pro.70514)
- **Authors:** Alexander Rose (RCSB/UCSD), Gianluca Tomasello, Áron Kovács, Ludovic Autin, David Sehnal
- **Key insight:** High-performance open-source molecular visualization framework with WebGPU roadmap
- **Relevance to SOMA:** Mol* demonstrates GPU-accelerated 3D rendering of complex biological structures in browser. Their architecture (sphere/cylinder impostors, direct-volume rendering) maps directly to anatomy visualization needs.
- **Techniques available across web viewers:** sphere/cylinder impostors (common), direct-volume rendering (3Dmol.js, Miew, Vol-E, Mol*)
- **WebGPU roadmap:** Will enable GPU-based calculations (compute shaders) for molecular tasks — same approach applicable to tissue rendering, cross-sections, SSS shaders

### 2. WebGPU Volume Rendering Framework (MDPI Applied Sciences, 2025)
- **Paper:** MDPI Applied Sciences 15(5), 2782
- **Focus:** Interactive visualization of scalar volume data using WebGPU
- **Key approach:** Compute-shader based ray marching for volume data
- **Relevance:** Directly applicable to SOMA's DICOM/volume rendering pipeline

### 3. WebGPU Client-Side AI for Dermatology (Patel, 2026)
- **Paper:** ResearchGate, Feb 2026
- **Key insight:** Using WebGPU compute shaders for on-device ML inference
- **Relevance:** Demonstrates WebGPU compute shaders can run medical AI models client-side — SOMA could do real-time tissue classification in-browser

### 4. RADSIM Medical-Grade Browser Rendering
- Flight simulator with medical-grade rendering running entirely in browser
- Shows that real-time, high-fidelity rendering is achievable in web context

## Actionable Insights for SOMA

1. **Adopt Mol*'s impostor rendering pattern** — sphere/cylinder impostors dramatically reduce triangle count for organic shapes. SOMA's anatomy models could use similar geometry approximation.

2. **WebGPU compute shaders for SSS** — The subsurface scattering shader work in SOMA's `soma-sss-shaders` skill can leverage WebGPU compute pipelines instead of fragment-only WebGL2 approaches.

3. **Volume rendering for cross-sections** — SOMA's `soma-cross-sections` skill should use ray-marching volume rendering (as in MDPI paper) rather than geometry clipping for more realistic tissue visualization.

4. **Client-side ML inference** — WebGPU compute shaders enable running medical classification models directly in browser, preserving privacy (as shown by dermatology paper).

## Architecture Recommendation
```
SOMA Rendering Pipeline (WebGPU migration path):
  WebGL2 (current) → WebGPU (target)
  
  Fragment shaders → Compute shaders
  Geometry clipping → Volume ray marching  
  CPU-based LOD → GPU compute LOD
  Static SSS → Dynamic SSS with compute
```


## Sources

- https://pubmed.ncbi.nlm.nih.gov/41820803/
- https://www.mdpi.com/2076-3417/15/5/2782
- https://www.researchgate.net/publication/401110730
- https://developer.nvidia.com/gpugems/gpugems/part-vi-beyond-triangles/chapter-39-volume-rendering-techniques
