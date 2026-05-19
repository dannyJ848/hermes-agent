# webgpu-sss-shaders-anatomy-2026

*Researched: 2026-04-02 20:05 CDT*

# WebGPU Subsurface Scattering for Anatomy Rendering (April 2026)

## Three.js TSL Approach (r170+)

### Strategy: MeshPhysicalNodeMaterial + Custom TSL Nodes
1. Use `MeshPhysicalNodeMaterial` with `thickness`/`attenuationColor` for basic SSS
2. Add custom TSL node functions for per-material tuning
3. Optionally combine with screen-space SSS blur post-processing

### Key TSL Imports
```javascript
import { MeshPhysicalNodeMaterial, uniform, texture, vec3, vec2, float,
         Fn, mix, max, clamp, dot, normalize, pow, exp, length,
         normalWorld, positionWorld, cameraPosition, dFdx, dFdy } from 'three/tsl';
```

### SSS Parameters (Per Tissue Type)
| Tissue | Thickness | Attenuation Color | Radius |
|--------|-----------|-------------------|--------|
| Skin (fair) | 2.0 | 0xff6633 | 0.003 |
| Muscle | 3.0 | 0xaa2200 | 0.005 |
| Organ (liver) | 4.0 | 0x882211 | 0.008 |
| Organ (heart) | 3.5 | 0xcc3322 | 0.006 |

### Pre-Integrated SSS (Penner-Borshukov Style)
- Create 512x512 LUT texture: X-axis = NdotL [-1,1], Y-axis = curvature [0,1]
- 3-lobe Gaussian approximation for skin-like tissue
- Look up at runtime for O(1) per-pixel SSS evaluation

## Screen-Space SSS (Jimenez 2015 Separable)
### Architecture
```
G-Buffer Pass → Lighting Pass → SSS Blur (2-pass separable) → Final Composite
```

### Gaussian Kernel (6-8 sample, skin profile)
- Separable blur: horizontal then vertical pass
- Uses SSS mask to identify which pixels get treatment
- Chromatic separation (different blur radii per RGB channel)
- Performance: ~2ms on Apple M1 at 1080p with 8 samples

## Performance Targets for Mobile
| Platform | Target FPS | SSS Budget | Recommended Approach |
|----------|-----------|------------|---------------------|
| Apple M-series | 60 FPS | <3ms | Full screen-space SSS |
| Apple A14+ | 30 FPS | <5ms | Pre-integrated LUT only |
| Snapdragon 8+ | 30 FPS | <8ms | Simplified translucency |
| Older mobile | 30 FPS | N/A | MeshPhysical thickness only |

## SOMA Implementation Priority
1. Start with `MeshPhysicalNodeMaterial` thickness/transmission (zero custom code)
2. Add pre-integrated LUT for curvature-dependent scattering
3. Implement screen-space SSS as post-processing pass for desktop/high-end
4. Fallback to simplified translucency for low-end mobile

## Sources

- https://threejs.org/docs/#api/en/renderers/webgpu/WebGPURenderer
- https://docs.google.com/document/d/1s1nKZXFBTVsJlEkFH9hirxsR7SUh1WJ9SJs8lLQO8ro
