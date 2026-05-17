# webgpu-volume-rendering-threejs-2026

*Researched: 2026-04-06 03:22 CDT*

# WebGPU Volume Rendering for Medical Imaging (2025-2026)

## Key Findings

### Three.js WebGPU Volume Support
- **RenderTargetArray and RenderTarget3D** added to three.js WebGPU renderer (Jan 2025)
- **Data3DTexture** support enables direct volume data loading
- Example: `webgpu_rendertarget_2d-array_3d.html` demonstrates the API
- Existing WebGL example: `webgl_texture3d` — already high performance/quality

### WebGPU Volume Rendering Techniques
1. **Ray marching in compute shaders**: Full-screen triangle approach, fragment shader determines ray entry/exit
2. **GitHub examples**: `samdauwe/webgpu-native-examples` — direct volume rendering via ray marching
3. **MDPI paper** (Applied Sciences 15(5), 2782): WebGPU-based volume rendering framework for interactive visualization of scalar data
4. **Mol* web molecular graphics** (Protein Science, 2026): Moving to WebGPU for GPU-based molecular calculations

### Medical-Specific Applications
- **WebGPU dermatological AI** (Patel, Feb 2026): Client-side skin lesion classification using native compute shaders with local differential privacy
- **WebGPU MRI Raycast Engine** (Feb 2026): Real-time brain reconstruction in browser
- **Vanilla WebGPU volume render + raytracing** (Oct 2025): Pure WebGPU implementations emerging

### SOMA Relevance
- WebGPU compute shaders could replace WebGL for anatomy volume rendering
- Data3DTexture + ray marching = direct DICOM/NIfTI volume visualization
- Three.js WebGPU renderer now mature enough for medical visualization
- Performance: interactive frame rates achievable for CT/MRI volumes in browser
- **Migration path**: Start with existing `webgl_texture3d` example, migrate to WebGPU compute shaders

## Sources
- Three.js forum discussion: discourse.threejs.org/t/high-quality-volume-rendering-with-webgpu/71183
- samdauwe/webgpu-native-examples (GitHub)
- MDPI Applied Sciences 15(5):2782
- Mol* Protein Science 2026


## Sources

- https://discourse.threejs.org/t/high-quality-volume-rendering-with-webgpu/71183
- https://github.com/samdauwe/webgpu-native-examples
- https://www.mdpi.com/2076-3417/15/5/2782
