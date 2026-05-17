---
name: soma-sss-shaders
description: Subsurface scattering for SOMA 3D anatomy viewer using native MeshSSSNodeMaterial from Three.js r182+ with legacy GLSL fallback. 14 tissue profiles.
---

# SOMA Subsurface Scattering (SSS) Guide

## Decision History

1. **v1 (Legacy):** Custom GLSL `onBeforeCompile` injection into `MeshPhysicalMaterial` - single LUT fetch, mobile-optimized. File: `SubsurfaceScattering.ts`.
2. **v2 (Current, Apr 2026):** Native `MeshSSSNodeMaterial` from Three.js r182 - zero custom shaders, GPU-native SSS, works on both WebGPU and WebGL2 via TSL. File: `SubsurfaceScatteringTSL.ts`.

**Use v2 (native) for all new code.** v1 is kept as WebGL2 fallback only.

---

## Path 1: Native WebGPU SSS (MeshSSSNodeMaterial) - PREFERRED

### Critical Import Pattern (discovered via trial-and-error)

```
Materials come from 'three/webgpu':
  MeshSSSNodeMaterial, MeshPhysicalNodeMaterial, MeshStandardNodeMaterial, etc.

TSL functions come from 'three/tsl':
  uniform, texture, mix, normalize, dot, clamp, vec3, float, etc.

NEVER import materials from 'three/tsl' - they do not exist there.
NEVER import uniform() from 'three/webgpu' - it does not exist there.
```

### Available Node Materials in three/webgpu (r182)

Discovered via `node -e "const m = require('three/webgpu'); console.log(Object.keys(m).filter(k => /NodeMaterial/i.test(k)))"`:
- MeshSSSNodeMaterial (our hero for SSS)
- MeshPhysicalNodeMaterial
- MeshStandardNodeMaterial
- MeshBasicNodeMaterial
- VolumeNodeMaterial
- NodeMaterial (base class)

### MeshSSSNodeMaterial Properties

**Standard PBR:** color, roughness, metalness, transparent, side, opacity
**SSS-specific (scalar):** thickness, attenuationColor, attenuationDistance
**SSS-specific (TSL node):**
- `thicknessColorNode` - internal scattering color tint
- `thicknessDistortionNode` - distortion amount (0.1-0.3 for anatomy)
- `thicknessAmbientNode` - ambient scattering (0.3-0.5)
- `thicknessAttenuationNode` - attenuation (0.6-0.9)
- `thicknessPowerNode` - falloff power (1.5-3.0)
- `thicknessScaleNode` - overall scale (matches thickness)

### Usage Pattern

```typescript
import { MeshSSSNodeMaterial } from 'three/webgpu';
import { uniform } from 'three/tsl';
import * as THREE from 'three';

// Create material with tissue profile
const material = new MeshSSSNodeMaterial();
material.color = new THREE.Color(0.8, 0.4, 0.3); // skin base
material.roughness = 0.6;
material.thickness = 1.2;
material.attenuationColor = new THREE.Color(0.8, 0.2, 0.1);
material.attenuationDistance = 0.6;

// TSL node uniforms (reactive - update .value at runtime)
material.thicknessColorNode = uniform(new THREE.Color(0.8, 0.4, 0.3));
material.thicknessDistortionNode = uniform(0.15);
material.thicknessAmbientNode = uniform(0.4);
material.thicknessAttenuationNode = uniform(0.8);
material.thicknessPowerNode = uniform(2.0);
material.thicknessScaleNode = uniform(1.2);
```

### Runtime Updates (no recompilation)

```typescript
// Update uniform values directly - takes effect next frame
(material.thicknessColorNode as any).value?.setRGB(r, g, b);
material.thicknessScaleNode.value = newThickness;
```

Note: TypeScript types for Node `.value` are incomplete. Use `as any` cast.

### File Location

`src/anatomy/SubsurfaceScatteringTSL.ts` - exports:
- `createNativeSSSMaterial(tissueType, baseConfig?)` - main factory
- `updateNativeSSSProfile(material, updates)` - runtime param updates
- `createAllTissueMaterials()` - batch create all 14 tissue materials

### Tissue Profiles (14 types)

skin, muscle, organ, bone, cardiac_muscle, liver_tissue, kidney_tissue, lung_tissue, blood_vessel_artery, blood_vessel_vein, fat, cartilage, neural_tissue, eye_sclera

---

## Path 2: Legacy GLSL SSS (WebGL2 Fallback)

### When to Use
- Devices without WebGPU support AND where MeshSSSNodeMaterial fails to fall back
- Debugging/testing shader behavior

### File Location
`src/anatomy/SubsurfaceScattering.ts` - uses `onBeforeCompile` GLSL injection into MeshPhysicalMaterial.

