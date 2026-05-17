# fhir-dicom-3d-anatomy-integration-ivms

*Researched: 2026-04-05 12:32 CDT*

# FHIR + DICOM 3D Anatomical Atlas Integration: I-VMS Case Study

**Date:** 2025-11-24 (HL7 Blog, Robert Lario PhD)
**Source:** AI-Conformable Venous Atlas — Overall Winner of HL7 AI Challenge

## What It Does
The I-VMS (Integrated Medical Management and Educational Gateway Venous Management System) projects a **vectorized atlas of the deep thoracic venous system** onto routine chest radiographs using:
1. **Deep learning landmark detection** — Modified DenseNet121 via MONAI framework predicts anatomical landmarks (carina, T1 vertebra, right rib edge)
2. **Affine transformation** — Landmarks establish patient-specific basis for overlaying a standardized vector-based venous atlas
3. **FHIR/DICOM interoperability** — Annotations stored in normalized coordinate space
4. **Longitudinal tracking** — Normalized coordinates enable comparison across encounters

## Relevance to SOMA
- **Architecture pattern**: This validates SOMA's approach of combining 3D anatomical models with standardized medical data formats
- **Coordinate normalization**: I-VMS uses normalized coordinate spaces for cross-encounter comparison — SOMA should adopt this for anatomy labeling
- **MONAI integration**: DenseNet121 for landmark detection — same MONAI framework SOMA uses for DICOM processing
- **FHIR storage**: Annotations stored via FHIR resources — SOMA could export anatomy session data as FHIR ImagingStudy resources
- **Vector-based atlases**: I-VMS uses vector (not raster) anatomy — aligns with SOMA's glTF mesh approach

## Technical Details
- **AI Model**: Modified DenseNet121, implemented in MONAI
- **Standards**: HL7 FHIR + DICOM
- **Use Case**: Central venous access (chemotherapy, dialysis, critical care)
- **Developer**: Xzyos.ai for Vanguard

## Action Items for SOMA
1. Investigate FHIR ImagingStudy resource for storing 3D anatomy session data
2. Consider normalized coordinate space for anatomy labels (cross-session persistence)
3. Evaluate MONAI DenseNet121 for anatomy landmark detection in SOMA's DICOM pipeline
4. Research vector-based anatomical atlas formats compatible with glTF

## Sources

- https://blog.hl7.org/topic/dicom
