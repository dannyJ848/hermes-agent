# biolens-architecture-analysis-soma-integration-april-2026

*Researched: 2026-04-03 14:05 CDT*

# BioLens Architecture Analysis: Volume Ray Marching for SOMA Cross-Sections

**Date:** April 3, 2026
**Source:** https://github.com/felix-ops/bio-lens (cloned and analyzed)

## Architecture Overview
BioLens is a Next.js + Babylon.js application for DICOM volumetric visualization in the browser.

### Core Components:
1. **`core/shader.ts`** — Vertex + Fragment shaders (GLSL) for volume ray marching
2. **`lib/loaders/dicom-loader.ts`** — DICOM → 3D texture pipeline using dcmjs
3. **`lib/loaders/nifti-loader.ts`** — NIfTI volume support
4. **`lib/transfer-function-store.ts`** — Color/alpha mapping for tissue differentiation
5. **`components/organisms/babylon-renderer.tsx`** — Babylon.js scene setup
6. **`components/organisms/transfer-function.tsx`** — Interactive transfer function UI

## Key Shader Techniques (Portable to SOMA)

### 1. Ray Marching with Jittering
```glsl
float jitter = hash12(gl_FragCoord.xy + u_time * 50.0);
tStart += jitter * stepSize;
```
Randomizes ray start position to eliminate banding artifacts. Essential for medical quality.

### 2. Transfer Function (Color + Alpha Separation)
- Color stops: up to 32 stops with RGB/HSL interpolation
- Alpha stops: independent opacity control per intensity
- Supports both RGB linear and HSL shortest-path interpolation
- This directly maps to SOMA's "layer opacity sliders" concept

### 3. Adaptive Step Size
```glsl
float stepSize = length(u_volume_size_world) / length(u_voxel_resolution);
```
Automatically adjusts quality based on data resolution. On mobile, could use 2x step size.

### 4. Early Ray Termination
```glsl
if (accumulatedColor.a > 0.99) break;
```
Stops marching when pixel is fully opaque. Critical performance optimization.

### 5. 3D Clipping Planes
```glsl
if (any(lessThan(uvw, u_clip_min)) || any(greaterThan(uvw, u_clip_max))) {
    // Skip sample
}
```
Directly applicable to SOMA's cross-section feature.

## DICOM Loading Pipeline
```
DICOM file → dcmjs parse → extract pixel data → rescale (slope/intercept)
→ normalize to 0-1 → create RawTexture3D → upload to GPU
```
Handles: 8-bit, 16-bit (signed/unsigned), 32-bit, multiframe DICOM.
Reorients spacing from standard DICOM (Axial: LR/AP/IS) to user view (Sagittal/Axial/Coronal).

## SOMA Integration Plan

### Phase 1: Mesh-Based (Current SOMA approach — keep this)
SOMA currently uses procedural geometry (EnhancedAnatomyModel). This is correct for the educational anatomy use case — surface meshes are faster and more interactive than volume rendering.

### Phase 2: Volume Cross-Sections (Add BioLens ray march for DICOM overlay)
When a user selects "cross-section" or "histology" view for a body region:
1. Load a pre-processed DICOM/NIfTI volume for that region
2. Apply BioLens ray marching shader (ported to Three.js/WebGPU)
3. Use transfer function to highlight relevant tissue layers
4. Allow 3D clipping planes for cross-section interaction

### Phase 3: WebGPU Migration (Future)
Port the GLSL shader to WGSL for WebGPU compute:
- Replace `sampler3D` with WebGPU storage texture
- Replace fragment shader with compute dispatch
- Enable progressive refinement across frames

### Mobile Performance Budget
- Volume size: 256³ maximum (16MB GPU) vs BioLens's 512³ (125M voxels)
- Step count: 256 steps mobile / 512 desktop
- Frame budget: 16ms (60fps) → adaptive step reduction
- Mip streaming: Load 128³ first, refine to 256³

## Dependencies to Evaluate
- `dcmjs` (MIT) — DICOM parsing (already used in SOMA's mcp-slicer evaluation)
- `@babylonjs/core` — Would need to port to Three.js for SOMA
- Three.js `Data3DTexture` — Available since r158, equivalent to Babylon's RawTexture3D


## Sources

- https://github.com/felix-ops/bio-lens
- https://forum.babylonjs.com/t/volumetric-visualization-app-for-medical-scans-biolens/61537
