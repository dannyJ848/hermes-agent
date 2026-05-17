# real-time-sss-webgpu-anatomy-2025

*Researched: 2026-04-05 23:22 CDT*

# Real-Time Subsurface Scattering & WebGPU Advances for Anatomy Rendering

## SIGGRAPH 2025: Real-Time SSS Course
- **Key paper**: "Real-Time Subsurface Scattering" from SIGGRAPH 2025 Advances course
  - URL: https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- **Hybrid ReSTIR-Path Tracing + Diffusion**: Novel hybrid for real-time SSS via path tracing
  - Combines ReSTIR sampling with diffusion approximation
  - Video: https://www.youtube.com/watch?v=AtFBbMnUgoc

## Curated SSS Reference Library (Jaysmito101/AdvancedVulkanDemos)
Key techniques applicable to SOMA anatomy rendering:
1. **Separable SSS** (Jimenez et al.): Screen-space blur, 12-tap approximation — fastest for mobile
   - Paper: https://www.iryoku.com/separable-sss/downloads/Separable-Subsurface-Scattering.pdf
2. **Burley's Normalized Diffusion**: More physically accurate than Gaussian, used in Disney BSDF
   - Efficient screen-space variant: https://advances.realtimerendering.com/s2018/Efficient%20screen%20space%20subsurface%20scattering%20Siggraph%202018.pdf
3. **Approximating Translucency** (Barre-Brisebois GDC 2011): Cheap wrap-lighting trick for convincing SSS look
   - Best for SOMA mobile — minimal GPU cost
4. **Quantized Diffusion** (d'Eon): Most accurate diffusion profile, used in film
   - Paper: https://eugenedeon.com/pdfs/qd.pdf
5. **Real-Time Realistic Skin Translucency** (Jimenez et al.): Translucency via thickness maps
   - Paper: https://www.iryoku.com/translucency/downloads/Real-Time-Realistic-Skin-Translucency.pdf

## WebGPU Capabilities (Feb 2025)
- **Three.js WebGPU renderer**: Now production-ready, used in Expo 2025 installations
- **MLS-MPM fluid simulations**: Run at 60fps in browser on consumer hardware
- **In-browser AI models**: Kokoro TTS, Janus Pro multimodal, SmolVLM all run via WebGPU
- **Implication for SOMA**: Three.js WebGPU path enables native SSS shaders without WebGL limitations

## SOMA Integration Recommendations
1. **Tier 1 (mobile-safe)**: Approximating Translucency wrap-lighting + screen-space blur
2. **Tier 2 (desktop)**: Burley Normalized Diffusion in screen-space
3. **Tier 3 (future)**: Hybrid ReSTIR path-traced SSS when WebGPU compute shaders mature
4. **Migration path**: Move from WebGL to Three.js WebGPU renderer for shader flexibility


## Sources

- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- https://github.com/Jaysmito101/AdvancedVulkanDemos/blob/main/resources/subsurface_scattering.md
- https://www.webgpuexperts.com/best-webgpu-updates-february-2025
- https://www.youtube.com/watch?v=AtFBbMnUgoc
