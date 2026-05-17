# webgpu-compute-medical-visualization

*Researched: 2026-04-02 18:03 CDT*

# WebGPU Compute Shaders for Medical Visualization

## Volume Rendering (DVR) in WebGPU

### Architecture: Compute-Based Ray Marching
WebGPU enables fully compute-based Direct Volume Rendering — no geometry-pass hacks needed:
- **Pass 1**: Compute shader generates rays, marches through 3D volume texture
- **Pass 2**: Full-screen quad blit to canvas
- Front-to-back compositing with early ray termination
- Empty space skipping (4x step in transparent regions)

### Key WGSL Shader Features for Medical Viz
```wgsl
// 3D volume texture sampling with hardware trilinear interpolation
let density = textureSampleLevel(volume, nearestSampler, pos, 0.0).r;
// Transfer function lookup
let tfColor = textureSampleLevel(transferFunc, nearestSampler, density, 0.0);
// Gradient via central differences (for lighting/normals)
let gradient = computeGradient(volume, nearestSampler, pos);
```

### Maximum Intensity Projection (MIP) — for angiography
```wgsl
var maxIntensity = 0.0;
for (var i = 0u; i < steps; i++) {
    let density = textureSampleLevel(volume, samp, pos, 0.0).r;
    if (density > maxIntensity) { maxIntensity = density; maxPos = pos; }
}
```

### GPU Marching Cubes (3-pass, no CPU readback)
1. **Classify Voxels** (compute): Sample 8 corners → cube index → active voxel list
2. **Prefix Sum + Generate** (compute): Atomic counters, write triangles to storage buffer
3. **Render** (render pipeline): Draw generated mesh directly

Key repos:
- `nicekernel/webgpu-volume-renderer` — most complete open-source DVR
- `mikoro/webgpu-marchingcubes` — well-documented WebGPU MC
- `webgpu/webgpu-samples` — Google's reference volume rendering

### Ambient Occlusion via Compute
Fibonacci hemisphere sampling around each voxel in a compute shader — gives depth perception for medical volumes.

### Performance: WebGPU vs WebGL2
- WebGPU compute eliminates geometry-pass overhead for volume rendering
- Storage buffers enable direct GPU mesh generation (no CPU readback for MC)
- FP16 support halves memory vs WebGL's forced FP32
- Early ray termination + empty space skipping are compute-only optimizations

### Relevance to SOMA
- Pre-computed organ meshes via GPU marching cubes → served as compressed GLB
- Interactive cross-sections via ray-marched DVR (no mesh needed)
- MIP mode for vascular/angiographic views
- Transfer function editor for tissue-type visualization (bone/muscle/skin)


## Sources

- https://github.com/webgpu/webgpu-samples
- https://github.com/nicekernel/webgpu-volume-renderer
- https://github.com/mikoro/webgpu-marchingcubes
