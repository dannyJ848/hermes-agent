# real-time-sss-techniques-webgl-threejs

*Researched: 2026-04-05 15:28 CDT*

# Real-Time Subsurface Scattering for WebGL/Three.js

## Key Techniques (as of SIGGRAPH 2025)

### 1. Screen-Space SSS (Post-Process)
- Most common real-time approach in games
- Render scene normally, then blur in screen-space to simulate light diffusion
- Gaussian-based kernels (typically 2-3 passes) approximate diffusion profile
- **Three.js relevance**: No built-in screen-space SSS. Custom post-processing pass needed via EffectComposer

### 2. Pre-Integrated Skin Shading
- Penn et al. technique: pre-compute diffuse lookup textures
- Avoids per-pixel subsurface sampling entirely
- Works on mobile — lookup texture is small (256x256)
- **Best option for SOMA mobile**: Low cost, good visual quality for anatomy

### 3. Separable Subsurface Scattering
- Jimenez et al. 2015: decompose 2D blur into two 1D passes
- 25x faster than full 2D convolution
- Used in Uncharted 4, Frostbite engine
- Requires render-to-texture + blur passes

### 4. NVIDIA SIGGRAPH 2025 Hybrid Approach
- Combines volumetric path tracing with physically-based diffusion approximation
- Likely requires RTX hardware — NOT suitable for mobile/WebGL

### 5. Wrap Lighting (Simplest)
- `diffuse = max(0, dot(N, L) + wrap) / (1 + wrap)` where wrap ∈ [0,1]
- Zero cost, instant improvement for organic tissue
- SOMA could use this as a baseline with wrap=0.5 for skin/muscle

## SOMA Implementation Strategy (Priority Order)

1. **Phase 1**: Wrap lighting for all organic tissues (1 shader line change)
2. **Phase 2**: Pre-integrated skin shading via lookup texture (moderate effort, mobile-friendly)
3. **Phase 3**: Screen-space blur SSS via post-processing (advanced, needs custom pass)
4. **Phase 4**: Consider WebGPU compute shaders for diffusion simulation (future)

## Key Insight
For medical anatomy on mobile, pre-integrated skin shading gives 80% of visual quality at 10% of the cost. The SIGGRAPH 2025 advances focus on path-traced SSS which requires hardware ray tracing — irrelevant for mobile WebGL. Focus on Phase 1+2.

## Sources
- MJP's SSS Introduction: https://therealmjp.github.io/posts/sss-intro/
- SIGGRAPH 2025 Real-Time Rendering Course: https://advances.realtimerendering.com/s2025/
- Three.js SSS discourse thread: https://discourse.threejs.org/t/skin-shading-with-screen-space-sub-surface-scattering/83939

## Sources

- https://therealmjp.github.io/posts/sss-intro/
- https://advances.realtimerendering.com/s2025/
- https://discourse.threejs.org/t/skin-shading-with-screen-space-sub-surface-scattering/83939
