# webgpu-tsl-instanced-rendering-performance

*Researched: 2026-04-06 06:43 CDT*

# WebGPU + TSL Instanced Rendering Performance (2026)

## Key Finding
Side-by-side benchmark (M3 MacBook Pro) comparing WebGL vs WebGPU with Three.js TSL (Three Shading Language):

| Metric | WebGL (CPU Bound) | WebGPU (TSL Driven) |
|--------|------------------|---------------------|
| Max Objects @60fps | ~15,000 | 200,000+ |
| CPU Usage | 100% main thread | Near zero |
| Draw Calls | 1 per object | 1 for all instances |
| Frame Updates | JS loop (600K calls/sec) | GPU shader (0 CPU) |

## Architecture: TSL (Three Shading Language)
- Write shader logic in TypeScript/JavaScript syntax
- Three.js compiles to WGSL (WebGPU Shading Language)
- `instanceIndex`, `time`, `hash`, `vec3` from `three/tsl`
- Define position/rotation as Nodes → runs entirely on GPU
- Zero CPU overhead after initial compile + buffer load

## Critical Pattern for SOMA
```typescript
// Instead of useFrame JS loop (CPU-bound):
// useFrame(() => { ref.current.rotation.x += delta; }); // 600K calls/sec

// Use TSL Nodes (GPU-bound):
import { time, instanceIndex, hash, vec3 } from 'three/tsl';
const index = instanceIndex;
const t = time.mul(1.0);
const angle = t.add(seed).mul(2.0);
const rotatedPos = rotateVector(positionLocal, axis, angle);
material.positionNode = offset.add(rotatedPos);
```

## SOMA Application
- Anatomy meshes (organs, bones) can use InstancedMesh + TSL for:
  - Breathing animations ( procedural sine wave on vertex positions)
  - Pulsing effects (cardiac cycle simulation)
  - Label positioning (GPU-computed world positions)
- Currently SOMA uses WebGL → migration to WebGPU+TSL would enable 10x more geometry at same FPS
- Three.js r160+ has WebGPU support; r170+ has stable TSL
- Caveat: WebGPU not supported on all mobile browsers yet (Safari iOS 17.4+, Chrome Android 121+)

## Source
- Gonzalo Galante, "WebGL vs WebGPU: The Performance Gap", Medium, Jan 2026
- Also: Reddit r/GraphicsProgramming discussion on instancing vs individual meshes confirms 1000 draw calls vs 1 draw call difference


## Sources

- https://gjgalante.medium.com/webgl-vs-webgpu-the-performance-gap-fbd121fb221a
- https://www.reddit.com/r/GraphicsProgramming/comments/1qn2c0y/what_would_the_performance_difference_look_like/
