# sam2-zero-shot-3d-ct-segmentation

*Researched: 2026-04-03 06:02 CDT*

# SAM2 Zero-Shot 3D CT Segmentation (March 2026)

**Paper**: "Automatic Segmentation of 3D CT scans with SAM2 using a zero-shot approach"
**Authors**: Miquel López Escoriza & Pau Amargant Alvarez (EPFL)
**arXiv**: 2603.23116v1 [cs.CV] 24 Mar 2026

## Key Innovation
Uses SAM2 (Segment Anything Model 2) for **zero-shot volumetric CT segmentation** — no fine-tuning, no domain-specific training. Treats CT slices as ordered video frames and leverages SAM2's streaming memory mechanism.

## Method
1. CT volume → pseudo-video (z-axis = temporal dimension)
2. Image encoder processes each slice → embedding
3. Prompted slices (e.g., first & last frame) stored in memory bank with temporal embeddings
4. Memory attention module attends to fixed window of 6 frames
5. Mask decoder generates segmentation per slice

## Inference-Only Modifications
- **Prompt strategies**: Test different prompting approaches (first/last frame, middle frame, etc.)
- **Memory propagation schemes**: How features flow between slices
- **Multi-pass refinement**: Iterative improvement
- **Multi-axis propagation**: Not just axial — sagittal and coronal too

## Results
- Evaluated on TotalSegmentator dataset (2,500 CT scans)
- Produces **coherent 3D segmentations** with frozen weights
- Demonstrates volumetric awareness from inference configuration alone

## SOMA Relevance — HIGH
This is a **game-changer** for SOMA's mesh pipeline:

1. **Zero-shot = no training data needed**: Can run on any CT/MRI without TotalSegmentator's specific training
2. **SAM2 is open-source**: Can be bundled in SOMA's processing pipeline
3. **Complements TotalSegmentator**: Use TotalSegmentator for 104 labeled structures + SAM2 zero-shot for anything else
4. **Interactive prompting**: Users could click on an anatomical region and SAM2 segments it — perfect for SOMA's interactive exploration
5. **Memory mechanism**: The streaming memory approach (6-frame window) is relevant for rendering optimization

## Pipeline Integration
```
Current: DICOM → TotalSegmentator → VTK Marching Cubes → glTF → Three.js
Enhanced: DICOM → TotalSegmentator (104 structures)
                  → SAM2 zero-shot (interactive, arbitrary structures)
                  → VTK Marching Cubes → glTF → Three.js/WebGPU
```

## Also Notable: TotalSegmentator MRI
- **TotalSegmentator MRI**: Now supports robust sequence-independent MRI segmentation
- Published in Radiology (RSNA) — clinical validation
- Extends beyond CT to MRI — critical for SOMA's multi-modality support

## Action Items
1. Evaluate SAM2 zero-shot performance vs TotalSegmentator on same data
2. Prototype interactive segmentation UI (click → segment)
3. Integrate SAM2 into SOMA's processing pipeline as fallback/interactive tool
4. Monitor SAM2's memory mechanism for rendering optimization ideas


## Sources

- https://arxiv.org/html/2603.23116v1
- https://pubs.rsna.org/doi/10.1148/radiol.241613
