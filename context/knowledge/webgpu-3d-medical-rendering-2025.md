# webgpu-3d-medical-rendering-2025

*Researched: 2026-04-04 20:59 CDT*

# WebGPU-Based 3D Rendering for Medical Applications (Web3D 2025)

## wgpuEngine: Cross-Platform WebGPU 3D Engine
**Institution:** Universitat Pompeu Fabra (UPF), Barcelona — GTI Interactive Technologies Group
**Venue:** Web3D 2025 (30th ACM Conference on 3D Web Technology), September 2025, Siena, Italy
**Paper:** "A Cross-Platform, WebGPU-Based 3D Engine for Real-Time Rendering and XR Applications"

### Key Features
- Cross-platform, open-source C++ graphics engine
- Built for WebGPU API (successor to WebGL)
- XR support built-in (AR/VR)
- Real-time 3D rendering for browsers AND native environments
- Used for sculpting applications (shown in Rooms app)

### Relevance to SOMA
1. **Migration Path:** SOMA currently uses Three.js + WebGL. wgpuEngine demonstrates WebGPU is production-ready for web-based 3D
2. **XR Integration:** SOMA could add AR/VR anatomy exploration using WebGPU's native XR APIs
3. **Performance:** WebGPU provides lower-level GPU access than WebGL, enabling:
   - Compute shaders for real-time tissue simulation
   - Better instanced rendering for complex anatomical scenes
   - Native subsurface scattering implementations

### Current SOMA Architecture (for comparison)
- Three.js + WebGL for rendering
- GLB/gltf mesh format (compatible with wgpuEngine)
- Target: mobile browsers (iOS Safari — note: WebGPU support still limited)

### Action Items for SOMA
1. Monitor iOS Safari WebGPU support progress (currently in beta)
2. When WebGPU reaches Safari stable, plan migration from Three.js
3. Keep mesh assets in glTF/GLB format (already compatible)
4. Consider compute shaders for real-time tissue deformation

## Broader 3D Medical Visualization Trends (2025)
From Emergent Mind survey:
- **Remote rendering** with thin clients gaining traction (HoloView) — foveated rendering minimizes bandwidth
- **Modular client-server** architecture standard for collaborative anatomy (Anatomy Studio II)
- **GLB/gltf streaming** via three.js/WebGL is the dominant web approach (HBot)
- **GPU-accelerated volume rendering** used in high-end VR systems (syGlass, CvhSlicer 2.0)


## Sources

- https://www.upf.edu/web/gti/news/-/asset_publisher/Fcaqe3UGmcpl/content/paper-accepted-at-web3d-2025/maximized
- https://www.emergentmind.com/topics/interactive-3d-human-body-visualization