### Core GLSL Functions

```glsl
uniform sampler2D sssLUT; // 256x256 pre-baked LUT

float computeCurvature(vec3 position, vec3 normal) {
    vec3 dx = dFdx(position);
    vec3 dy = dFdy(position);
    vec3 dn1 = dFdx(normal);
    vec3 dn2 = dFdy(normal);
    vec3 dndx = dn1 * length(dy) - dn2 * length(dx);
    vec3 dndy = dn2 * length(dx) - dn1 * length(dy);
    return max(length(dndx), length(dndy));
}

vec3 preIntegratedSSS(float NdotL, float curvature, vec3 sssColor) {
    float uv_x = NdotL * 0.5 + 0.5;
    float uv_y = clamp(curvature * 10.0, 0.0, 1.0);
    return texture2D(sssLUT, vec2(uv_x, uv_y)).rgb * sssColor;
}
```

### LUT Generation

The LUT is generated programmatically in `generateSSSLUT()` (TypeScript, no Python needed). Creates a 256x256 DataTexture with Gaussian diffusion profiles (sigma R=0.1, G=0.05, B=0.02). Cached for app lifetime.

---

## R3F Canvas + WebGPU Integration (Lesson Learned Apr 2026)

### WRONG APPROACH #1: Async gl factory (FAILS)
```tsx
// R3F v9.5.0 does NOT support async gl factories. TS2322 error.
<Canvas gl={async (canvas: HTMLCanvasElement) => {
  const renderer = new WebGPURenderer({ canvas });
  await renderer.init(); // Can't await in sync factory
  return renderer;
}} />
```

### WRONG APPROACH #2: Dynamic import of WebGPURenderer (FAILS)
```tsx
// Module not found: 'three/examples/jsm/renderers/webgpu/WebGPURenderer.js'
// The path doesn't exist in three v0.182.0
const { default: WebGPURenderer } = await import('three/examples/jsm/renderers/webgpu/WebGPURenderer.js');
```

### CORRECT APPROACH: WebGL2 renderer + TSL node materials (WORKS)
```tsx
// Keep WebGL2 renderer. TSL node materials (MeshSSSNodeMaterial) compile to
// BOTH WGSL (WebGPU) and GLSL (WebGL2) automatically via Three.js's pipeline.
<Canvas gl={(props) => {
  return new THREE.WebGLRenderer({
    ...props,
    antialias: false,
    alpha: true,
    powerPreference: 'default',
  });
}} />
```

The key insight: **Don't change the renderer.** TSL-based node materials handle the dual-path internally. Three.js r182's TSL compiles to WGSL when WebGPU is available, GLSL when it's not. The renderer stays WebGL2 for R3F compatibility.

### iOS WebGPU Reality (verified April 2026)
- WebGPU requires **iOS 26+** (Safari 26.0, shipped September 2025)
- iOS 17, 18, 19, 20, 21, 22, 23, 24, 25 = NO WebGPU
- iPhone 14 running any iOS < 26 = WebGL2 only
- Chrome Android 121+ = WebGPU available now
- Therefore: WebGL2 primary renderer is correct for SOMA's target demographic

### SSS in ZAnatomyLoader (Integration Pattern)
```typescript
// In processMesh() - use require() with try/catch for graceful fallback
if (config.useSSS && config.sssProfile !== 'none') {
  try {
    const { createNativeSSSMaterial } = require('./SubsurfaceScatteringTSL');
    const sssMaterial = createNativeSSSMaterial(config.sssProfile);
    if (sssMaterial) {
      // Preserve original GLB color
      if (mesh.material instanceof THREE.MeshStandardMaterial && mesh.material.color) {
        (sssMaterial as any).color = mesh.material.color.clone();
      }
      mesh.material = sssMaterial as THREE.Material;
      mesh.material.transparent = config.defaultOpacity < 1.0;
      mesh.material.opacity = config.defaultOpacity;
    }
  } catch (e) {
    // TSL SSS not available — fall back to standard material
    console.warn('[ZAnatomyLoader] SSS failed, using standard:', e);
  }
}
```

---

## WebGPU Compute Shader Path (Future-Ready)

As of March 2026, WebGPU has ~70% browser support on desktop (Wishtree research). Performance gains of 2-3x over WebGL for GPU-heavy workloads. Compute shaders enable:

