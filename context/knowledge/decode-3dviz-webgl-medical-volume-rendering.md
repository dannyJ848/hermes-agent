# decode-3dviz-webgl-medical-volume-rendering

*Researched: 2026-04-07 10:23 CDT*

# DECODE-3DViz: Efficient WebGL Medical Volume Rendering (2025)

## Summary
DECODE-3DViz is an open-source WebGL pipeline for high-fidelity visualization of large-scale medical imaging data, specifically peripheral artery CT images.

## Key Technical Achievements
- **98% reduction in rendering time** compared to competitors
- **144 FPS** sustained frame rate
- **2.6 MB GPU memory** (vs 100+ MB in other tools)
- Progressive chunk streaming + Level of Detail (LOD) algorithms
- Handles WebGL texture size constraints and browser memory limits

## Architecture
1. Progressive data chunk streaming (avoids loading entire volume)
2. LOD algorithms (coarse-to-fine rendering based on camera distance)
3. WebGL-optimized texture management
4. Real-time interaction while streaming

## Relevance to SOMA
- **Directly applicable**: SOMA uses Three.js (which sits atop WebGL) for anatomy rendering
- LOD approach could dramatically improve mobile performance (triangle/texture budget)
- Chunk streaming pattern useful for loading large DICOM/NIfTI datasets
- 2.6 MB GPU memory is achievable even on mobile Safari/WKWebView
- Open source: https://github.com/mohammed-abo-arab/3D_WebGL_VolumeRendering.git

## Action Items for SOMA
1. Study their LOD implementation for mesh simplification
2. Adopt chunk streaming for large anatomy datasets
3. Benchmark SOMA's current GPU memory against their 2.6 MB target
4. Consider progressive loading: coarse anatomy first, detail on zoom

## Citation
AboArab et al., "DECODE-3DViz: Efficient WebGL-Based High-Fidelity Visualization of Large-Scale Images using Level of Detail and Data Chunk Streaming", J Digit Imaging, 2025.


## Sources

- https://link.springer.com/article/10.1007/s10278-025-01430-9
- https://github.com/mohammed-abo-arab/3D_WebGL_VolumeRendering.git
