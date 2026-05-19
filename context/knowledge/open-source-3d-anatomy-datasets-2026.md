# open-source-3d-anatomy-datasets-2026

*Researched: 2026-04-03 03:17 CDT*

# Open-Source 3D Anatomy Datasets (2026)

## Primary Datasets

### 1. Open 3D Anatomical Model (AnatomyTOOL / LUMC)
- **URL**: https://anatomytool.org/open3dmodel-about
- **License**: Creative Commons Attribution ShareAlike (CC BY-SA)
- **Origin**: Built on Z-Anatomy → BodyParts3D lineage
- **Team**: Leiden University Medical Center (LUMC) + UMC Utrecht + Maastricht University + KU Leuven + Amsterdam UMC + Radboud UMC + University of Gent
- **What they did**:
  - Remeshed (retopologized) ALL structures from Z-Anatomy to remove hooked surface artifacts
  - Enabled smoother modeling in Blender
  - Built an online interactive viewer for medical education
- **Format**: Blender .blend files (exportable to OBJ/GLB/STL)
- **SOMA Relevance**: HIGHEST PRIORITY. This is the most curated open anatomy dataset. The retopologized meshes from LUMC are production-quality and CC BY-SA licensed. Should be SOMA's primary mesh source.

### 2. Z-Anatomy
- **URL**: https://www.z-anatomy.com/
- **Stats**: 5,000+ 3D anatomical structures, 3,500+ definitions
- **License**: CC BY-SA
- **History**: Modified version of BodyParts3D with retopologized meshes, nerves/vessels as curves, material properties (colors), Python scripts for automation
- **Format**: Blender .blend files
- **Limitation**: Some surface artifacts (addressed by the Open 3D Model project above)

### 3. BodyParts3D (DBCLS Japan)
- **URL**: http://lifesciencedb.jp/bp3d/
- **License**: CC BY-SA
- **Origin**: 2003 Japanese MRI voxel models → 2008 segmented into 382 body parts
- **Format**: OBJ files
- **Limitation**: Lower mesh quality, older segmentation. Best used as reference, not production.

### 4. NIH 3D Print Exchange — Human Reference Atlas Collection
- **URL**: https://3d.nih.gov/collections/hra
- **Content**: Expert-reviewed 3D reference organs for the Human Reference Atlas (HRA)
- **Developed by**: Medical illustrators, approved by organ experts
- **Sub-collections**: Visible Human Female, Visible Human Male
- **Use case**: Tissue registration via Registration User Interface, VR exploration
- **SOMA Relevance**: Good for organ-level reference models. Quality is expert-verified.

### 5. 3D Slicer Community Atlas
- **URL**: https://discourse.slicer.org/t/open-source-human-anatomy-atlas/17734
- **Format**: .blend files (Blender)
- **SOMA Relevance**: Community resource, may have structures not in other datasets

## Recommended Pipeline for SOMA
1. **Primary source**: Open 3D Anatomical Model (AnatomyTOOL) — highest quality, actively curated
2. **Supplementary**: NIH HRA for organ-specific reference models
3. **Gap filling**: Z-Anatomy / BodyParts3D for structures not in AnatomyTOOL
4. **Pipeline**: Blender .blend → glTF/GLB export → Meshopt compression → LOD generation → progressive loading in Three.js/R3F
5. **License compliance**: All CC BY-SA — requires attribution and share-alike, compatible with SOMA's open model


## Sources

- https://anatomytool.org/open3dmodel-about
- https://www.z-anatomy.com/
- http://lifesciencedb.jp/bp3d/
- https://3d.nih.gov/collections/hra
- https://discourse.slicer.org/t/open-source-human-anatomy-atlas/17734
