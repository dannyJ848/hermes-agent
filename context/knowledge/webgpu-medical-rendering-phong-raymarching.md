# webgpu-medical-rendering-phong-raymarching

*Researched: 2026-04-06 15:27 CDT*

# WebGPU Medical Rendering: Phong Reflection in MRI Raymarching

**Date:** 2026-04-06
**Source:** Oserebameh Beckley (LinkedIn)

## Key Technique
WebGPU-based MRI volume rendering with **Phong reflection model** implemented directly inside a raymarcher shader.

### How it works:
1. **Gradient computation**: Central differences on MRI intensity field → derive surface normals per voxel
2. **Lighting model**: Apply specular highlights + diffuse shading from computed normals
3. **Visual result**: Transforms "cloudy X-ray look" into "rigid body appearance" with clear depth/topology

### Why it matters for SOMA:
- Surface definition crucial for distinguishing tissue boundaries (Gray Matter, White Matter, CSF)
- Running entirely in browser via WebGPU — no server-side rendering needed
- Next step: curvature-based transfer functions to isolate pathologies

### Implementation insights:
- Transfer from emission-only to Phong-lit volume rendering dramatically improves anatomical perception
- Central differences for gradient: `normal = normalize(grad(scalar_field))` at each sample point
- Could be applied to SOMA's anatomy models for realistic tissue shading

## Related work:
- WebGL-based raycasting for 3D medical images (ResearchGate, 2020) — predecessor technique
- Blender Conference 2025: "Anatomy of Medical 3D" — Robin Imcke on medical 3D workflows


## Sources

- https://www.linkedin.com/posts/oserebameh-beckley_webgpu-medicalimaging-digitaltwins-activity-7407362252783140864-30oX
- https://www.researchgate.net/figure/Rendered-3D-medical-images-with-WebGL-based-raycasting-algorithms-showing-different_fig2_344398372
