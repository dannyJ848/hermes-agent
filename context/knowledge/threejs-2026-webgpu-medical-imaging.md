# threejs-2026-webgpu-medical-imaging

*Researched: 2026-04-12 18:56 CDT*

# Three.js 2026 + WebGPU for Medical Imaging

## Key Developments (Mar-Apr 2026)

### WebGPU Now Universal
- Safari 26 (Sep 2025) was the final piece — WebGPU is now on ALL major browsers including iOS
- Three.js r171+ made WebGPU production-ready: `import { WebGPURenderer } from 'three/webgpu'`
- Zero-config imports, no polyfills needed

### Three.js Dominance
- 2.7M weekly NPM downloads (270x Babylon.js, 337x PlayCanvas)
- No real competition in web 3D space

### Performance Gains
- One platform achieved **100x performance improvement** migrating from WebGL to WebGPU
- GPU-driven techniques replacing CPU-heavy scene graphs (instancing, GPGPU particles, compute shaders)
- Compute shaders now available for collision detection, real-time filtering, ML inference in browser

### SOMA-Relevant Implications
1. **Volume rendering in browser**: 67% of desktop performance at 24fps for ray-casting 3D visualization
2. **Ossium** (fraserlove/ossium): WebGPU volume rendering for 3D medical imaging, open-source
3. **Rust + WASM**: Web MRI volume renderer compiled to WASM shows GPU-accelerated 3D rendering is production-viable
4. **NVIDIA Clara + VolView**: Kitware integrating Clara models into browser-native imaging — shows browser DICOM is mainstream

### Action Items for SOMA
- Evaluate WebGPURenderer migration from WebGL for 3D anatomy viewer
- Consider Ossium's approach for volume rendering (cross-sections, tissue differentiation)
- Explore compute shaders for real-time tissue segmentation in browser
- Monitor Three.js releases for MeshSSSNodeMaterial improvements (r182+)

## Sources
- https://www.utsubo.com/blog/threejs-2026-what-changed
- https://github.com/fraserlove/ossium
- https://www.bonamisoftware.com/blog-healthcare-dicom-imaging-browser
- https://www.kitware.com/integrating-nvidia-clara-models-into-volview/


## Sources

- https://www.utsubo.com/blog/threejs-2026-what-changed
- https://github.com/fraserlove/ossium
- https://www.bonamisoftware.com/blog-healthcare-dicom-imaging-browser
- https://www.kitware.com/integrating-nvidia-clara-models-into-volview/
