---
name: ossium-webgpu-volume-renderer
version: 1.0
description: Ossium — WebGPU volume rendering for 3D medical imaging data in the browser. Lightweight TypeScript implementation for DICOM/NIfTI visualization.
trigger: When researching or implementing WebGPU volume rendering, DICOM visualization, or 3D medical imaging display in the browser.
---

# Ossium: WebGPU Volume Rendering for Medical Imaging

**Repo:** https://github.com/fraserlove/ossium  
**Stars:** 13 (new, April 2025) | **Language:** TypeScript (WebGPU)

## What It Does

Browser-native volume rendering of 3D medical imaging data (DICOM/NIfTI) using **pure WebGPU**. One of the first WebGPU-native medical volume renderers.

## Why It Matters for SOMA

- **WebGPU = 2-5x faster than WebGL2** for volume rendering operations
- Pure browser implementation — no server-side rendering
- Could power DICOM cross-section visualization in SOMA
- Shader approach directly applicable to SOMA's SSS (subsurface scattering) needs
- Lightweight alternative to NiiVue or VolView

## Key Technical Patterns to Study

1. **WebGPU Compute Pipelines** — how volume data is processed on GPU
2. **Ray-marching shaders** — the core rendering technique for volume data
3. **Transfer functions** — mapping intensity values to colors for tissue differentiation
4. **Progressive loading** — handling large DICOM series in browser

## Installation

```bash
git clone https://github.com/fraserlove/ossium.git
cd ossium
npm install
npm run dev
```

## Integration Path for SOMA

### Phase 1: Study & Adapt (immediate)
- Read the WebGPU shader code for ray-marching approach
- Adapt volume rendering techniques for SOMA's anatomy mesh pipeline
- Test cross-section rendering with Ossium's shader approach

### Phase 2: WebGPU Enhancement (medium-term)
- Implement WebGPU renderer as progressive enhancement in SOMA
- WebGL2 fallback for iOS Safari (SOMA's primary mobile target)
- Use for DICOM/NIfTI visualization alongside Three.js mesh rendering

### Phase 3: Full Integration (long-term)
- Unified WebGPU renderer for both meshes (anatomy) and volumes (scans)
- SSS shaders informed by Ossium's volume rendering approach

## Pitfalls
- **Safari/iOS WebGPU** — limited support as of 2025; MUST have WebGL2 fallback
- **Very new project** (13 stars) — API may change rapidly
- **No DICOM parser included** — needs integration with dicomParser or daikon
- **Browser compatibility** — Chrome/Edge only for full WebGPU features

## Related Tools
- **NiiVue** (niivue/niivue) — mature WebGL2 medical viewer with WebGPU experiments
- **VolView** (Kitware) — production browser DICOM viewer with Clara AI integration
- **MONAI** — server-side medical imaging pipeline
- **Grenzwert** (Jan 2026) — Path-traced volumetric CT rendering in WebGPU. C++/WASM + WebGPU, streams 3D mip pyramid for responsive interaction. Real-time transfer function editing and volume cropping. Ground-truth path tracing.
- **OHIF Viewer** (Mar 2026) — Clinical-grade medical imaging on WebGL. Streams DICOM (CT, MRI, PET) into browser via Cornerstone3D's single shared WebGL context. Tumor segmentation, multi-modality fusion. Production-grade.

## Sources
- https://github.com/fraserlove/ossium
