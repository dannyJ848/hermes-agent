# webgl-lod-medical-viz-decode3dviz-2025

*Researched: 2026-04-07 10:26 CDT*

# DECODE-3DViz: WebGL LOD + Chunk Streaming for Medical Visualization (Feb 2025)

**Paper:** Journal of Imaging Informatics in Medicine, Vol 38, pp 4148-4166
**Authors:** AboArab et al.
**Open Source:** https://github.com/mohammed-abo-arab/3D_WebGL_VolumeRendering

## Key Findings
- WebGL-based progressive chunk streaming + LOD for large-scale medical images (CT peripheral arteries)
- 98% reduction in rendering time vs competitors
- Up to 144 FPS sustained frame rate
- GPU memory as low as 2.6 MB desktop (vs 100+ MB competitors)
- User satisfaction 4.3/5 for diagnostic capability
- Handles WebGL texture size constraints and browser memory limits

## SOMA Relevance
- LOD approach directly applicable to SOMA's Three.js/WebGPU anatomy rendering
- Chunk streaming pattern for progressive loading of high-res anatomy meshes
- Memory efficiency techniques critical for mobile (WKWebView)
- Open-source reference implementation to study

## Sources

- https://link.springer.com/article/10.1007/s10278-025-01430-9
