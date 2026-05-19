# dicom-to-gltf-medical-pipeline-tools-2025

*Researched: 2026-04-05 22:56 CDT*

# DICOM-to-3D Mesh Pipeline Tools for Medical Anatomy (2025)

## Summary
Research into open-source tools and pipelines for converting medical imaging data (DICOM) into 3D mesh formats (STL/glTF) for anatomy visualization. Directly relevant to SOMA's asset pipeline.

## Key Tools Found

### 1. DICOMator (Blender Add-on)
- **URL**: PMC article PMC12738608 (Phys Eng Sci Med, Jul 2025)
- **Direction**: Mesh → Synthetic DICOM (reverse pipeline)
- **Stack**: Python + Blender scripting API
- **Use case**: Generate synthetic CT datasets from 3D mesh objects for training/research
- **Key insight**: Blender's mesh manipulation, animation, and rendering can create semi-realistic synthetic CT data including 4D CT datasets
- **SOMA relevance**: Could be used to generate training data for ML-based anatomy segmentation. Blender integration aligns with SOMA's 3D pipeline.

### 2. DECODE Platform
- **URL**: ScienceDirect S0169260725004547 (2025)
- **Direction**: DICOM/STL → widely-used formats
- **Stack**: Cloud-based, open-source
- **Key feature**: Automated medical imaging transformation pipeline for seamless DICOM and STL data conversion
- **SOMA relevance**: Direct pipeline for converting medical scan data into web-viewable formats

### 3. democratiz3D (embodi3D)
- **Direction**: DICOM → STL (online tool)
- **Key feature**: Free, user-friendly, no expertise required
- **Limitation**: Cloud-based, may not suit batch processing

### 4. 3D Slicer (Kitware)
- **Direction**: Full DICOM → segmentation → STL/glTF pipeline
- **Stack**: C++/Python, desktop application
- **Key feature**: Industry standard for medical image computing
- **SOMA relevance**: Best-established tool for DICOM → mesh conversion. Python-scriptable for automation.

### 5. Galaxy Project Imaging Tutorial
- **URL**: training.galaxyproject.org
- **Direction**: DICOM series → TIFF → 3D anatomical segmentation
- **Stack**: Galaxy workflow framework
- **Key feature**: Reproducible, shareable workflows for medical image processing

## Pipeline Architecture for SOMA

Recommended pipeline for DICOM → glTF:
1. **Input**: DICOM series (CT/MRI scans)
2. **Segmentation**: 3D Slicer or MONAI for tissue classification
3. **Marching Cubes**: Extract isosurface mesh from segmented volume
4. **Mesh Cleanup**: Blender Python API for decimation, smoothing, UV unwrapping
5. **Texture Baking**: Transfer volume rendering colors to mesh textures
6. **glTF Export**: Draco compression, LOD generation, material setup
7. **Web Delivery**: Three.js/WebGPU loading with progressive LOD

## Critical Research Gap
- **STL → glTF** is straightforward (mesh format conversion)
- **DICOM → segmented mesh** is the hard part (requires ML segmentation models)
- **MONAI + 3D Slicer** combination appears most promising for automated pipeline
- BodyParts3D and Z-Anatomy provide pre-segmented anatomy meshes as alternative to running full DICOM segmentation

## Sources
- PMC12738608 (DICOMator paper)
- ScienceDirect S0169260725004547 (DECODE)
- collectiveminds.health (DICOM to STL guide)
- Kitware 3D Slicer documentation


## Sources

- https://pmc.ncbi.nlm.nih.gov/articles/PMC12738608/
- https://www.sciencedirect.com/science/article/pii/S0169260725004547
- https://collectiveminds.health/articles/converting-dicom-to-stl-a-comprehensive-guide-to-methods-and-libraries
- https://training.galaxyproject.org/training-material/topics/imaging/tutorials/dicom-anatomical-3d/tutorial.html
