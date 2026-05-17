# soma-3d-anatomy-models-sources

*Researched: 2026-04-02 16:23 CDT*

# 3D Anatomy Model Sources for SOMA

## Best Options (Open Source, Web-Ready)

### Z-Anatomy (RECOMMENDED)
- URL: https://z-anatomy.com/ (GitHub available)
- License: CC-BY 4.0
- Format: Native glTF/GLB (Three.js ready)
- Poly count: ~1M total (pre-optimized for web)
- Layers: 150+ structures
- **Verdict: Start here. Saves 6 months of mesh decimation.**

### BodyParts3D (Most Complete)
- URL: https://dbcls.rois.ac.jp/en/ (DBCLS Japan)
- License: CC-BY-SA 2.1
- Format: OBJ (needs conversion to GLB)
- Poly count: 10M+ total (needs aggressive decimation)
- Layers: 2,000+ structures
- **Requires Blender pipeline to decimate + convert to glTF**

### OpenAnatomy
- URL: https://www.openanatomy.org/
- License: CC-BY / CC0
- Format: VTK/STL (needs conversion)
- Poly count: 1M-5M
- Layers: 100-400 structures

## Commercial (NOT open-source compatible)
- **Complete Anatomy (3D4Medical/Elsevier)**: Proprietary SDK, $10K+/year, forbids open-source use
- **Zygote Body**: Strictly commercial, no OSS licensing

## Pipeline Recommendation
1. Base assets: Z-Anatomy for immediate use, BodyParts3D for completeness
2. Conversion: Blender Python scripts for OBJ→GLB with decimation
3. Three.js: MeshPhysicalMaterial with transmission for skin, LOD groups for layers


## Sources

- https://z-anatomy.com/
- https://dbcls.rois.ac.jp/en/
- https://www.openanatomy.org/
