# threejs-volume-renderer-medical

*Researched: 2026-04-05 20:44 CDT*

# Three.js Volume Renderer for Medical Imaging (Donitzo/three.js-volume-renderer)

**Source:** github.com/Donitzo/three.js-volume-renderer
**License:** MIT
**Stars:** 16 (as of April 2026)
**Demo:** https://donitzo.github.io/three.js-volume-renderer

## Key Features
- **Single-class implementation**: `VolumeRenderer` extends `THREE.Mesh` with a raymarching fragment shader
- **NIfTI support**: Built-in NIfTI reader for loading medical imaging data (MRI, CT)
- **Procedural or data-driven**: Supply custom GLSL functions or 3D volumetric data
- **Compile-time shader toggles**: Uses `#define` directives to keep shader lightweight
  - Normal estimation for lighting
  - Depth testing against existing geometry
  - Clip planes (essential for anatomy cross-sections)
  - Color palettes with transparent cutoff range
  - Extinction coefficients for translucency
  - Animated 3D volume data atlas textures
- **VolumeSamplers.js**: Convert `THREE.Mesh` surfaces into volumetric shapes via signed distance fields

## Architecture
- `VolumeRenderer.js` — Core class, raymarching shader
- `VolumeSamplers.js` — Mesh-to-volume conversion
- `nifti-reader.js` — Medical image format parser
- `App.js` — Demo application

## Relevance to SOMA
- **Directly usable** for rendering DICOM/NIfTI anatomy data in SOMA's Three.js viewer
- **Clip planes** feature enables interactive cross-sections (SOMA's "scalpel" feature)
- **Extinction coefficients** could simulate subsurface scattering on tissue
- **VolumeSamplers** could convert existing glTF anatomy meshes into volumetric representations
- **Performance**: Uses ray step count as the primary quality/performance knob — critical for mobile

## Integration Path
1. Import `VolumeRenderer.js` and `VolumeSamplers.js` into SOMA's Three.js scene
2. Load NIfTI anatomy data (from BodyParts3D or Z-Anatomy datasets)
3. Configure clip planes for interactive dissection
4. Adjust ray step count for mobile vs desktop performance targets
5. Layer with existing mesh-based anatomy models for hybrid rendering

## Performance Considerations
- Ray step count is the primary performance lever (fewer steps = faster but blockier)
- Works as a fullscreen postprocessing effect, renders ON TOP of existing geometry
- Depth testing allows compositing with traditional mesh geometry
- Mobile viability depends on reducing ray steps and volume resolution


## Sources

- https://github.com/Donitzo/three.js-volume-renderer
- https://discourse.threejs.org/t/a-fairly-customizable-volumetric-renderer-mris-and-such/87212
