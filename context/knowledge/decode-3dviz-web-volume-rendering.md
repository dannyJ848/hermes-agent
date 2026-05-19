# DECODE-3DViz Web Volume Rendering

*Researched: 2026-04-05 12:16 CDT*

# DECODE-3DViz: Efficient WebGL-Based High-Fidelity Visualization

**Source:** Journal of Imaging Informatics in Medicine, Vol 38, Feb 2025 (Open Access)
**Authors:** AboArab et al.
**GitHub:** https://github.com/mohammed-abo-arab/3D_WebGL_VolumeRendering.git

## Key Results
- Progressive chunk streaming + LOD algorithms for large-scale medical volume rendering in WebGL
- **98% reduction in rendering time** vs state-of-the-art competitors
- **144 FPS** real-time performance
- **2.6 MB GPU memory** on desktop (vs 100+ MB required by other tools)
- Applied to peripheral artery CT images but technique is generalizable

## Relevance to SOMA
- Same WebGL constraints we face (texture size limits, browser memory)
- LOD approach directly applicable to our anatomy mesh rendering
- Chunk streaming pattern could optimize SOMA's glTF loading
- Open source — can study their WebGL texture management code
- LOD algorithm could reduce triangle budgets for mobile iOS rendering

## Techniques to Investigate
1. Progressive chunk streaming — how they partition volumetric data
2. LOD implementation details — distance-based mesh simplification
3. WebGL texture constraint management — how they stay under 2.6MB
4. Transfer function design for medical tissue differentiation


## Sources

- https://link.springer.com/article/10.1007/s10278-025-01430-9
- https://github.com/mohammed-abo-arab/3D_WebGL_VolumeRendering
