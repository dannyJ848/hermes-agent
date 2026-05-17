# webgpu-compute-shaders-medical-rendering-2026

*Researched: 2026-04-05 21:22 CDT*

# WebGPU Compute Shaders for Medical Imaging (2025-2026)

## Key Developments

### 1. WebGPU Volume Rendering Framework (MDPI Applied Sciences 2025)
- Full WebGPU-based volume rendering framework for interactive visualization of scalar data
- Demonstrates that WebGPU compute shaders can handle real-time volumetric rendering in browser
- Directly applicable to SOMA's 3D anatomy rendering pipeline — could replace Three.js raymarching with native WebGPU compute

### 2. WebGPU for Client-Side Medical AI (Patel 2026)
- On-device skin lesion classification using WebGPU compute shaders
- Implements local differential privacy for privacy-preserving diagnostics
- Proof that WebGPU can handle both rendering AND inference in browser
- **SOMA application:** Run lightweight medical classification models client-side for anatomy identification

### 3. Mol* Web Molecular Graphics Engine (Rose 2026, Protein Science)
- WebGPU upgrade for Mol* molecular visualization engine
- GPU-based calculations replacing CPU-bound approaches
- Demonstrates production-grade WebGPU adoption in scientific visualization
- **SOMA application:** Molecular-level anatomy visualization (protein structures, cellular components)

### 4. RADSIM Medical-Grade Rendering
- Flight simulator upgraded with medical-grade rendering running in browser
- Shows cross-domain applicability of medical rendering techniques

## Architecture Implications for SOMA

### Current: Three.js + WebGL2
- Raymarching via GLSL shaders
- Limited compute capabilities (no compute shaders in WebGL2)
- Texture-based volume rendering with performance constraints

### Future: WebGPU Migration Path
1. **Compute shaders** enable direct voxel manipulation without texture tricks
2. **Storage buffers** allow efficient transfer of volumetric medical data (DICOM → GPU)
3. **Parallel dispatch** enables real-time multi-tissue rendering with independent shading
4. **On-device inference** allows anatomy classification without server roundtrips

### Migration Strategy
- Phase 1: Use `navigator.gpu` detection with WebGL2 fallback
- Phase 2: Implement WebGPU compute pipeline for volume rendering
- Phase 3: Add client-side inference for anatomy labeling
- WebGPU available in Chrome 113+, Safari 18+, Firefox Nightly

## Performance Expectations
- 2-5x improvement in volume rendering throughput vs WebGL2 raymarching
- Compute shaders enable techniques impossible in WebGL2 (e.g., ambient occlusion on voxel grids, real-time SSS on volumetric tissue)
- Critical for mobile: Safari WebGPU support means iOS WKWebView can leverage GPU compute

## Sources

- https://www.mdpi.com/2076-3417/15/5/2782
- https://www.researchgate.net/publication/401110730_WebGPU_Accelerated_Client-Side_AI_for_Privacy_Preserving_Dermatological_Diagnostics
- https://onlinelibrary.wiley.com/doi/10.1002/pro.70514
