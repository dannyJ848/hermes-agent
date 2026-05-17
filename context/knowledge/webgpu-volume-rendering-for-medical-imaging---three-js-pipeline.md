# WebGPU Volume Rendering for Medical Imaging - Three.js Pipeline

*Researched: 2026-04-05 15:52 CDT*

# WebGPU Volume Rendering for Medical Imaging

## Key Findings (April 2026)

### 1. Three.js WebGPU Volume Rendering Support
- **RenderTarget3D / RenderTargetArray**: Added to Three.js r170+ for WebGPU backend
- **Data3DTexture**: Native 3D texture support enables volume data (MRI/CT DICOM) to be loaded directly
- Example: `webgpu_rendertarget_2d-array_3d.html` in Three.js examples

### 2. Phong Shading in Ray Marching (MRI Pipeline)
- Oserebameh Beckley demonstrated WebGPU-based MRI volume rendering with Phong reflection
- Key technique: Compute gradient of MRI intensity field on-the-fly using central differences → derive surface normals
- Transforms "cloudy X-ray" emission rendering into "rigid body" appearance with depth/topology
- Critical for surgical planning: distinguishes Gray Matter, White Matter, CSF boundaries
- Next step: Transfer functions based on curvature to isolate pathologies
- **All running in browser**

### 3. MDPI Paper (2076-3417/15/5/2782)
- WebGPU-based volume rendering framework for interactive visualization of scalar data
- Uses compute shaders for ray marching (blocked by paywall, but confirms viability)

### 4. Mol* Molecular Graphics Engine (Protein Science, 2026)
- Moving to WebGPU for GPU-based calculations
- Relevant as reference architecture for SOMA's medical viewer

## SOMA Integration Path
1. Use Three.js WebGPU renderer (not WebGL) for volume rendering
2. Load DICOM data as Data3DTexture
3. Implement ray marcher as WebGPU compute shader
4. Add Phong shading with central-difference gradient normals
5. Curvature-based transfer functions for tissue segmentation

## Key References
- Three.js WebGPU volume example: threejs.org/examples/?q=3d#webgl_texture3d
- Three.js RenderTarget3D: threejs.org/examples/webgpu_rendertarget_2d-array_3d.html
- Twinklebear (Will Usher): github.com/Twinklebear — scientific visualization with WebGPU


## Sources

- https://discourse.threejs.org/t/high-quality-volume-rendering-with-webgpu/71183
- https://www.linkedin.com/posts/oserebameh-beckley_webgpu-medicalimaging-digitaltwins-activity-7407362252783140864-30oX
- https://www.mdpi.com/2076-3417/15/5/2782
- https://onlinelibrary.wiley.com/doi/10.1002/pro.70514
