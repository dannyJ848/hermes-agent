# threejs-webgpu-regression-r182-2026

*Researched: 2026-04-07 12:59 CDT*

# Three.js WebGPU Performance Regression (r182, Jan 2026)

## Critical Finding
Three.js WebGPU renderer (r182) has SIGNIFICANT performance regressions vs WebGL (r170):
- Lower general frame rate on identical hardware (RTX 4070 Ti)
- Post-processing causes severe FPS drops in WebGPU
- Shadow quality is worse (harder edges) vs WebGL's softer shadows
- ShadowBias needs adjustment: -0.0005 for WebGPU

## Three.js Team Response
"WebGLRenderer has had a decade of optimizations... WebGPURenderer is still very actively being developed." — manthrax (Three.js contributor)

## SOMA Architecture Impact
- CONFIRMS WebGL2 as primary renderer (correct decision)
- TSL node materials (MeshSSSNodeMaterial) on WebGL2 renderer = correct approach
- Do NOT switch to WebGPU renderer until Three.js r190+ at minimum
- The TSL dual-compilation path (WGSL/WebGL2) is the right strategy

## Source
- Thread: https://discourse.threejs.org/t/webgpu-significant-performance-drop-and-shadow-quality-regression-in-r182-vs-webgl-r170/89322
- Date: January 20, 2026
- Three.js versions: r182.0 (WebGPU) vs r170.0 (WebGL)


## Sources

- https://discourse.threejs.org/t/webgpu-significant-performance-drop-and-shadow-quality-regression-in-r182-vs-webgl-r170/89322
