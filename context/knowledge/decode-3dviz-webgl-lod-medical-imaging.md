# DECODE-3DViz WebGL LOD Medical Imaging

*Researched: 2026-04-05 18:16 CDT*

# DECODE-3DViz: WebGL LOD for Medical 3D Visualization (2025)

**Paper:** AboArab et al., "DECODE-3DViz: Efficient WebGL-Based High-Fidelity Visualization of Large-Scale Images using Level of Detail and Data Chunk Streaming" — J Imaging Inform Med, 2025.

**Key Innovation:** A pipeline combining LOD (Level of Detail) with data chunk streaming for web-based medical imaging. Targets peripheral artery CT visualization via WebGL.

**SOMA Relevance:**
- Uses LOD algorithm for detailed artery rendering within anatomical context — directly applicable to SOMA's anatomy model loading
- WebGL-based (compatible with Three.js / our stack)
- Handles large-scale volumetric datasets efficiently — critical for SOMA's high-poly anatomy models on mobile
- Data chunk streaming pattern could improve SOMA's asset loading on slow connections

**Key Techniques:**
- LOD with progressive detail levels for medical structures
- Chunk-based data streaming to avoid loading entire datasets at once
- High-fidelity preservation at close range, simplified at distance
- Optimized for WebGL constraints (no native GPU compute)

**Implementation Insight for SOMA:**
- Three.js LOD component (`THREE.LOD`) can be used directly — assign different geometry resolutions per distance threshold
- For anatomy models: 3 LOD levels recommended (high/close, medium/mid, far/low-poly)
- Chunk streaming could be implemented via Three.js `LoadingManager` + progressive GLB loading
- Mobile WKWebView: keep triangle budget under 500K total across all visible objects with LOD active

**Three.js LOD Pattern:**
```javascript
const lod = new THREE.LOD();
lod.addLevel(highPolyMesh, 0);    // 0-5m: full detail
lod.addLevel(midPolyMesh, 50);    // 5-15m: reduced
lod.addLevel(lowPolyMesh, 150);   // 15m+: minimal
scene.add(lod);
```

**Sources:** PMC12701164, Three.js Discourse LOD discussions

## Sources

- https://pmc.ncbi.nlm.nih.gov/articles/PMC12701164/
- https://discourse.threejs.org/t/when-is-it-actually-beneficial-to-use-lod-in-three-js-for-performance/87697
- https://threejs.org/docs/pages/LOD.html
