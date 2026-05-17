# webgpu-volview-nvidia-clara-integration-2025

*Researched: 2026-04-11 13:00 CDT*

# VolView + NVIDIA Clara: Browser-Native Medical AI Architecture (2025)

## Kitware VolView Architecture (Nov 2025)
- **Zero-install browser-native** medical imaging platform using WebGPU/WebGL + VTK.js
- **4-layer architecture**: Data Sources → Browser Viewer → Communication Layer → Backend AI Services
- **ITK-WASM** for in-browser DICOM/NIfTI/NRRD/MHA processing via WebAssembly
- Supports **cinematic volume rendering**, MPR, window/level, annotations — all client-side
- AI models deployed as independent REST/WebSocket microservices on NVIDIA GPU infrastructure

## NVIDIA Clara Model Integration (3 capabilities):
1. **Segment** — organ/tissue segmentation from volumetric scans
2. **Generate** — synthetic data generation for training
3. **Reason** — AI-assisted diagnostic reasoning

## Key SOMA Relevance:
- VolView's modular architecture mirrors SOMA's goals: browser-native, zero-install, client-side rendering
- VTK.js + ITK-WASM stack could replace or complement Three.js for medical volume rendering
- WebSocket streaming for AI results → immediate overlay on canvas pattern is directly applicable
- NVIDIA Clara models (open-source) could provide organ segmentation for SOMA's anatomy viewer
- Their approach to decoupled services (viewer evolves independently of models) is the right pattern

## Performance Notes:
- All rendering client-side, no remote rendering needed
- Cinematic volume rendering works in-browser (WebGPU)
- Handles standard radiology workflows at interactive framerates

## Rust + WASM MRI Volume Renderer (Dec 2025)
- Armeet Jatyani built a GPU-accelerated 3D MRI renderer in Rust → WASM
- Ray marching approach using WebGL (not WebGPU due to compat issues)
- Features: trackball rotation, quality slider (step size), opacity control, occupancy grid optimization
- Client-server architecture with axum backend serving HDF5 volumes
- Demonstrates Rust/WASM viability for heavy medical imaging compute in browser


## Sources

- https://www.kitware.com/integrating-nvidia-clara-models-into-volview-a-technical-deep-dive/
- https://armeet.ca/blog/2025/web-mri-volume-renderer-in-rust
