# medical-image-segmentation-to-3d-mesh-pipeline

*Researched: 2026-04-03 05:45 CDT*

# Medical Image Segmentation → 3D Mesh Pipeline for SOMA

## Overview

A comprehensive research survey of open-source tools and pipelines for converting medical imaging data (CT/MRI DICOM) into 3D meshes suitable for WebGL/WebGPU rendering, directly applicable to SOMA's anatomy viewer.

## Key Tools & Frameworks

### 1. TotalSegmentator (★2.6K, Apache-2.0)
- **What:** Automatically segments 104+ anatomical structures (27 organs, 59 bones, 10 muscles, 8 vessels) from CT/MRI
- **Built on:** nnU-Net v2 (the gold standard for medical segmentation)
- **Training data:** 1,228 CT subjects + 616 MR subjects (publicly downloadable)
- **Online tool:** totalsegmentator.com for testing without installation
- **3D Slicer integration:** Available as extension for interactive refinement
- **SOMA relevance:** ★★★★★ — This is the most direct path to generating comprehensive anatomical meshes. Could produce all 104 structures automatically from any CT scan.
- **GitHub:** https://github.com/wasserth/TotalSegmentator

### 2. MONAI (5.5M+ downloads, Apache-2.0)
- **What:** End-to-end medical AI framework (annotation → training → deployment)
- **Components:**
  - **MONAI Core:** Domain-specific transforms, UNETR architecture, 40+ pre-trained models, automated ML pipelines
  - **MONAI Label:** AI-assisted interactive annotation with active learning
  - **MONAI Deploy:** Clinical deployment with DICOM/FHIR support, containerized MAPs
- **MAISI:** 3D Latent Diffusion Model for synthetic medical image generation
- **DeepAtlas:** Joint learning of registration + segmentation (solves limited data problem)
- **SOMA relevance:** ★★★★ — Framework for training custom segmentation models if TotalSegmentator's 104 structures aren't enough. MONAI Deploy's FHIR support aligns with SOMA's FHIR integration plans.
- **GitHub:** https://github.com/Project-MONAI

### 3. nnU-Net v2 (MICCAI 2024 benchmark winner)
- **Key finding from "nnU-Net Revisited" (arXiv:2404.09556):**
  - CNN-based U-Net with proper configuration STILL outperforms Transformer and Mamba-based approaches
  - The recipe for SOTA: (1) CNN U-Net with ResNet/ConvNeXt variants, (2) nnU-Net framework, (3) scale to modern hardware
  - Paper exposes "innovation bias" — many claimed architecture improvements fail under rigorous validation
  - **Lesson for SOMA:** Don't chase novel architectures. Use proven nnU-Net recipes for any custom segmentation needs.

### 4. 3D Slicer Open Anatomy Export
- **What:** Export segmentations directly to glTF format with hierarchy, colors, and metadata
- **Pipeline:** Segmentation → Convert to models → Set PBR interpolation → Export glTF
- **Caveat:** glTF only supports PBR shading; transparent structures (vessels) need depth-sorted rendering
- **SOMA relevance:** ★★★★★ — This is the exact output format SOMA uses. Proves the DICOM → segmentation → glTF pipeline is mature and production-ready.

## Recommended SOMA Pipeline

```
DICOM/CT Scan
    ↓
TotalSegmentator (104 structures auto-segment)
    ↓
3D Slicer (optional refinement, quality check)
    ↓
Marching Cubes (segmentation mask → mesh)
    ↓
Open Anatomy Export → glTF/GLB
    ↓
SOMA optimization (LOD, texture compression, SSS shaders)
    ↓
Three.js/WebGPU rendering in SOMA viewer
```

## Alternative: MONAI for Custom Models

If TotalSegmentator's 104 structures need extension:
1. Use MONAI Label for efficient annotation of additional structures
2. Train with MONAI Core using nnU-Net recipes
3. Deploy via MONAI Deploy with DICOM/FHIR integration
4. Export segmentations through same glTF pipeline

## Technical Notes

### Mesh Generation from Segmentation Masks
- **Algorithm:** Marching Cubes (VTK implementation is standard)
- **Export chain:** VTK marching cubes → OBJ → glTF (proven in published pipeline)
- **Optimization:** Decimate meshes for mobile, use LOD (Level of Detail) hierarchy

### Transparency Challenges
- Thin structures (vessels, bronchi) require depth-sorted rendering in WebGL
- SOMA's existing SSS shader approach should handle tissue transparency well
- Consider separate render passes for opaque organs vs. transparent vasculature

### Federated Learning Option
- FednnU-Net (PMC, 2025) enables privacy-preserving segmentation training across hospitals
- Relevant if SOMA ever trains custom models on hospital data

## Action Items for SOMA

1. **Evaluate TotalSegmentator** on sample CT data → measure segmentation quality for anatomy education use case
2. **Test 3D Slicer glTF export** → verify mesh quality in SOMA's Three.js viewer
3. **Build DICOM-to-GLB pipeline** using VTK marching cubes + gltf-transform for optimization
4. **Benchmark mesh complexity** — 104 structures may produce too many triangles for mobile; need LOD strategy
5. **Consider MONAI for custom structures** — if specific educational anatomy isn't covered by TotalSegmentator's 104 classes

## Sources
- TotalSegmentator: https://github.com/wasserth/TotalSegmentator (Radiology AI 2022)
- nnU-Net Revisited: arXiv:2404.09556 (MICCAI 2024)
- MONAI: https://project-monai.github.io/ (5.5M+ downloads)
- 3D Slicer Open Anatomy: https://discourse.slicer.org/t/open-anatomy-export-in-gltf-format/34819
- DICOM→glTF pipeline: JOIG V11N1-32 (2023)


## Sources

- https://github.com/wasserth/TotalSegmentator
- https://arxiv.org/abs/2404.09556
- https://project-monai.github.io/
- https://discourse.slicer.org/t/open-anatomy-export-in-gltf-format/34819
- https://www.joig.net/uploadfile/2023/JOIG-V11N1-32.pdf
