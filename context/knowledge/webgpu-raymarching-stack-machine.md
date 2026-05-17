# webgpu-raymarching-stack-machine

*Researched: 2026-04-05 17:56 CDT*

# WebGPU Raymarching Stack Machine for Anatomy Rendering

## Source
Byron Batteson's blog (Dec 2023) — Raymarching WebGPU Stack Machine

## Key Innovation
Uses a **stack machine architecture** to drive raymarching from CPU-side data rather than hardcoding shapes in shaders. This is directly applicable to SOMA's anatomy pipeline.

## Architecture Pattern
1. **CPU sends an array of shape/command descriptors** to GPU via WebGPU buffer
2. **Fragment shader evaluates SDF scene** using a virtual stack machine
3. Shapes: sphere, box, cylinder, plane, composite — all using WGSL `switch` dispatch
4. Composition via union/intersection/subtraction using `min`/`max` on SDF results

## WGSL Code Pattern
```wgsl
fn shape_sdf(p: vec3f, shape: Shape) -> Sdf {
    let color = shape.color;
    switch u32(shape.id) {
        case 0: { return Sdf(shape.a, color); }          // composite
        case 1: { return Sdf(box(p - offset, half_extents), color); }
        case 2: { return Sdf(cylinder(p - offset, r, h), color); }
        case 3: { return Sdf(plane(p, normal, offset), color); }
        case 4: { return Sdf(sphere(p - center, radius), color); }
        default: { return Sdf(MAX_DIST + EPSILON, color); }
    }
}
```

## Key Gotchas for SOMA
- **16-byte alignment** required for all structs in WebGPU buffers
- All shapes padded to same size (max shape size) for uniform array access
- Only 2 triangles needed for fullscreen raymarching (fragment shader does all work)
- SDF composition via `min`/`max` enables CSG operations (useful for anatomical cross-sections)

## Relevance to SOMA
1. **Cross-section rendering**: SDF subtraction = tissue dissection views
2. **Organ composition**: Union of sphere/cylinder SDFs ≈ anatomical structures
3. **Mobile-friendly**: No mesh data needed, just mathematical descriptors
4. **SSS integration**: SDF distance field naturally provides thickness for subsurface scattering

## Related Work Found
- MDPI paper: "WebGPU-Based Volume Rendering Framework" (ocean scalar data, same techniques applicable to medical volumes)
- Mol* molecular viewer: Moving to WebGPU for GPU compute calculations (Protein Science, 2026)
- WebGPU MRI reverse engineering pipeline: Phong reflection in WebGPU for brain digital twins
- WebGPU client-side AI: On-device skin lesion classification using WebGPU compute shaders (Feb 2026)

## Implementation Priority for SOMA
Phase 1: SDF-based anatomy primitives (sphere, cylinder for bones/organs)
Phase 2: Stack machine for composable scenes (CPU-driven, no shader recompilation)
Phase 3: Volume rendering integration with DICOM/NIfTI data via 3D textures


## Sources

- https://blog.batteson.com/2023/12/17/raymarching-webgpu-stack-machine.html
- https://www.mdpi.com/2076-3417/15/5/2782
- https://onlinelibrary.wiley.com/doi/10.1002/pro.70514
