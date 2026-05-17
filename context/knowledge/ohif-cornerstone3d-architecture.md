# ohif-cornerstone3d-architecture

*Researched: 2026-04-05 13:43 CDT*

# OHIF Viewer 3.8 & Cornerstone3D Architecture

## Overview
OHIF Viewer (Open Health Imaging Foundation) is a production-grade, open-source web-based medical imaging platform built on Cornerstone3D. It represents the most mature web-based DICOM viewer ecosystem.

## OHIF Viewer v3.8 Key Features (May 2024)
- **4D Visualization**: Full support for time-series/dynamic imaging data with CINE player. Supports frame rate control, play direction, loop mode.
- **4D PET/CT Mode**: Combines 3D CT + 4D PET in a 9-viewport layout. Supports computed images (sum, subtraction, averaging frames).
- **Per-Viewport Rendering Controls**: Window level presets tailored per viewport data type (CT, MRI, 3D Rendering). Color lookup table selector with in-viewport previews.
- **Enhanced Layout Menu**: Preconfigured layouts (MPR, 3D four up, custom views). Quick switch between grids and advanced 3D layouts.
- **Workflow Steps**: Break complex tasks into stages, showing only relevant tools per step.
- **Advanced Segmentation Tools**: Spline tools, freehand ROI, livewire with magnetic edge snapping, dynamic threshold tool, advanced magnify.

## Cornerstone3D Technical Stack
- **Rendering**: WebGL-based (not yet WebGPU as of 2024). Uses 2D textures for large images via WebGL upgrade.
- **Volume Loader**: `@cornerstonejs/streaming-image-volume-loader` — progressive chunk streaming for volumetric data.
- **Architecture**: Lightweight JavaScript library for medical image visualization on HTML5 canvas.
- **Integration**: Cornerstone3D builds include OHIF checkout linked to current branch for compatibility testing.
- **4D Support**: Dynamic imaging (cardiac, perfusion studies) with smooth frame navigation.

## Relevance to SOMA
1. **Streaming Architecture**: Cornerstone's streaming-image-volume-loader uses progressive chunk loading — same pattern as DECODE-3DViz. SOMA should adopt this for mobile anatomy models.
2. **Per-Viewport Controls**: SOMA's MPR/3D view system should implement similar per-viewport preset management.
3. **Workflow Steps Pattern**: SOMA's guided anatomy exploration could use the same "show relevant tools per step" UX pattern.
4. **WebGL → WebGPU Migration Path**: Cornerstone is still WebGL-based. SOMA can leapfrog by going directly to WebGPU (like Grenzwert) for better compute shader support.
5. **4D/Dynamic Data**: If SOMA adds cardiac anatomy or surgical simulation, Cornerstone's 4D patterns are directly applicable.

## Key Repos
- Cornerstone3D: https://github.com/cornerstonejs/cornerstone3D
- OHIF Viewer: https://github.com/OHIF/Viewers
- Live demo: https://viewer.ohif.org/

## Comparison: SOMA vs OHIF
| Feature | OHIF/Cornerstone | SOMA |
|---------|------------------|------|
| Target | Radiology (DICOM) | Anatomy education |
| Rendering | WebGL | Three.js → WebGPU |
| Data | DICOM (patient scans) | Pre-built anatomy meshes |
| 4D | ✅ (PET/CT, cardiac) | Planned |
| Mobile | Limited (desktop-first) | iOS-first |
| Bilingual | No | EN/ES planned |


## Sources

- https://ohif.org/newsletters/2024-05-01-ohif%20viewer%203.8%20with%204d%20visualization%20and%20volume%20rendering--release-note3p8
- https://cornerstonejs.org/docs/getting-started/overview/
- https://github.com/cornerstonejs/cornerstone3D
