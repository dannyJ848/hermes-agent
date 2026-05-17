# TSL-shader-authoring-for-anatomy-sss

*Researched: 2026-04-06 01:34 CDT*

# TSL (Three.js Shading Language) for Anatomy SSS Shaders

## Overview
TSL is a JavaScript API for building shaders as node graphs in Three.js. It compiles to both GLSL and WGSL, meaning shaders run on both WebGL and WebGPU without modification.

## Why TSL for SOMA Anatomy Rendering
- **No string injection**: Replace fragile `onBeforeCompile()` string surgery with clean JS composition
- **Cross-backend**: Same shader runs on WebGL (iOS Safari) and WebGPU (Chrome/Desktop)
- **PBR integration**: `MeshStandardNodeMaterial` and `MeshPhysicalNodeMaterial` expose shader slots (`colorNode`, `roughnessNode`, `emissiveNode`) that integrate with the full lighting model
- **Automatic dependency tracking**: Reference `positionWorld` and TSL auto-generates uniform declarations and matrix transforms

## Key API Patterns
```js
import { uniform, sin, float, color, texture, positionWorld, normalView } from 'three/tsl';

const material = new THREE.MeshPhysicalNodeMaterial();
material.colorNode = texture(map).mul(color(0xff0000));
material.roughnessNode = float(0.5);
material.emissiveNode = color(0x00ffff).mul(sin(time));
```

## Node Composition
- Operations chain fluently: `sin(time).mul(0.5).add(0.5)`
- Type system auto-converts: `vec3 * float` works correctly
- Dead code elimination at compile time
- Variable reuse is automatic

## SSS Implementation Strategy for SOMA
1. **Existing module**: Three.js already has `SubsurfaceScatteringShader` (examples/jsm/) based on GDC 2011 fast translucency approximation
2. **TSL rewrite**: Port the SSS logic to TSL nodes for cross-backend compatibility
3. **Anatomy-specific tuning**: Skin, muscle, and organ tissue have different SSS parameters (scattering distance, absorption color)
4. **Use MeshPhysicalNodeMaterial**: Already supports transmission/thickness — layer custom SSS on top

## Requires Three.js ≥ r171 (confirmed compatible with WebGPURenderer)


## Sources

- https://threejsroadmap.com/blog/tsl-a-better-way-to-write-shaders-in-threejs
- https://github.com/mrdoob/three.js/wiki/Three.js-Shading-Language
- https://threejs.org/docs/pages/module-SubsurfaceScatteringShader.html
