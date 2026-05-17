# webgpu-volumetric-medical-rendering-techniques

*Researched: 2026-04-05 16:25 CDT*

# WebGPU Volumetric Medical Imaging: State of the Art (2025-2026)

## 1. GPU Path Tracing for CT Volumes (grenzwert.net, 2025)

**Source:** Hacker News Show HN (MickGorobets, ~Feb 2026)

A real-time GPU path tracer for volumetric medical data running entirely in Chrome via WebGPU + WebAssembly (C++/Emscripten).

### Key Technical Details:
- **Delta tracking (Woodcock null-collision algorithm)** for unbiased volume rendering
- **Cook-Torrance GGX BRDF** + **Henyey-Greenstein phase function** for light scattering
- **MacroGrid acceleration**: DDA empty-space skipping + GPU tile culling
- **Progressive frame accumulation**: noisy at first, converges to ground truth
- **HDR pipeline**: bloom, auto-exposure, PBR Neutral / ACES tone mapping
- **Async mip-level streaming** with gzip decompression
- Built on **Diligent Engine** (contributed WebGPU backend)
- Chrome-only (WebGPU), works on discrete and integrated GPUs

### SOMA Relevance:
- Delta tracking + Henyey-Greenstein phase function could dramatically improve subsurface scattering in anatomical rendering
- MacroGrid empty-space skipping is relevant for optimizing large DICOM volumes
- Mip-level streaming pattern could be adapted for SOMA's asset pipeline

## 2. Cinematic Volume Rendering in vtk.js (Kitware, 2022-2024)

**Source:** PMC10292767, Comput Methods Biomech Biomed Eng Imaging Vis

Kitware's open-source CVR (Cinematic Volume Rendering) extensions to vtk.js with WebXR support.

### Key Points:
- First open-source CVR solution for in-browser + WebXR rendering
- Built on vtk.js (VTK rewritten in JavaScript)
- Benchmarked speed and quality of various CVR techniques on medical data
- Targets WebXR standard for medical AR/VR applications
- Foundation for digital twin and surgical simulation

### SOMA Relevance:
- vtk.js is a mature, actively maintained library that SOMA could leverage for DICOM/volume rendering
- WebXR integration path exists for future AR anatomy education features
- Open-source licensing makes it viable for SOMA's stack

## 3. Real-Time Volumetric CBCT for Anatomy Learning (ResearchGate, 2025)

Craniofacial cone-beam CT volumetric visualization as simulation framework for radiographic anatomy learning — directly aligned with SOMA's educational use case.


## Sources

- https://news.ycombinator.com/item?id=46933474
- https://pmc.ncbi.nlm.nih.gov/articles/PMC10292767/
- https://www.researchgate.net/publication/393563051_Real-Time_Volumetric_Visualisations_of_Cone-Beam_Computed_Tomography_Scans_as_a_Simulation_Framework_for_Radiographic_Anatomy_Learning
