# volview-clara-integration-architecture

*Researched: 2026-04-05 16:30 CDT*

# Kitware VolView + NVIDIA Clara Integration Architecture

**Source:** Kitware Blog, November 2025
**Authors:** Andinet Enquobahrie, Andrew Howe, Michael Zephyr, Monty Zarrouz, Stephen Aylward

## Key Architecture: 4-Layer Decoupled Design

1. **Data Sources** — PACS, local files (drag-and-drop), cloud buckets. All visualization is client-side, enabling low-latency interactive exploration even with remote data.

2. **Browser-Based Viewer** — TypeScript/Vue frontend, VTK.js for 2D/3D visualization, ITK-WASM for in-browser image processing and DICOM handling. Cinematic volume rendering and radiology tools (window/level, measurements, annotations) run entirely in the browser with no remote rendering.

3. **Communication Layer** — Small API requests + WebSocket subscriptions for AI results. UI stays responsive; model outputs stream back and overlay on image canvas in real-time for review/editing.

4. **Backend AI Services** — Independent microservices for Segment, Generate, Reason. Horizontally scalable on any NVIDIA-enabled GPU infrastructure (single workstation, GPU cluster, managed cloud). New models added via REST/WebSocket endpoint interface.

## Rendering Pipeline
- WebGL **and WebGPU** provide GPU-accelerated browser rendering
- VTK.js powers interactive 2D/3D visualization
- ITK-WASM handles in-browser operations: reading, decoding, resampling, measuring, manipulating medical volumes via WebAssembly
- Supports DICOM, NIfTI, NRRD, MHA formats without plugins/backend

## SOMA Relevance
- **Direct architecture reference:** SOMA's 3D anatomy viewer can adopt the same 4-layer pattern — client-side Three.js/WebGPU rendering + lightweight API for AI services
- **ITK-WASM:** Could be used in SOMA for client-side DICOM/NIfTI processing without a backend
- **WebSocket streaming pattern:** Real-time AI overlay on anatomy models
- **Zero-install approach matches SOMA's mobile-first design philosophy**
- **VTK.js techniques could complement Three.js for medical volume rendering**

## Clara Model Types Integrated
- **Segment:** Tissue/organ segmentation from volumetric data
- **Generate:** Synthetic data generation
- **Reason:** AI-powered diagnostic reasoning over imaging data


## Sources

- https://www.kitware.com/integrating-nvidia-clara-models-into-volview-a-technical-deep-dive/
