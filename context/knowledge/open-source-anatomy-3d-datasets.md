# open-source-anatomy-3d-datasets

*Researched: 2026-04-02 18:08 CDT*

# Open-Source 3D Anatomy Datasets for Web Apps

## TL;DR: Z-Anatomy is the Best Foundation for SOMA

### Dataset Comparison

| Dataset | License | Raw Triangles | Texture | GLB Ready? | Mobile Viable? |
|---------|---------|--------------|---------|-----------|---------------|
| **Z-Anatomy** | CC BY-SA 4.0 | 5-10M+ | Vertex colors (0MB) | Needs decimation | ✅ Best option |
| BodyParts3D | CC BY-SA 2.1 JP | 20M+ | None | Needs retopo | ❌ Bad topology |
| Open Anatomy | Research | N/A (volumetric) | N/A | No (.mrml) | ❌ Desktop only |
| Google/Zygote | Commercial | N/A | N/A | No | ❌ Copyrighted |
| VH Dissector | PD (raw data) | N/A | N/A | No | ❌ Months of work |
| NIH 3D Print | CC0/PD | 1M+ | None | Needs decimation | ⚠️ Isolated organs |
| Sketchfab (CC) | CC BY/CC0 | Varies | PBR | Some are | ✅ Already optimized |

### Z-Anatomy Details (Recommended)
- **GitHub**: Active, community-maintained
- **Formats**: `.blend` (native), `.obj`, `.stl`, `.gltf/.glb` available
- **Systems**: Skeletal, Muscular, Respiratory, Digestive, Urinary, Cardiovascular, Lymphatic, Nervous (CNS + PNS), Integumentary
- **Vertex colors only** = zero texture memory overhead
- **Modular**: Can load individual systems independently

### Recommended Asset Pipeline for SOMA
1. **Source**: Download `.blend` from Z-Anatomy
2. **Select**: Isolate needed body system(s) per screen
3. **Decimate**: Blender Modifier → Decimate to ~180K triangles per scene
4. **Export**: `.glb` (Binary glTF) for Three.js/React Three Fiber
5. **Optional**: Add normal maps in Substance Painter for detail without triangles

### Sketchfab CC Models
Hidden gem: Many indie devs publish CC-licensed anatomy models that are already under 50K triangles with PBR textures. Good for individual organs (heart, brain, lung).

### Budget Allocation Strategy (200K total)
- Skeleton: ~60K triangles (structural importance)
- Muscles: ~40K triangles (major groups only)
- Organs: ~30K triangles (heart, lungs, liver, kidneys, stomach, intestines)
- Skin shell: ~20K triangles
- Vessels: ~20K triangles (major arteries/veins)
- Nervous system: ~20K triangles (brain + spinal cord + major nerves)
- Reserve: ~10K triangles (UI overlays, labels)


## Sources

- https://github.com/z-anatomy/z-anatomy
- https://lifesciencedb.jp/bp3d/
- https://www.openanatomy.org/
- https://3dprint.nih.gov/
- https://sketchfab.com/search?q=anatomy&type=models&licenses=322a749bcfa841b29dff1e7a985d9210
