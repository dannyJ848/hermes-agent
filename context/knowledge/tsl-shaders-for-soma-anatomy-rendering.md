# TSL Shaders for SOMA Anatomy Rendering

*Researched: 2026-04-05 18:49 CDT*

# TSL Shaders for SOMA Anatomy Rendering

## Summary
Three.js Shading Language (TSL) is production-ready for building custom materials with subsurface scattering effects. Combined with WebGPURenderer (Three.js r171+), TSL enables node-based shader authoring that's portable across WebGL and WebGPU backends — ideal for SOMA's tissue-specific rendering needs.

## Key Findings

### 1. TSL Architecture
- TSL is a JavaScript-like shading language that compiles to WGSL (WebGPU) or GLSL (WebGL)
- Uses a node system: `Fn`, `uniform`, `vec3`, `float`, `texture` etc. compose into shader graphs
- Maxime Heckel's Field Guide (Oct 2025) is the definitive reference: covers materials, compute shaders, particles, post-processing
- R3F integration has some quirks — `extend()` needs workarounds for node materials

### 2. Existing SSS in Three.js
- Built-in addon: `SubsurfaceScatteringShader` in `three/addons/shaders/SubsurfaceScatteringShader.js`
- Based on GDC 2011 "Approximating Translucency" — fast, cheap, convincing look
- This is the **legacy GLSL** approach — needs TSL rewrite for WebGPU compatibility

### 3. TSL SSS Implementation (Community)
- Reddit user demonstrated a TSL subsurface refraction shader (Jan 2025)
- Shows that SSS effects CAN be written in TSL's node system
- Approach: custom node material wrapping scattering + refraction logic

### 4. SOMA Migration Path
1. **Phase 1:** Port SOMA's current GLSL SSS to TSL node functions
2. **Phase 2:** Create tissue-specific SSS presets (skin, muscle, organ, fat) as TSL `Fn` blocks
3. **Phase 3:** Add TSL compute shaders for real-time light diffusion through tissue volumes
4. **Phase 4:** Integrate with WebGPURenderer for mobile iOS 18+ Safari support

### 5. TSL Gotchas
- TSL "considered harmful" discourse thread exists — some devs find the abstraction leaky
- Node material system differs from classic material system — can't mix freely
- React Three Fiber `extend()` needs workarounds for node materials
- iOS Safari WebGPU available since iOS 18 (late 2024)

## Source Code Pattern (TSL SSS Skeleton)
```javascript
import { Fn, uniform, vec3, vec4, float } from 'three/tsl';

const sssMaterial = Fn(({ position, normal, lightDir, thickness }) => {
  // GDC 2011 approximation in TSL
  const vLt = normal.dot(lightDir.negate()).add(1.0).mul(0.5);
  const distortion = float(0.2);
  const power = float(12.234);
  const scale = float(1.0);
  
  const vDistort = vLt.add(distortion);
  const vSubsurface = vDistort.pow(power).mul(scale);
  const subColor = vec3(1.0, 0.3, 0.1).mul(vSubsurface.mul(thickness));
  
  return vec4(subColor, 1.0);
});
```

## Next Steps for SOMA
- Implement TSL-based `TissueSSSMaterial` with presets for 6 tissue types
- Test on WebGPURenderer in Three.js r171+
- Benchmark mobile performance (triangle budget + shader complexity)


## Sources

- https://blog.maximeheckel.com/posts/field-guide-to-tsl-and-webgpu/
- https://threejs.org/docs/pages/module-SubsurfaceScatteringShader.html
- https://github.com/mrdoob/three.js/wiki/Three.js-Shading-Language
- https://discourse.threejs.org/t/tsl-considered-harmful/89497
