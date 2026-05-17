# medsam2-3d-medical-segmentation

*Researched: 2026-04-03 04:11 CDT*

# MedSAM2: Segment Anything in 3D Medical Images and Videos

**Research Date:** April 3, 2026
**Paper:** arXiv:2504.03600 (April 2025)
**Authors:** Jun Ma, Zongxin Yang, et al. (University Health Network, Vector Institute, Harvard, U of Toronto)

## Overview

MedSAM2 is a **promptable segmentation foundation model** for 3D medical images and videos, built by fine-tuning Meta's SAM2 on a massive medical dataset. It represents a major leap over MedSAM (2D only) and addresses the critical gap in 3D/volumetric medical segmentation.

## Key Numbers

- **Training data**: 455,000+ 3D image-mask pairs + 76,000+ annotated video frames
- **Modalities**: CT, PET, MRI, ultrasound, endoscopy
- **User study**: Annotated 5,000 CT lesions, 3,984 liver MRI lesions, 251,550 echocardiogram frames
- **Efficiency gain**: Reduces manual annotation cost by **>85%**

## Architecture

```
Image Encoder → Multiscale Feature Extraction
                       ↓
Prompt Encoder → Bounding Box / Point Prompts
                       ↓
Memory Attention → Conditions current frame on past frames + predictions (streaming memory)
                       ↓
Mask Decoder → Accurate segmentation masks
```

**Key innovation**: Memory attention module exploits spatial continuity across slices/frames — enabling both 3D volumetric segmentation AND temporal video segmentation with a single architecture.

## Deployment

- Integrated into **3D Slicer** for organ/lesion segmentation in CT scans
- Available on **Hugging Face Spaces** for cloud deployment
- Local deployment supported (laptop-grade GPUs)
- Code and weights publicly available

## SOMA Relevance

**Direct integration potential:**
1. **Anatomy segmentation**: MedSAM2 can segment organs from CT/MRI, producing masks that can be converted to 3D meshes for SOMA's anatomy viewer
2. **Interactive dissection**: Users could click on an anatomical region in a cross-section and get an instant segment — enabling SOMA's planned "interactive cross-section" feature
3. **DICOM pipeline**: MedSAM2 runs on 3D Slicer, which uses DICOM natively — fits SOMA's DICOM-to-glTF asset pipeline
4. **ONNX export**: SAM2 models export to ONNX, enabling browser-based inference via ONNX Runtime Web for SOMA's web viewer

**Implementation path:**
1. Export MedSAM2 to ONNX format
2. Integrate with SOMA's ZAnatomyLoader as a pre-processing step
3. Use segmentation masks to generate per-organ glTF meshes
4. Add browser-based interactive segmentation (click-to-segment in cross-sections)

## Comparison: MedSAM vs MedSAM2

| Feature | MedSAM (2024) | MedSAM2 (2025) |
|---------|---------------|-----------------|
| Dimensionality | 2D only | 3D + Video |
| Base model | SAM | SAM2 |
| Memory attention | No | Yes (streaming) |
| Training data scale | ~1.5M 2D images | 455K 3D volumes + 76K frames |
| Annotation speedup | ~50% | **>85%** |
| 3D Slicer integration | Limited | Full |


## Sources

- https://arxiv.org/abs/2504.03600
- https://medsam2.github.io/
- https://www.nature.com/articles/s41467-024-44824-z
