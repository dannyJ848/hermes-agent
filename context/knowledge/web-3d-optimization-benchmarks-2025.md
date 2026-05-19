# web-3d-optimization-benchmarks-2025

*Researched: 2026-04-07 12:50 CDT*

# Web 3D Model Optimization Benchmarks (2025)

## Performance Targets (SOMA Mobile)
- **File size**: <2MB per model for mobile delivery
- **FPS**: 60 FPS on mid-range devices
- **Load time**: <3 seconds first render

## gltf-transform CLI (Key Tool)
```bash
npm install -g @gltf-transform/cli

# Convert any format to GLB
gltf-transform copy model.fbx model.glb
gltf-transform copy model.obj model.glb

# Draco compression (90% mesh size reduction)
gltf-transform draco model.glb model-optimized.glb

# Texture optimization (WebP = 50-70% smaller than JPEG/PNG)
gltf-transform etc1s model.glb model-compressed.glb
```

## Key Findings
- **GLB format**: 20-40% size reduction over multi-file glTF
- **Draco**: 90%+ mesh compression (vertices, normals, UVs)
- **Textures**: 80% of file size → WebP/ETC1S compression is critical
- **Meshopt**: Alternative to Draco, better for progressive loading (important for SOMA)
- **Unoptimized models**: 300-500% larger, cause mobile frame drops

## SOMA Application
1. Use gltf-transform in asset pipeline (soma-asset-pipeline skill)
2. Meshopt > Draco for SOMA (progressive loading + no WASM decoder needed with Three.js r182+)
3. Texture budget per anatomy model: aim for 512x512 max (mobile GPU)
4. LOD system: 3 levels (high=100%, medium=40% triangles, low=15% triangles)


## Sources

- https://www.axl-devhub.me/en/blog/optimizing-3d-models
- https://github.com/donmccurdy/glTF-Transform
