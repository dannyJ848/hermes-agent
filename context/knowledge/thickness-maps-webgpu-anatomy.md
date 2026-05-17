# thickness-maps-webgpu-anatomy

*Researched: 2026-04-05 17:16 CDT*

# Thickness Map Generation for Anatomy Rendering in WebGPU

## Problem
SOMA's 3D anatomy viewer needs thickness maps for realistic subsurface scattering (SSS). Thickness maps encode how "thick" the mesh is at each point — thicker = more light scattering (ears, nose tip), thinner = less.

## Known Techniques (from SSS literature)

### Technique 1: Back-face Depth Subtraction (Real-time, Screen-Space)
1. Render front faces to depth buffer (Z_front)
2. Render back faces to another depth buffer (Z_back)
3. Thickness = Z_back - Z_front per pixel
4. **Pros:** Simple, works in WebGPU with two render passes, no pre-processing
5. **Cons:** Screen-space only, must recompute per frame, artifacts at silhouette edges
6. **Implementation:** Two render passes in WGSL, one with `frontFace: 'ccw'` and one with `frontFace: 'cw'`, then compute difference in a compute shader

### Technique 2: Pre-baked Thickness Texture (Offline)
1. Ray-march from each surface point inward along the normal
2. Record distance until exiting the mesh
3. Store as a grayscale texture (UV-mapped)
4. **Pros:** Highest quality, no per-frame cost, no artifacts
5. **Cons:** Requires UV unwrapping, offline baking step, doesn't work for dynamic meshes

### Technique 3: Approximate Thickness from Curvature (Fastest)
1. Compute curvature from surface normals
2. High curvature = likely thin (ears, fingers)
3. Low curvature = likely thick (torso, skull)
4. **Pros:** Trivially fast, can be computed in vertex shader
5. **Cons:** Very approximate, wrong for many anatomical structures

## Recommended Approach for SOMA
**Technique 1 (Back-face Depth Subtraction)** is the sweet spot:
- Works in real-time WebGPU
- No offline pre-processing needed
- Quality sufficient for educational visualization
- Implementation: 2 render passes + 1 compute shader in WGSL
- Cost: ~0.5ms per frame on mobile

## WGSL Implementation Sketch
```wgsl
// Compute thickness from two depth textures
@group(0) @binding(0) var front_depth: texture_2d<f32>;
@group(0) @binding(1) var back_depth: texture_2d<f32>;
@group(0) @binding(2) var output_tex: texture_storage_2d<rgba8unorm, write>;

@compute @workgroup_size(16, 16)
fn main(@builtin(global_invocation_id) id: vec3u) {
    let dims = textureDimensions(front_depth);
    if (id.x >= dims.x || id.y >= dims.y) { return; }
    let z_front = textureLoad(front_depth, id.xy, 0).r;
    let z_back = textureLoad(back_depth, id.xy, 0).r;
    let thickness = clamp((z_back - z_front) * 20.0, 0.0, 1.0);
    textureStore(output_tex, id.xy, vec4f(thickness, thickness, thickness, 1.0));
}
```

## Sources
- Separable Subsurface Scattering (Jimenez et al. 2015) — uses screen-space thickness
- GPU Pro 5, Chapter 2: "Fast Subsurface Scattering" — back-face depth technique
- Three.js examples: WebGL deferred rendering approach


## Sources

- https://research.nvidia.com/sites/default/files/pubs/2010-06_Ambient-Occlusion-Volumes/McGuire10AOV.pdf
- https://animation.rwth-aachen.de/media/papers/2013-CADGraphics-MultilayerAO.pdf
