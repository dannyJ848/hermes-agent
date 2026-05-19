# threejs-instanced-mesh-frustum-culling-mobile

*Researched: 2026-04-06 05:55 CDT*

# Three.js InstancedMesh View Frustum Culling for Mobile Performance

**Source:** VR Me Up DevLog #10 (Jan 2024)
**Relevance:** SOMA 3D anatomy viewer — critical for mobile GPU performance

## Key Insight
InstancedMesh in Three.js does NOT automatically frustum-cull individual instances. All instances are sent to the GPU regardless of visibility. On mobile/low-end GPUs, this can actually **decrease** performance vs individual objects (observed: 85 FPS individual → 55 FPS instanced on Quest 2).

## Solution Pattern
1. Allocate InstancedMesh with max capacity: `new THREE.InstancedMesh(geom, mat, MAX_COUNT)`
2. Each frame, iterate instances and test against camera frustum
3. Move visible instances to front of instance array
4. Set `mesh.count = visibleCount` to only render visible ones

```javascript
// Setup frustum from camera
camera.updateWorldMatrix(true, true);
const mat = new THREE.Matrix4();
mat.multiplyMatrices(camera.projectionMatrix, camera.matrixWorldInverse);
const frustum = new THREE.Frustum();
frustum.setFromProjectionMatrix(mat);

// Per-frame: test each instance position against frustum
const testSphere = new THREE.Sphere();
for (each instance) {
  testSphere.set(pos, testRadius);
  if (frustum.intersectsSphere(testSphere)) {
    // move to visible portion of array
  }
}
mesh.count = visibleCount;
```

## SOMA Application
- Anatomy models have many sub-meshes (organs, bones, systems)
- On mobile, only render body parts visible in current view
- Layer this with LOD: distant organs get simplified geometry
- Expected improvement: 2x frame rate on mobile for complex scenes
- Combine with Three.js `LOD` object for distance-based detail switching

## Performance Notes
- Array shuffling must be efficient (minimize matrix4 writes)
- Test with bounding spheres first (cheap), then bounding boxes (expensive)
- On high-end desktop, culling overhead may exceed GPU savings — profile first


## Sources

- https://vrmeup.com/devlog/devlog_10_threejs_instancedmesh_performance_optimizations.html
