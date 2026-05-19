# webgpu-compute-shaders-anatomy-rendering

*Researched: 2026-04-06 01:24 CDT*

# WebGPU Compute Shaders for Medical 3D Rendering

## Key Findings (Aug 2025)

### Compute Shaders vs WebGL Ping-Pong
- **WebGL approach**: Required 2 FBOs (Framebuffer Objects) for read/write data — one to read previous frame, another to write next frame results. Complex, wasteful.
- **WebGPU compute shaders**: Use **storage buffers** that allow in-place read/write in a single buffer. Eliminates swap overhead entirely.
- **Workgroup model**: Instead of thinking in pixels, compute shaders use threads grouped into workgroups (e.g., `WORKGROUP_SIZE = 32`). Dispatched via `wpass.dispatchWorkgroups(count)`.
- Workgroup sizing: enough threads to keep GPU busy but not exceed hardware limits.

### SOMA Application
1. **Particle-based anatomy**: If SOMA uses particle systems for tissue visualization, compute shaders would eliminate the FBO swap overhead
2. **Real-time mesh deformation**: Storage buffers could enable in-place vertex manipulation for interactive anatomy exploration
3. **Cross-section computation**: Compute shaders could calculate cross-section geometry in parallel on GPU
4. **Performance on mobile**: Author noted Android devices struggled more with CPU-side ML (MediaPipe) than GPU rendering — suggests mobile WebGPU is viable if CPU offload is managed

### Storage Buffer Advantage (Code Pattern)
```wgsl
// Before (WebGL): 2 buffers, swap each frame
@group(0) @binding(0) var<storage, read> inBuffer: array<Particle>;
@group(0) @binding(1) var<storage, read_write> outBuffer: array<Particle>;

// After (WebGPU compute): single buffer, in-place
@group(0) @binding(0) var<storage, read_write> buffer: array<Particle>;
```

### Mobile Caveat
- MediaPipe + WebGPU on mobile causes CPU bottleneck, not GPU
- Pixel phone handles 5x more particles with MediaPipe disabled
- Lesson: Keep ML inference separate from render loop on mobile

## Sources
- Medium: "WebGPU — From Ping Pong WebGL To Compute Shader" by Phish Chiang (Aug 2025)


## Sources

- https://medium.com/phishchiang/webgpu-from-ping-pong-webgl-to-compute-shader-%EF%B8%8F-1ab3d8a461e2
