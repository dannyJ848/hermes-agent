# grenzwert-biolens-webgpu-volume-rendering-april-2026

*Researched: 2026-04-03 14:03 CDT*

# WebGPU Volume Rendering for Medical Imaging: Grenzwert & BioLens (April 2026)

**Date:** April 3, 2026
**Sources:** webgpu.com (Grenzwert), Babylon.js forum (BioLens)

## Grenzwert — Path-Traced Volumetric CT in WebGPU
- **Author:** Mikhail Gorobets (graphics engineer)
- **URL:** https://grenzwert.net (live demo)
- **Architecture:** Cross-platform C++ engine → WebAssembly + WebGPU
- **Key Features:**
  - Ground-truth path tracing of volumetric CT data in browser
  - Progressive streaming via 3D mip pyramid (coarse → fine)
  - Real-time transfer function editing (opacity + color mapping)
  - 3D cropping/slicing in real time
  - Physically-based light scattering through bone and soft tissue
- **SOMA Relevance:** This proves WebGPU can handle medical-grade volumetric rendering client-side. The mip pyramid streaming approach is ideal for SOMA's mobile constraint — start with low-res, refine on idle. The transfer function approach maps directly to SOMA's tissue layer visibility concept.
- **Integration Path:** SOMA could adopt the mip-level streaming pattern for DICOM-derived 3D textures, keeping initial load <2s on mobile while progressively refining.

## BioLens — DICOM Volume Visualization in Babylon.js
- **Author:** Bhuvaneshwaran_M (GitHub: felix-ops/bio-lens)
- **Framework:** Babylon.js with custom shader
- **Key Techniques:**
  - Volume ray marching through 3D texture on GPU
  - Uploads volume as 3D texture for fast shader sampling
  - Compared voxel traversal (blocky) vs ray marching (smooth with interpolation)
  - Interactive transfer function for opacity/color control
  - 512×512×512 = ~125M voxels handled
  - Open-source on GitHub
- **SOMA Relevance:** Open-source reference implementation for volume ray marching. Could inform SOMA's cross-section and dissection rendering. The ray marching approach with interpolation produces medical-quality visuals.

## Synthesis for SOMA Architecture

Both projects validate the same architectural pattern that SOMA should follow:

1. **Upload volumetric data as 3D texture** (GPU-resident for fast sampling)
2. **Ray march in fragment shader** (better quality than voxel traversal)
3. **Progressive refinement** (start coarse, sharpen over frames)
4. **Transfer function UI** (let users control tissue visibility by density)

For SOMA's mobile target, the key constraint is texture memory. A 256³ volume at 8-bit = 16MB GPU memory — manageable even on older iPhones. The ray march step count must be adaptive (fewer steps on mobile, more on desktop).

## Action Items for SOMA
- [ ] Evaluate Grenzwert's C++/WASM approach for iOS WKWebView compatibility
- [ ] Study BioLens ray marching shader for adaptation to Three.js/WebGPU
- [ ] Design mip-level streaming for SOMA's anatomy data (currently mesh-based, future volume support)
- [ ] Prototype transfer function UI matching SOMA's existing layer opacity sliders


## Sources

- https://www.webgpu.com/showcase/grenzwert-volumetric-ct-rendering-webgpu/
- https://forum.babylonjs.com/t/volumetric-visualization-app-for-medical-scans-biolens/61537
- https://grenzwert.net
