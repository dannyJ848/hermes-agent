# soma-integrated-medical-data-pipeline

*Researched: 2026-04-03 05:47 CDT*

# SOMA Integrated Medical Data Pipeline: DICOM → FHIR → Segmentation → 3D Viewer

## Synthesis of Multiple Research Findings

This document connects three research threads:
1. **FHIR/HL7 integration** (previous session: Medplum, SMART on FHIR, SNOMED-CT)
2. **Medical image segmentation** (this session: TotalSegmentator, MONAI, nnU-Net)
3. **DICOM-to-3D mesh pipeline** (this session: VTK Marching Cubes, glTF export)

## The End-to-End Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    DATA INGESTION LAYER                         │
│                                                                 │
│  Hospital PACS ──── WADO-RS/DICOMweb ────→ FHIR ImagingStudy   │
│  (DICOM files)        (REST API)           (standard resource)  │
│                                                                 │
│  FHIR Server (Medplum recommended)                              │
│  ├── Patient resources (demographics)                           │
│  ├── ImagingStudy (metadata, series, instance refs)             │
│  ├── Observation (lab results, vitals)                          │
│  └── Condition (diagnoses, SNOMED-CT coded)                    │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                  SEGMENTATION PIPELINE                           │
│                                                                 │
│  DICOM Series ──→ TotalSegmentator ──→ 104 Structure Masks     │
│                    (nnU-Net v2)          (NIfTI format)          │
│                                                                 │
│  OR: Custom MONAI pipeline for extended structures              │
│  OR: MedSAM2 for interactive/few-shot segmentation             │
│                                                                 │
│  Output: Per-structure binary masks (27 organs, 59 bones,       │
│          10 muscles, 8 vessels)                                 │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                  MESH GENERATION PIPELINE                        │
│                                                                 │
│  NIfTI Masks ──→ VTK Marching Cubes ──→ Raw Triangle Meshes    │
│                  (isosurface)              (.obj format)         │
│                                                                 │
│  Raw Meshes ──→ gltf-transform ──→ Optimized GLB                │
│                  (draco compression,     (per-structure)         │
│   LOD generation, decimation)                                   │
│                                                                 │
│  Alternative: 3D Slicer Open Anatomy → direct glTF export       │
│               (includes hierarchy, colors, PBR materials)       │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                  SOMA RENDERING LAYER                            │
│                                                                 │
│  GLB Models ──→ Three.js/WebGPU Scene Graph                     │
│                  ├── Subsurface scattering (SSS) shaders         │
│                  ├── LOD system (mobile: 50K tri, desktop: 500K)│
│                  ├── Interactive cross-sections                  │
│                  ├── EN/ES bilingual labels (SNOMED-CT mapped)  │
│                  └── Medical encyclopedia overlay                │
│                                                                 │
│  Connected to:                                                  │
│  ├── FHIR Patient context (demographics, conditions)            │
│  ├── SNOMED-CT terminology (EN/ES bilingual mapping)            │
│  └── Education content (encyclopedia, clinical notes)           │
└─────────────────────────────────────────────────────────────────┘
```

## Key Integration Points

### 1. FHIR ImagingStudy ↔ DICOM
- **FHIR ImagingStudy resource** provides metadata and references to DICOM series
- **WADO-RS** (DICOMweb) retrieves actual pixel data via RESTful URLs
- **OMI (Open Medical Inference)** defines FHIR endpoints for DICOMweb-enabled PACS
- **Mayo Clinic + Google Cloud** building production pipeline (DevDays 2024)
- **FLUTE project** (EU) profiles ImagingStudy for research linkage
- For SOMA: Medplum server acts as FHIR facade, DICOMweb bridge fetches imaging data

### 2. DICOM → Segmentation
- **TotalSegmentator** operates on DICOM/NIfTI input directly
- Outputs 104 binary masks in NIfTI format (one per anatomical structure)
- Supports both CT and MR (separate models, 616 MR training subjects)
- **Quality control:** Use 3D Slicer with TotalSegmentator extension for manual refinement
- For SOMA: Run TotalSegmentator as a preprocessing step on curated CT datasets

### 3. Segmentation → 3D Mesh
- **VTK Marching Cubes** is the standard algorithm (marching cubes on binary mask → triangle mesh)
- **3D Slicer Open Anatomy** provides direct glTF export with:
  - Segment names and hierarchy
  - PBR material properties (color, opacity)
  - Coordinate system alignment
- **Caveat:** Thin structures (vessels, bronchi) need special handling:
  - Higher marching-cubes resolution for small features
  - Depth-sorted transparency in renderer
  - Separate render passes for opaque vs. transparent structures

### 4. Mesh → SOMA Viewer
- **Optimization pipeline:** Raw mesh → decimation → Draco compression → LOD hierarchy
- **Mobile targets:** ≤50K triangles per visible structure, LOD switching at distance
- **SSS shaders:** Native GLSL for tissue translucency (organs, skin)
- **Bilingual labels:** SNOMED-CT mapped EN/ES terminology via xMEN cross-lingual normalization

## FHIR Binding Strategy (from previous research)

Each anatomical structure in SOMA maps to:
- **SNOMED-CT code** (universal medical identifier)
- **FHIR BodyStructure resource** (formal reference to body site)
- **Bilingual label** (EN/ES via SNOMED-CT Spanish Edition, May 2025 release)

Example mapping:
```
TotalSegmentator label: "liver" 
  → SNOMED-CT: 10200004 (Liver structure)
  → FHIR BodyStructure: { location: { coding: [{ system: "http://snomed.info/sct", code: "10200004" }] } }
  → EN label: "Liver"
  → ES label: "Hígado"
  → glTF node: "liver_mesh"
```

## Research Gaps & Next Steps

1. **DICOMweb → TotalSegmentator** direct integration — currently requires NIfTI conversion step
2. **FHIR ImagingSelection** resource (R4B/R5) for referencing segmentation regions within studies
3. **AI-assisted labeling** — MONAI Label for interactive refinement by anatomy educators
4. **Quality metrics** — Dice coefficient benchmarks for TotalSegmentator on educational-quality CT data
5. **MAISI synthetic data** — MONAI's latent diffusion model could generate training CT data with known ground truth

## Sources
- TotalSegmentator: wasserth/TotalSegmentator (Radiology AI 2022)
- nnU-Net Revisited: arXiv:2404.09556 (MICCAI 2024)
- MONAI: project-monai.github.io
- DICOM→FHIR pipeline: PMC12133321 (Methods Inf Med 2025)
- 3D Slicer Open Anatomy: discourse.slicer.org
- FHIR/HL7 research: Previous session finding (Medplum, SMART on FHIR, SNOMED-CT)
- Bilingual NLP: Previous session finding (xMEN, SNOMED-CT Spanish Edition)


## Sources

- https://github.com/wasserth/TotalSegmentator
- https://pmc.ncbi.nlm.nih.gov/articles/PMC12133321/
- https://discourse.slicer.org/t/open-anatomy-export-in-gltf-format/34819
- https://project-monai.github.io/
- https://arxiv.org/abs/2404.09556
