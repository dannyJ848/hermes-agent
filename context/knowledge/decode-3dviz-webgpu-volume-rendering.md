# DECODE-3DViz WebGPU Volume Rendering

*Researched: 2026-04-05 13:13 CDT*

# DECODE-3DViz: WebGL Volume Rendering with LOD & Chunk Streaming

**Source:** Springer - Journal of Imaging Informatics in Medicine (Feb 2025)
**Open Source:** https://github.com/mohammed-abo-arab/3D_WebGL_VolumeRendering.git

## Key Results
- **98% reduction in rendering time** vs competitors
- **Up to 144 FPS** on desktop with large-scale CT data
- **GPU memory: as low as 2.6MB** (vs 100MB+ for other tools)
- User satisfaction: 4.3/5 average

## Techniques (applicable to SOMA)
1. **Progressive chunk streaming** — loads volumetric data in chunks instead of all at once, critical for mobile
2. **Level of Detail (LOD) algorithms** — reduces triangle/texture complexity at distance
3. **WebGL texture size constraint management** — handles browser memory limits gracefully
4. **Applied to peripheral artery CT** — similar vascular anatomy to what SOMA renders

## SOMA Integration Ideas
- Adapt LOD system for SOMA's anatomy models (reduce poly count for distant structures)
- Use chunk streaming for loading large DICOM datasets progressively
- The 2.6MB GPU footprint pattern could help SOMA run on low-end iOS devices
- Progressive loading = better perceived performance on mobile

## Citation
AboArab et al., "DECODE-3DViz: Efficient WebGL-Based High-Fidelity Visualization of Large-Scale Images using Level of Detail and Data Chunk Streaming," J Imaging Inform Med, vol. 38, pp. 4148–4166, 2025.


## Sources

- https://link.springer.com/article/10.1007/s10278-025-01430-9
- https://github.com/mohammed-abo-arab/3D_WebGL_VolumeRendering.git