### SSS Precomputation on GPU
```typescript
// Future: WebGPU compute shader for scattering table generation
// Currently done in TypeScript via generateSSSLUT()
// WebGPU compute could parallelize this across 1000+ threads
async function precomputeScatteringTable(device: GPUDevice) {
  if (!navigator.gpu) return null;
  const adapter = await navigator.gpu.requestAdapter();
  if (!adapter) return null;
  
  const computeShader = `
    @group(0) @binding(0) var<storage, read_write> output: array<vec4f>;
    @compute @workgroup_size(256)
    fn main(@builtin(global_invocation_id) id: vec3u) {
      let idx = id.x;
      // Parallel Gaussian diffusion profile computation
      let sigma_r = 0.1; let sigma_g = 0.05; let sigma_b = 0.02;
      // ... compute scattering values ...
      output[idx] = vec4f(r, g, b, 1.0);
    }
  `;
  // 256x256 LUT in <1ms vs ~15ms in JS
}
```

### Detection Pattern
```typescript
// WebGPU feature detection — use for future progressive enhancement
const hasWebGPU = !!navigator.gpu;
const hasComputeShaders = hasWebGPU && await (async () => {
  try {
    const adapter = await navigator.gpu.requestAdapter();
    return adapter?.features.has('shader-f16') ?? false;
  } catch { return false; }
})();
```

### Migration Timeline
- **Now (Apr 2026):** WebGL2 primary, TSL dual-compiles to WGSL/GLSL
- **Q3 2026:** When iOS Safari WebGPU hits 50%+ of SOMA target users, switch primary renderer
- **Q4 2026:** Compute shaders for SSS LUT precomputation, tissue simulation, medical NLP on-device
- **Never:** Don't break WebGL2 fallback — always maintain dual-path

### Key Data (Wishtree, March 2026)
- WebGPU: 70% desktop browser support, 2-3x perf over WebGL
- iOS: Safari 26+ only (Sept 2025), vast majority still on iOS <26
- Chrome Android 121+: WebGPU available
- Recommendation: WebGL2 primary + WebGPU progressive enhancement

### ⚠️ Three.js WebGPU Performance Regression (Jan 2026, r182)
- **WebGPU renderer (r182) is SIGNIFICANTLY slower than WebGL (r170)** on same hardware
- Post-processing causes severe FPS drops in WebGPU mode
- Shadow quality is worse (harder edges) in WebGPU vs WebGL
- Three.js team acknowledges: "WebGLRenderer has had a decade of optimizations... WebGPURenderer is still very actively being developed"
- **ShadowBias fix**: For WebGPU, use -0.0005 as starting bias
- **Source**: https://discourse.threejs.org/t/webgpu-significant-performance-drop-and-shadow-quality-regression-in-r182-vs-webgl-r170/89322
- **SOMA Impact**: CONFIRMS WebGL2 as primary renderer. Do NOT switch to WebGPU renderer until Three.js matures (likely r190+). TSL node materials on WebGL2 renderer remain the correct approach.

---

## SIGGRAPH 2025: ReSTIR SSS (Future Integration)

**Paper:** "ReSTIR Subsurface Scattering for Real-Time Path Tracing" (KIT/NVIDIA, SIGGRAPH 2025)
- **DOI:** https://dl.acm.org/doi/abs/10.1145/3675372
- Hybrid approach: volumetric path tracing + physically-based diffusion profiles
- Uses ReSTIR (Reservoir-based Spatiotemporal Importance Resampling) for sample reuse across pixels/frames
- Significantly reduces noise in real-time path-traced SSS

**SOMA relevance:** When WebGPU compute shaders become primary (Q4 2026+), ReSTIR SSS could enable film-quality subsurface scattering in the anatomy viewer. Requires:
1. WebGPU ray tracing pipeline (not yet in browser WebGPU spec)
2. Compute shader-based resampling
3. Denoiser pass

**Current alternative for SOMA:** Wrap lighting + thickness maps (cheapest), screen-space separable blur (moderate), MeshSSSNodeMaterial (best quality today).

**Full research finding saved:** `~/.hermes/knowledge/real-time-subsurface-scattering-techniques-2025.md`

---

## Pitfalls

1. **NEVER combine with `transmission: 1.0`** - multi-pass OIT destroys mobile perf
2. **Import separation is critical** - materials from `three/webgpu`, functions from `three/tsl`
3. **`thicknessColorNode` can be null** - always null-check before accessing `.value`
4. **TypeScript Node types are incomplete** - use `as any` for `.value` access
5. **Curvature from dFdx/dFdy is noisy on low-poly** - consider pre-baked curvature maps
6. **iOS WKWebView has ~350MB memory limit** - proactive geometry/material disposal is mandatory
7. **Discovery trick** - Use `node -e "const m = require('three/webgpu'); ..."` to inspect available exports at runtime when TypeScript types are misleading
8. **R3F v9.5 gl factory is SYNC only** - Cannot use async WebGPURenderer init. Use TSL materials instead.
9. **WebGPU != available on target devices** - iOS 26+ required. WebGL2 is primary renderer.
10. **Use require() not import for SSS in loaders** - Allows graceful fallback when three/webgpu is unavailable
