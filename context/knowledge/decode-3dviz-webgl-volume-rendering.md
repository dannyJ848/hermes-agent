# DECODE-3DViz WebGL Volume Rendering

*Researched: 2026-04-06 18:34 CDT*

# DECODE-3DViz: Efficient WebGL-Based High-Fidelity Visualization

**Source:** J Imaging Inform Med. 2025 Feb 14;38(6):4148–4166. PMC12701164.
**GitHub:** https://github.com/mohammed-abo-arab/3D_WebGL_VolumeRendering

## Key Techniques for SOMA
1. **Level of Detail (LOD)** — Progressive detail loading for large volumetric datasets. Critical for mobile where GPU memory is limited.
2. **Data Chunk Streaming** — Streams volume data in chunks rather than loading entire dataset. Enables visualization of multi-GB CT/MRI scans in browser.
3. **WebGL-based** — Runs in browser without plugins. SOMA could adopt similar chunking for anatomy atlas data.
4. **Application domain:** Peripheral artery disease imaging, but techniques generalize to any volumetric medical data.

## Relevance to SOMA
- SOMA's 3D anatomy viewer currently loads full GLB meshes. Adopting LOD + chunk streaming would improve mobile performance dramatically.
- The open-source repo provides reference implementation for WebGL volume rendering with ray marching.
- Potential integration: Use LOD for anatomy models (high-detail when zoomed in, low-detail for overview).
- Data chunk streaming pattern could be adapted for progressive anatomy model loading on mobile Safari/WKWebView.

## Authors
AboArab et al., University of Ioannina, AGH University Krakow, MedApp S.A, University of Belgrade.

## Sources

- https://pmc.ncbi.nlm.nih.gov/articles/PMC12701164/
- https://github.com/mohammed-abo-arab/3D_WebGL_VolumeRendering
