# webgpu-volume-rendering-medical-2026

*Researched: 2026-04-05 22:32 CDT*

# WebGPU & WebGL Volume Rendering for Medical Imaging (2025-2026)

## Key Finding: 4D Cardiac Visualization Pipeline (Hao et al., FIMH 2025)

Three open-source tools for 4D cardiac image workflows:

### 1. Scherzo — Fast Web-Based 4D Model Generation & Visualization
- Web-based tool for generating and visualizing 4D cardiac models
- Directly relevant to SOMA: proves web-based 4D medical visualization is production-viable
- Could inform SOMA's animated anatomy (beating heart, joint articulation)

### 2. ITK-SNAP 4 — 4D Image I/O, Visualization, Segmentation
- Natively supports 4D image formats
- Open-source, handles common 4D cardiac image formats
- Potential tool for SOMA's medical data pipeline (DICOM/NIfTI → 4D meshes)

### 3. Greedy Propagation — Intra-Series Registration
- Creates 4D segmentation from sparse 3D segmentations
- Registration-based propagation across time frames
- Could automate SOMA's mesh generation from medical scans

## DECODE-3DViz (ScienceDirect 2025)
- WebGL-powered 3D visualization framework for medical imaging datasets
- Interactive volume rendering of medical imaging data
- Cloud-based platform for noninvasive diagnostics
- Relevant: proves WebGL volume rendering is mature enough for clinical use

## WebGPU Volume Rendering Framework (MDPI Applied Sciences 2025)
- WebGPU-based volume rendering framework for interactive scalar data visualization
- Published at MDPI Appl. Sci. 2025, 15(5), 2782
- Demonstrates WebGPU's superiority over WebGL for compute-heavy volume rendering
- Key for SOMA: WebGPU enables ray-marching volume rendering in browser

## WebGPU Client-Side AI for Dermatology (ResearchGate, Feb 2026)
- WebGPU-accelerated client-side AI for privacy-preserving diagnostics
- Performance benchmarking with local differential privacy
- Relevant: proves WebGPU can handle both rendering AND inference on same page

## SOMA Architecture Implications
1. **Volume rendering**: WebGPU ray-marching could replace mesh-only approach for organ cross-sections
2. **4D animation**: Scherzo's approach to web-based 4D models maps directly to SOMA's animated anatomy goals
3. **Medical data pipeline**: ITK-SNAP 4 + Greedy = potential automation for DICOM → mesh conversion
4. **Performance**: WebGPU compute shaders handle both rendering and AI inference — single pipeline possible
5. **Privacy**: Client-side processing via WebGPU enables SOMA to run without sending medical data to servers


## Sources

- https://pmc.ncbi.nlm.nih.gov/articles/PMC12885243/
- https://www.mdpi.com/2076-3417/15/5/2782
- https://www.sciencedirect.com/science/article/pii/S0169260725004547
- https://www.researchgate.net/publication/401110730
