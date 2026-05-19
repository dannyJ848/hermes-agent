# webgpu-compute-shaders-threejs-particles

*Researched: 2026-04-06 13:43 CDT*

# WebGPU Compute Shaders for Three.js Particle Systems

**Source:** Three.js Roadmap (Dan Greenheck, Dec 2025)

## Key Insight for SOMA
WebGPU compute shaders eliminate CPU→GPU data transfer bottleneck for particle systems. For anatomy rendering, this means tissue particle effects, volumetric rendering, and dynamic organ simulations can run entirely on GPU.

## Architecture Pattern
- **CPU approach:** Loop through particles sequentially, upload ~1.2MB/100K particles per frame = 72MB/s at 60fps. CPU bottleneck.
- **GPU compute shader approach:** All particles processed in parallel on GPU cores. No CPU↔GPU data transfer. ~30ms CPU → ~0.5ms GPU.
- **Storage buffers:** Particle data lives permanently in GPU memory. Compute shader reads/writes directly.

## Three.js TSL Integration
```javascript
// GPU compute shader pattern
computeShader() {
  const idx = instanceIndex;
  const velocity = velocityBuffer[idx];
  const position = positionBuffer[idx];
  velocity += acceleration * deltaTime;
  position += velocity * deltaTime;
  velocityBuffer[idx] = velocity;
  positionBuffer[idx] = position;
}
await renderer.computeAsync(computeShader);
```

## SOMA Application Ideas
1. **Tissue deformation:** Compute shader-driven vertex displacement for organ tissue simulation
2. **Volumetric rendering:** Ray-marched volume data in compute shader for CT/MRI visualization
3. **Particle-based fluids:** Blood flow, cerebrospinal fluid visualization
4. **LOD transitions:** Compute shader calculates optimal LOD per-vertex based on camera distance
5. **SSS approximation:** Screen-space subsurface scattering pass via compute shader

## Performance Implications
- 100K+ particles feasible at 60fps on mobile GPUs (M1+, A15+)
- Eliminates the main bottleneck for Three.js heavy scenes on mobile
- Requires WebGPU-capable browser (Safari 18+, Chrome 113+)

## Next Steps for SOMA
- Evaluate Three.js TSL (Three Shading Language) for compute shader authoring
- Prototype compute shader for anatomy model vertex skinning
- Test WebGPU availability on target iOS devices


## Sources

- https://threejsroadmap.com/blog/galaxy-simulation-webgpu-compute-shaders
