# webgpu-medical-3d-visualization-2026

*Researched: 2026-04-05 13:40 CDT*

# WebGPU & Web-Based Medical 3D Visualization (2025-2026)

## Key Tools & Papers

### Scherzo — Web-Based 4D Cardiac Visualization
- Open-source tool from UPenn for fast web-based 4D model generation and visualization
- Part of a trio: ITK-SNAP 4 (4D I/O/segmentation), Greedy Propagation (intra-series registration), Scherzo (web viz)
- Natively handles time-series cardiac image data — no need to manually split into 3D frames
- **SOMA relevance:** Directly applicable architecture for SOMA's web-based anatomy viewer. Scherzo proves web-based medical 3D is production-viable.
- Source: Hao et al. "Streamlining 4D Cardiac Image Workflows" (Funct Imaging Model Heart, 2025) PMC12885243

### WebGPU Volume Rendering Framework
- MDPI Applied Sciences paper proposes WebGPU-based volume rendering for interactive visualization of scalar data
- Could not access full text (403), but title confirms WebGPU volume rendering is being actively developed for scientific visualization
- **SOMA relevance:** WebGPU volume rendering could replace Three.js raymarching for CT/MRI volume visualization in SOMA

### DECODE Platform — WebGL Medical 3D
- DECODE-3DViz module: WebGL-powered 3D visualization for medical imaging datasets
- Cloud-based platform for noninvasive diagnostics
- Uses interactive volume rendering
- **SOMA relevance:** Reference architecture for how medical imaging platforms structure their web-based 3D viewing

### WebGPU Client-Side AI for Dermatology
- Feb 2026 paper: Uses WebGPU for on-device AI inference for privacy-preserving dermatological diagnostics
- Includes local differential privacy integration
- **SOMA relevance:** Pattern for running AI models client-side in SOMA's iOS app — no server roundtrip needed for basic diagnostics

## Actionable Insights for SOMA
1. **Investigate Scherzo's rendering approach** — if it uses Three.js or raw WebGL/WebGPU, SOMA could adopt similar patterns
2. **WebGPU adoption timeline:** Multiple 2025-2026 papers confirm WebGPU is maturing for medical use. SOMA should plan a WebGPU renderer.
3. **Client-side AI inference:** WebGPU compute shaders enable on-device model inference — useful for SOMA's offline capability requirements


## Sources

- https://pmc.ncbi.nlm.nih.gov/articles/PMC12885243/
- https://www.mdpi.com/2076-3417/15/5/2782
- https://www.sciencedirect.com/science/article/pii/S0169260725004547
- https://www.researchgate.net/publication/401110730
