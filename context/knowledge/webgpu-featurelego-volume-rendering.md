# webgpu-featurelego-volume-rendering

*Researched: 2026-04-05 16:28 CDT*

# FeatureLego: WebGPU Volume Rendering with Super-Voxel Clustering

**Source:** TU Wien Visualization 2 course project (2025/2026)
**URL:** https://www.cg.tuwien.ac.at/courses/Vis2/HallOfFame/2025/visvu-2025-jadhav-goncalves-schiebel-main/website/documentation.html

## What It Does
Implements the FeatureLego framework (Jadhav et al., IEEE TVCG 2019) using modern WebGPU + D3.js for interactive volume exploration. Partitions volumetric datasets into semantic regions ("Legos") that users can interactively select and group.

## Pipeline (4 stages, all in JS + WGSL)
1. **Super-Voxel Generation (SLIC 3D):** Over-segments volume into compact, homogeneous super-voxels. Reduces millions of voxels → thousands of super-voxels (graph nodes).
2. **Exhaustive FH Clustering:** Felzenszwalb-Huttenlocher graph-based clustering with logarithmic parameter scan of k. Identifies stable regions across multiple scales.
3. **Meta-Cluster Tree:** Organizes overlapping regions via Jaccard distance similarity graph → MST via Reverse-Delete → hierarchical meta-clusters.
4. **Linked Views:** WebGPU ray-marcher for 3D + D3.js collapsible tree. Click tree node → highlight region in 3D.

## Key Techniques for SOMA
- **WebGPU ray-marching** with dynamic mask textures for region highlighting
- **SLIC 3D** for anatomy segmentation without pre-labeled data
- **Super-voxel → semantic region pipeline** could auto-segment anatomy from DICOM/NIfTI
- **Linked views pattern** (3D + hierarchical tree) matches SOMA's anatomy tree + 3D viewer

## Datasets Used
Aneurism (256³), Skull (256³), Shockwave (64×64×512) — standard TC18 medical datasets.

## Relevance to SOMA
This is directly applicable to SOMA's 3D anatomy viewer. The super-voxel clustering could enable interactive anatomy exploration where users click anatomical regions and the system auto-segments related structures. The WebGPU ray-marching approach is an alternative to mesh-based rendering for volumetric medical data.

## Reference Paper
S. Jadhav, S. Nadeem, A. Kaufman. "FeatureLego: Volume Exploration Using Exhaustive Clustering of Super-Voxels." IEEE TVCG, vol. 25, no. 09, pp. 2725-2737, Sept. 2019.


## Sources

- https://www.cg.tuwien.ac.at/courses/Vis2/HallOfFame/2025/visvu-2025-jadhav-goncalves-schiebel-main/website/documentation.html
