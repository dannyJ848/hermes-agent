# sss-shader-techniques-webgl-threejs

*Researched: 2026-04-06 03:59 CDT*

# Real-Time Subsurface Scattering Techniques for WebGL/Three.js

## Key Techniques for SOMA Anatomy Rendering

### 1. Frostbite Approximate Translucency (GDC 2011, Barré-Brisebois & Bouchard)
- **Source**: Used in Battlefield 3 (Frostbite 2 engine)
- **Approach**: Wrap lighting + distortion + power/thickness falloff
- **Cost**: Extremely cheap — 1 extra lighting pass, no precomputation needed
- **Quality**: Convincing for thin surfaces (ears, fingers, membranes)
- **Mobile viable**: YES — pure math, no texture lookups beyond thickness map
- **Key formula**: `translucency = pow(saturate(dot(N, -L + distortion)), power) * thickness * attenuation`
- **Reference**: https://colinbarrebrisebois.com/2011/03/07/gdc-2011-approximating-translucency-for-a-fast-cheap-and-convincing-subsurface-scattering-look/
- **Also in**: GPU Pro 2 (detailed implementation chapter)

### 2. Three.js SSS Status (Issue #9249)
- Open since 2016, still no built-in physically-based SSS in Three.js core
- Ben Houston (clara.io) had a hack implementation
- Community implementations exist as custom ShaderMaterial
- **For SOMA**: Must implement as custom shader, cannot rely on Three.js built-in

### 3. SIGGRAPH 2025 Advances in Real-Time SSS
- Latest state-of-the-art published at SIGGRAPH 2025 Advances course
- PDF available at: https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- **Note**: Binary PDF — need browser or download to read
- ReSTIR-SSS from KIT (Karlsruhe Institute of Technology) — resampling-based SSS

### Mobile Performance Considerations
- WebGL 1.0 lacks compute shaders → no screen-space SSS
- WebGL 2.0 has MRT → screen-space possible but expensive on mobile
- **Recommended approach for SOMA**: 
  1. Per-vertex/per-object thickness map (precomputed)
  2. Frostbite approximation in fragment shader
  3. Fallback to simple wrap lighting on low-end devices
  4. Use `#ifdef USE_SSS` compile-time toggle in Three.js material

### WebGL + 3D Anatomy
- ACM paper (10.1145/3757749.3757808) confirms WebGL viable for 3D anatomical model rendering
- Key requirements: real-time rendering, smooth interaction, no lag
- SOMA is well-positioned with this approach

## Implementation Priority for SOMA
1. Start with Frostbite approximation (cheapest, looks good)
2. Add thickness map generation pipeline (MeshThicknessPass)
3. Integrate with existing PBR materials via shader chunks
4. Performance test on iOS WKWebView target devices


## Sources

- https://colinbarrebrisebois.com/2011/03/07/gdc-2011-approximating-translucency-for-a-fast-cheap-and-convincing-subsurface-scattering-look/
- https://github.com/mrdoob/three.js/issues/9249
- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- https://dl.acm.org/doi/full/10.1145/3757749.3757808
