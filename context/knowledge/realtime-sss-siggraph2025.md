# realtime-sss-siggraph2025

*Researched: 2026-04-06 13:12 CDT*

# Real-Time Subsurface Scattering for Anatomy Rendering (SIGGRAPH 2025 Update)

## Key Development: Hybrid ReSTIR-Path Tracing + Diffusion (SIGGRAPH 2025)

SIGGRAPH 2025 Advances in Real-Time Rendering course introduced a **novel hybrid solution** combining:
- **ReSTIR path tracing** for light transport sampling
- **Diffusion approximation** for fast subsurface scattering
- Achieves real-time SSS with physically-based accuracy

Source: `advances.realtimerendering.com/s2025/` (course session on SSS)

## Classical Foundation: GPU Gems 3 Chapter 14 (d'Eon & Luebke, NVIDIA)

### Why SSS Matters for Anatomy
- Skin is ~6% specular reflection; 94% enters subsurface layers
- Without SSS, anatomy looks "hard and dry" — light only reflects at entry point
- SSS gives soft appearance via light exiting in a 3D neighborhood around entry
- Critical for ears, nose, fingers where light transmits through thin tissue
- Human viewers are acutely sensitive to skin/face appearance

### Multi-Layer Skin Model (Donner & Jensen 2006)
1. **Oily surface layer** → specular reflection (Fresnel, rough)
2. **Epidermis** → slight scattering, pigment absorption
3. **Dermis** → heavy scattering, blood absorption (red tones)
4. **Subcutaneous fat** → strong forward scattering, diffusion

Single-layer models are INSUFFICIENT. Minimum 2-3 layers needed for realism.

### Practical Implementation Approaches

**Screen-Space Diffusion (d'Eon method):**
- Render irradiance to texture
- Apply Gaussian blur kernels at multiple scales (6 kernel sizes typical)
- Sum weighted contributions = diffusion approximation
- Each kernel corresponds to different scattering depth

**Texture-Space Diffusion:**
- Render unwrapped UV space
- Apply blurs in texture space
- Sample at render time
- Better quality but more memory

**For SOMA (mobile WebGPU):**
- Screen-space is more practical (lower memory)
- Can reduce kernel count from 6 to 3-4 for mobile perf
- Pre-integrated SSS (penumbra-based) is cheapest option
- Consider using SSS only on close-up views, skip for distant

### Open-Source SSS Reference
- `github.com/Jaysmito101/AdvancedVulkanDemos` includes SSS implementation
- Vulkan-based but shaders are portable to WGSL/WebGPU

## Application to SOMA 3D Anatomy Viewer

### Priority: Tissue-Specific SSS Profiles
- **Skin**: Moderate scattering, warm red tones from blood
- **Muscle**: Higher absorption, red/brown coloring
- **Organs**: Variable — liver (high absorption), lungs (low)
- **Bone**: Minimal SSS, mostly diffuse/specular

### Mobile Performance Budget
- Target: 2-4 SSS texture samples per pixel for tissue
- Use pre-integrated BRDF lookup textures
- LOD: disable SSS beyond certain camera distance
- WebGPU compute shaders can handle screen-space diffusion efficiently

## Sources
- SIGGRAPH 2025 Advances Course: advances.realtimerendering.com/s2025/
- GPU Gems 3 Ch.14: developer.nvidia.com/gpugems3/chapter-14
- Jaysmito101 AdvancedVulkanDemos SSS: github.com/Jaysmito101/AdvancedVulkanDemos


## Sources

- https://advances.realtimerendering.com/s2025/
- https://developer.nvidia.com/gpugems/gpugems3/part-iii-rendering/chapter-14-advanced-techniques-realistic-real-time-skin
- https://github.com/Jaysmito101/AdvancedVulkanDemos
