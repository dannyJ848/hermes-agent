# soma-3d-anatomy-rendering-deep-dive

*Researched: 2026-04-02 15:49 CDT*

# SOMA 3D Anatomy Rendering - Technical Deep Dive

## Subsurface Scattering (SSS)

### Screen-Space SSS vs Pre-Integrated SSS
- **Screen-Space**: Post-process convolution on G-buffer. High quality, 3-4 full-screen passes (~2-3ms on mobile). Requires WebGL2+MRT.
- **Pre-Integrated**: Single LUT texture fetch per pixel. Trivially fast on mobile. Works on WebGL1. Less convincing for extreme scattering.
- **RECOMMENDATION for SOMA**: Pre-integrated SSS as base, optional screen-space pass for hero close-ups on high-end devices.

### Tissue-Specific Shader Patterns
- **Skin**: 3-layer model (epidermis/dermis/subcutaneous). Dual-lobe specular (sebum + rough). Wrap lighting factor ~0.5. Red/orange translucency on thin parts.
- **Muscle**: Shorter scatter distance, anisotropic along fiber direction. Deep red myoglobin scatter. Wet glossy specular (roughness ~0.05). 2 Gaussians sufficient.
- **Organs**: Variable density. Chromatic separation (R scatters furthest, B shortest). Back-transmission for thin regions (red glow). Organ capsule sheen. Density parameter per organ type.
- **Bone**: Nearly opaque, minimal SSS. Yellowish-white subsurface tint from marrow. Short scatter distance.

### KTX2 Compression for SSS Maps
- Use KTX2 for SSS LUTs, curvature maps, thickness maps
- ETC1S for opaque textures, UASTC for normals/curvature
- Pre-integrated LUT only 128x128 — negligible size

## Interactive Cross-Sections / Dissection

### Stencil Buffer Capping
- 3-pass rendering: stencil front (increment) → stencil back (decrement) → cap where stencil != 0
- Must enable `stencil: true` on WebGLRenderer
- Cap geometry = plane matching clip plane orientation, sized to bounding box
- For box clipping: 6 planes, each with own stencil pass pair

### Dual-Depth Inside/Outside
- Custom shader detects proximity to clip boundary
- Distance-to-clip-plane determines interior factor
- Face orientation (front/back facing) distinguishes inside from outside
- Multi-layer coloring based on depth from surface (skin→fat→muscle→bone)

### Layer Peeling
- Vertex shader displacement with per-vertex `peelOrder` attribute
- Curl effect: vertices rotate around peel axis, translate outward
- Canvas-based dissection mask painted by raycaster
- Dissolve shader for gradual layer removal
- InteractiveDissector class: raycaster-driven, shift+click to dissect

## 3D Asset Pipeline

### DICOM/NIfTI → Mesh Pipeline
1. Volume loading (pydicom/nibabel)
2. Isotropic resampling (critical — CT has 0.5mm in-plane but 2-5mm slice spacing)
3. Segmentation by HU thresholds + morphological cleanup
4. Marching cubes surface extraction
5. Quadric error decimation (preserves anatomical features better)
6. LOD chain generation (1.0, 0.3, 0.1 face count ratios)
7. glTF export

### Key HU Ranges (CT)
- Cortical bone: 300-3000 HU
- Cancellous bone: 100-300 HU
- Soft tissue: -100 to 100 HU
- Fat: -120 to -50 HU
- Lungs: -1000 to -500 HU
- Liver: 40-80 HU
- Blood vessels (contrast): 200-500 HU

### Meshopt vs Draco Compression
- Meshopt: GPU-friendly decompression, better for runtime. Works with WebGPU.
- Draco: Better compression ratio but CPU decompression bottleneck.
- For SOMA: Meshopt preferred (better mobile performance).

### Scene Graph Architecture
- Layered anatomy: skin/muscle/bone/vessels/organs/nervous as separate meshes
- Each layer with tissue-appropriate material (SSS params, color, roughness)
- Raycaster picking for organ selection
- Progressive loading: LOD0 visible immediately, higher LODs stream in
- Proactive disposal: geometry.dispose() + material.dispose() on layer toggle
- iOS WKWebView: 350MB hard memory limit — must dispose aggressively

### Performance Budget
- Target: 30 FPS on mobile
- <100 draw calls, <200K triangles, <200MB GPU memory
- LOD system critical: distant anatomy at 10% triangle count
- Texture streaming: KTX2 with Basis universal transcoding


## Sources

- delegated research via GLM-5.1
