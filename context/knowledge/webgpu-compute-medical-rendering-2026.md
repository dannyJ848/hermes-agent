# webgpu-compute-medical-rendering-2026

*Researched: 2026-04-05 13:58 CDT*

# WebGPU Compute Shaders for Medical/Scientific Volume Rendering (2026)

## Key Finding: Mol* Viewer Adopts WebGPU Compute

**Source:** Rose et al. (2026) "Mol* web molecular graphics engine" — Protein Science journal.

Mol*, the leading web-based molecular graphics engine (used by RCSB PDB), has integrated WebGPU compute shaders for three critical GPU-side operations:

1. **Gaussian-density accumulation** — Building volumetric density fields from atomic Gaussian distributions, entirely on GPU
2. **Marching cubes isosurface extraction** — Generating triangle meshes from volumetric data via classic marching cubes, now GPU-accelerated
3. **Volumetric smoothing** — Applying spatial filters to volume data for cleaner visualizations

### Relevance to SOMA
These three GPU compute functions map directly to SOMA's 3D anatomy rendering needs:
- **Gaussian-density accumulation**: Could generate smooth tissue boundary volumes from DICOM/segmentation data
- **Marching cubes isosurface**: Already used in SOMA's asset pipeline (SomaAssetPipeline skill) — could move from offline to real-time browser-side generation
- **Volumetric smoothing**: Essential for making anatomical surfaces look natural rather than blocky

### Technical Implications
- WebGPU compute shaders run **in-browser** — no server-side rendering needed
- Enables real-time volume manipulation (cutting planes, cross-sections) with GPU-side mesh regeneration
- Workgroup/thread dispatch model allows parallelizing across GPU cores efficiently

### Additional Sources
- MDPI Applied Sciences (2026): WebGPU volume rendering framework for interactive ocean scalar data visualization — demonstrates general-purpose WebGPU volume rendering pipeline
- Patel (2026): WebGPU-accelerated client-side AI for dermatological diagnostics — shows WebGPU compute shaders used for on-device medical AI inference (privacy-preserving)
- Chrome Developers blog: WebGPU unlocks modern GPU access including compute pipelines in browser

### Action Items for SOMA
1. Investigate Mol*'s WebGPU implementation (open-source on GitHub: molstar/molstar)
2. Evaluate replacing offline marching-cubes with real-time WebGPU compute version
3. Prototype WebGPU-based volume rendering for cross-section/dissection features
4. Monitor WebGPU browser support stability (Chrome stable, Firefox experimental, Safari TP)


## Sources

- https://onlinelibrary.wiley.com/doi/10.1002/pro.70514
- https://www.mdpi.com/2076-3417/15/5/2782
- https://developer.chrome.com/blog/webgpu-io2023
