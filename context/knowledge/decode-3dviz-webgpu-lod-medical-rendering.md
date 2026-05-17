# DECODE-3DViz WebGPU LOD Medical Rendering

*Researched: 2026-04-06 15:19 CDT*

# DECODE-3DViz: Efficient WebGL Medical Visualization with LOD + Chunk Streaming

**Source:** AboArab et al., J Imaging Inform Med (2025) - Open Access
**URL:** https://link.springer.com/article/10.1007/s10278-025-01430-9
**GitHub:** https://github.com/mohammed-abo-arab/3D_WebGL_VolumeRendering.git

## Key Results
- **98% reduction in rendering time** vs competitors
- **144 FPS** achievable on desktop
- **2.6 MB GPU memory** vs 100+ MB in other tools
- Uses progressive chunk streaming + Level of Detail (LOD) algorithms
- Manages WebGL texture size constraints and browser memory limits

## Techniques Relevant to SOMA
1. **Progressive Chunk Streaming:** Load mesh/texture data in chunks on demand rather than all at once. Critical for mobile.
2. **LOD Algorithms:** Dynamically adjust mesh detail based on camera distance. Essential for anatomy models with 100k+ triangles.
3. **Texture Size Management:** WebGL texture size constraints handled gracefully — applicable to Three.js/WebGPU.
4. **Volume Rendering Pipeline:** CT/MRI volumetric data rendered efficiently in browser.

## SOMA Integration Ideas
- Apply LOD to SOMA's GLB anatomy models (currently loaded at full detail)
- Implement chunk streaming for large anatomy datasets (body > organ > tissue detail)
- Texture compression pipeline could reduce mobile GPU usage from current levels
- The open-source repo provides a reference implementation for volume rendering

## Citation
AboArab MA, Potsika VT, Skalski A, et al. "DECODE-3DViz: Efficient WebGL-Based High-Fidelity Visualization of Large-Scale Images using Level of Detail and Data Chunk Streaming." J Imaging Inform Med. 2025;38:4148-4166.


## Sources

- https://link.springer.com/article/10.1007/s10278-025-01430-9
- https://github.com/mohammed-abo-arab/3D_WebGL_VolumeRendering.git
