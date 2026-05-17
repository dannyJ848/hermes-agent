# cinematic-volume-rendering-web-browser-vtkjs

*Researched: 2026-04-06 14:18 CDT*

# Cinematic Volume Rendering in Browser via vtk.js (Kitware)

**Source:** Xu et al. (2022), "Interactive, in-browser cinematic volume rendering of medical images" — PMC10292767

## Key Findings

1. **vtk.js CVR Extensions**: Kitware extended the open-source vtk.js to support cinematic volume rendering (CVR) in-browser and via WebXR. This is the first open-source CVR solution for web.

2. **WebXR Integration**: The implementation supports augmented and virtual reality rendering, aligning with the WebXR standard — relevant for SOMA's potential AR/VR anatomy viewing.

3. **GPU-Accelerated**: Uses WebGL for real-time ray casting with multiple CVR techniques (gradient-based shading, ambient occlusion, color mapping).

4. **Medical Data Support**: Tested on CT and ultrasound volumes — directly applicable to SOMA's DICOM/CT rendering needs.

5. **Performance**: Benchmarked across various CVR algorithms on medical datasets to help developers choose optimal techniques for their use case.

## Relevance to SOMA
- vtk.js is the web visualization toolkit by Kitware (same team behind VolView)
- CVR techniques (ambient occlusion, gradient shading) could enhance SOMA's tissue rendering
- WebXR support aligns with future AR anatomy viewing on iOS/Apple Vision Pro
- Open-source = can study their shader implementations for SSS and volume rendering

## Technical Stack
- vtk.js (JavaScript visualization toolkit)
- WebGL (can be ported to WebGPU)
- WebXR standard for AR/VR
- Ray casting based volume rendering

## Action Items for SOMA
1. Study vtk.js CVR shader code for SSS-like tissue rendering
2. Consider vtk.js as a potential rendering backend alongside Three.js
3. Evaluate WebXR support for SOMA's iOS app via WKWebView


## Sources

- https://pmc.ncbi.nlm.nih.gov/articles/PMC10292767/
