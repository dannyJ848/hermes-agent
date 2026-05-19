# tsl-sss-shader-tissue-rendering

*Researched: 2026-04-05 18:20 CDT*

# TSL Subsurface Scattering for Medical Tissue Rendering

## Summary
Research on implementing subsurface scattering (SSS) shaders using Three.js Shading Language (TSL) for realistic tissue visualization in SOMA. SSS is critical for medical anatomy — skin, organs, and tissue all exhibit light transmission through semi-transparent layers.

## Key Findings

### 1. TSL is the correct abstraction layer
- TSL (Three.js Shading Language) is a functional JS-based shading language that compiles to both WGSL (WebGPU) and GLSL (WebGL)
- Key benefit: write once, run on both WebGPU and WebGL — critical for SOMA's cross-platform needs (iOS Safari, desktop Chrome)
- Available since Three.js r166+ (mid-2025), production-ready in r171+ (Sep 2025)
- NodeMaterial system: `MeshPhysicalNodeMaterial` provides the base for custom SSS extensions

### 2. Existing TSL SSS Implementation
- Reddit user created a **TSL subsurface refraction shader** (r/threejs, ~Jan 2025) that adds subsurface + diffuse scattering to any mesh
- This is the first known TSL-native SSS implementation — directly relevant to SOMA
- Source: https://www.reddit.com/r/threejs/comments/1huapi3/

### 3. Screen-Space SSS Technique (for Skin)
- Screen-Space Subsurface Scattering is the production technique for real-time skin rendering
- Reference: Der Schmale's "Subsurface Scattering for Skin Rendering" (derschmale.com)
- Works by blurring light contributions in screen space based on a thickness map
- Three.js forum thread: https://discourse.threejs.org/t/skin-shading-with-screen-space-sub-surface-scattering/83939

### 4. Fast SSS in Three.js PBR (Matt DesLauriers)
- Gist with translucency-based SSS integrated into Three.js Physical material: https://gist.github.com/mattdesl/2ee82157a86962347dedb6572142df7c
- Key uniforms: `thicknessMap`, `thicknessPower`, `thicknessScale`, `thicknessDistortion`, `thicknessAmbient`
- Uses `USE_TRANSLUCENCY` preprocessor flag — translucency approach (wrap lighting) rather than full path tracing
- 33 stars, actively referenced — this is the community-standard starting point

### 5. TSL Architecture for Custom Shaders
From the TSL wiki and Maxime Heckel's Field Guide:
- TSL uses node-based composition: `Fn()` factory for shader functions
- Uniforms declared as `uniform(type, value)` 
- `uv`, `normalLocal`, `positionLocal` are built-in node attributes
- Swizzle operators work like GLSL: `color.rgb`, `color.x`
- Compute shaders available via TSL for GPU-side calculations (e.g., thickness precomputation)
- React Three Fiber integration has known issues with `extend()` — use vanilla Three.js for reliability

## SOMA Implementation Strategy

### Phase 1: Thickness-Based Translucency (Fast, ~2 days)
Port Matt DesLauriers' translucency approach to TSL:
```javascript
import { Fn, uniform, texture, vec3, float } from 'three/tsl';
import { MeshPhysicalNodeMaterial } from 'three/webgpu';

const sssMaterial = new MeshPhysicalNodeMaterial();
// Add thickness uniform, wrap lighting distortion
```
This gives immediate tissue-like appearance with minimal performance cost.

### Phase 2: Screen-Space SSS (Medium, ~1 week)
Implement screen-space blur technique for more realistic skin rendering:
- Requires depth + thickness prepass
- Use TSL compute shader for blur pass
- Apply to skin/muscle layers specifically

### Phase 3: Spectral SSS (Future)
For research-grade medical visualization:
- Multi-wavelength light absorption based on tissue type
- Would require compute shader for Monte Carlo sampling
- WebGPU-only (too heavy for WebGL fallback)

## TSL Gotchas (from Maxime Heckel's Field Guide)
1. R3F `extend()` has bugs with node materials — use vanilla Three.js
2. Classic materials (`meshStandardMaterial`) appear normal but may be node materials under the hood in R3F playgrounds
3. Lights sometimes need `scene.add()` instead of JSX syntax
4. TSL is relatively new — expect undocumented edge cases

## Sources
- Reddit TSL SSS shader: https://www.reddit.com/r/threejs/comments/1huapi3/
- Maxime Heckel TSL/WebGPU Field Guide: https://blog.maximeheckel.com/posts/field-guide-to-tsl-and-webgpu/
- TSL Official Wiki: https://github.com/mrdoob/three.js/wiki/Three.js-Shading-Language
- Matt DesLauriers SSS Gist: https://gist.github.com/mattdesl/2ee82157a86962347dedb6572142df7c
- Three.js Forum SSS Discussion: https://discourse.threejs.org/t/skin-shading-with-screen-space-sub-surface-scattering/83939


## Sources

- https://www.reddit.com/r/threejs/comments/1huapi3/
- https://blog.maximeheckel.com/posts/field-guide-to-tsl-and-webgpu/
- https://github.com/mrdoob/three.js/wiki/Three.js-Shading-Language
- https://gist.github.com/mattdesl/2ee82157a86962347dedb6572142df7c
- https://discourse.threejs.org/t/skin-shading-with-screen-space-sub-surface-scattering/83939
