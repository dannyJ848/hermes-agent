# threejs-instanced-mesh-large-scale-optimization

*Researched: 2026-04-06 05:58 CDT*

# Three.js InstancedMesh Large-Scale Optimization (3M+ instances)

## Key Techniques from Forum Discussion (April 2025)

### Problem
Scaling InstancedMesh from 1M to 3M+ instances causes FPS drops without LOD/frustum culling.

### Optimization Strategies
1. **Chunking**: Divide instances into spatial chunks. Only update/render chunks within view frustum.
2. **LOD for InstancedMesh**: Use multiple InstancedMesh objects at different detail levels. Swap instance counts per LOD level based on distance from camera.
3. **Custom Shader Animation**: Don't animate via JS — use vertex shaders with per-instance attributes (e.g., `instanceColor`, custom `instanceOffset`) for wind/grass sway.
4. **Frustum Culling at Instance Level**: Standard Three.js frustum culling only works on mesh-level. For instances, manually test instance bounding boxes against camera frustum and rebuild instance matrix buffer with only visible instances.
5. **GPU Instancing**: Ensure `InstancedBufferAttribute` is used for per-instance data — avoids CPU-GPU round trips.
6. **Count Management**: Use `InstancedMesh.count` property to dynamically reduce rendered instances without recreating the mesh.

### SOMA Application
- Anatomy models with thousands of labeled parts can use chunked InstancedMesh
- LOD levels: close-up shows full mesh detail, mid-range shows simplified geometry, far shows bounding boxes only
- Label rendering should use instanced quads with SDF text in shaders — avoids DOM overhead
- Mobile: cap at 100K visible instances, use aggressive frustum culling per body region

### Performance Targets
- 1M instances: 30-60 FPS achievable with chunking + frustum culling
- 3M instances: Requires GPU-driven culling or compute shaders (WebGPU)
- Mobile (iOS Safari): Cap at 50K-100K instances for stable 30 FPS


## Sources

- https://discourse.threejs.org/t/performance-optimizing-3m-instanced-grass-in-three-js/81286
- https://discourse.threejs.org/t/one-draw-call-massive-crowd-performance-engineering-in-three-js/89928
