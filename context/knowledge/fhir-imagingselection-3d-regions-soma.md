# fhir-imagingselection-3d-regions-soma

*Researched: 2026-04-05 13:22 CDT*

# FHIR ImagingSelection Resource for 3D Medical Imaging Regions

**Source:** HL7 FHIR v6.0.0-ballot4 (CI Build, R6)
**Date:** 2026-04-05
**Relevance:** SOMA architecture — linking 3D anatomy models to clinical imaging data

## Key Finding

FHIR R6 introduces **ImagingSelection**, a resource for selecting subsets of DICOM imaging data. Critically, it supports:

### 3D Region Support
- **3D regions within a DICOM Frame of Reference** — this means FHIR can natively reference volumetric spatial regions, not just 2D image slices
- **Segments within DICOM segmentation SOP Instances** — anatomical segmentations (organs, tissues) are first-class FHIR citizens

### Capabilities Relevant to SOMA
1. **2D regions** within DICOM image SOP Instances
2. **3D regions** within a DICOM Frame of Reference
3. **Frames** within multiframe image SOP Instances
4. **Segments** within DICOM segmentation SOP Instances
5. **Content items** within DICOM Structured Report SOP Instances

### Workflow Integration
- `Observation.derivedFrom` references an `ImagingSelection` when it relates to an identified imaging subset
- `Observation.partOf` references an `ImagingStudy` for full study context
- Multiple `ImagingSelection` resources needed for cross-series/cross-study references

### SOMA Integration Path
1. **SOMA's 3D anatomy models** can be registered to DICOM Frames of Reference
2. **Anatomical regions clicked in SOMA** could generate `ImagingSelection` resources pointing to corresponding DICOM image regions
3. **Bilingual medical terms** in SOMA can link to `Observation` resources via `derivedFrom` → `ImagingSelection`
4. **FHIR server** (e.g., Medplum, HAPI) as backend would allow SOMA to query patient imaging data and overlay anatomy

### Related Standard
- PMC paper (Tang et al., J Digit Imaging 2023) demonstrates web-based FHIR + DICOMweb + SVG workflow for medical image annotation — proves browser-based medical imaging pipeline is viable
- `ImagingStudy` resource stores full DICOM study metadata; `ImagingSelection` references subsets

### Next Steps for SOMA
- Evaluate Medplum as FHIR backend (open-source, TypeScript SDK)
- Design mapping: SOMA anatomy node → DICOM Frame of Reference UID → ImagingSelection 3D region
- Test with DICOM SEG files from open datasets (TCIA, MIMIC-CXR)


## Sources

- https://build.fhir.org/imagingselection.html
- https://pmc.ncbi.nlm.nih.gov/articles/PMC10287854/
