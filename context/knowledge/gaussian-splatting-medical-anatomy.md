# gaussian-splatting-medical-anatomy

*Researched: 2026-04-05 21:19 CDT*

# 3D Gaussian Splatting for Medical Anatomy Visualization

## Overview
Two major 2024-2025 papers demonstrate using 3D Gaussian Splatting (3DGS) to create interactive, photorealistic anatomy renderings from CT scans — directly applicable to SOMA's architecture.

## Paper 1: Multi-Layer Gaussian Splatting (Kleinbeck et al., IEEE TVCG 2025)
- **Authors:** Constantin Kleinbeck, Hannah Schieber, Klaus Engel, Ralf Gutjahr, Daniel Roth (TU Munich / HEX Lab)
- **Venue:** IEEE VR 2025, IEEE Transactions on Visualization and Computer Graphics
- **Key Innovation:** Layered GS representation where different anatomical structures are incrementally included as separate layers. This allows selective activation and clipping at render time — critical for interactive exploration.
- **Compression:** Clustering across layers to reduce model size.
- **Training:** Extended GS training removes inactive Gaussians.
- **Use Case:** VR headsets and compute-constrained devices. Interactive frame rates preserved.
- **Code/Data:** All code, trained models, and datasets available online.

## Paper 2: Cinematic Anatomy via Compressed 3DGS (Niedermayr et al., 2024)
- **Authors:** Simon Niedermayr, Christoph Neuhauser, Kaloian Petkov, Klaus Engel, Rüdiger Westermann (TU Munich / Siemens Healthineers)
- **arXiv:** 2404.11285
- **Key Innovation:** Pipeline: CT scan → path-traced images → 3DGS optimization → compression → WebGPU rendering.
- **Compression:** Sensitivity-aware vector quantization + entropy encoding.
- **Rendering:** WebGPU-based GPU sorting and rasterization of projected 2D splats.
- **Results:** Drastic compression ratios:
  - Brain: 36.4 GB → 69 MB (527:1)
  - Kidney: 3.6 GB → 31 MB (116:1)
  - Full body: 200 MB → 7.8 MB (26:1)
  - Skull: 64 MB → 2.1 MB (30:1)
- **Interactive Web Demos:** Working WebGPU demos available — brain, kidney, full body, skull.
- **Pipeline:** Presets define transfer functions + material classifications + clip planes → camera pose generation → path tracing → 3DGS fitting → compression → WebGPU rendering.

## SOMA Implications
1. **Mobile Performance:** 3DGS could replace mesh-based rendering for complex anatomy scenes, achieving better quality at lower triangle counts.
2. **WebGPU Requirement:** Both papers use WebGPU for rendering — aligns with SOMA's planned WebGPU migration.
3. **Layered Approach:** Multi-layer GS maps directly to SOMA's organ system layers (skin → muscles → organs → skeleton).
4. **Compression:** The extreme compression ratios (30-500x) make large anatomical datasets viable on mobile.
5. **Open Code:** Both papers provide code and datasets —可以直接集成或参考实现。

## Next Steps for SOMA
- Evaluate WebGPU 3DGS rendering pipeline as alternative to Three.js mesh rendering
- Test Niedermayr's WebGPU demo on iOS Safari (WebGPU support status)
- Consider hybrid approach: mesh for interactive dissection, 3DGS for cinematic presets
- Study compression pipeline for SOMA's GLB anatomy models

## Sources

- https://hex-lab.io/publication/2025/2025-ieee-tvcg-multi-layer-gs-constantin/
- https://niedermayr.dev/cinematic-gaussians/
- https://ieeexplore.ieee.org/document/10919012/
