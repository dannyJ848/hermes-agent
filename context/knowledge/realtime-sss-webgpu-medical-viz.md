# realtime-sss-webgpu-medical-viz

*Researched: 2026-04-06 05:25 CDT*

# Real-Time Subsurface Scattering for Medical Visualization

## Key Findings (April 2026 Research)

### SIGGRAPH 2025: Hybrid ReSTIR-Path Tracing + Diffusion for SSS
- **Source**: "Real-Time Subsurface Scattering" — SIGGRAPH 2025 Advances course
- **URL**: https://advances.realtimerendering.com/s2025/
- **Key innovation**: Hybrid approach combining ReSTIR path tracing with diffusion approximation for real-time SSS
- **Relevance to SOMA**: Could enable realistic tissue translucency in 3D anatomy viewer without offline rendering

### WebGPU + Medical AI (Feb 2026)
- **Paper**: "WebGPU Accelerated Client-Side AI for Privacy Preserving Dermatological Diagnostics"
- **Published**: Feb 23, 2026 by Arpankumar Patel (ResearchGate)
- **Key concept**: Using WebGPU for on-device medical AI inference with local differential privacy
- **Relevance to SOMA**: Proves WebGPU is viable for client-side medical computation — validates SOMA's architecture

### Khronos "3D on the Web" Event (GDC 2025, March 19)
- **Topic**: Large Scale Scientific Visualization with WebGL/WebGPU
- **Relevance**: Khronos actively pushing WebGPU for scientific/medical visualization

### NVIDIA GPU Gems Ch.16 — SSS Approximation Techniques
- **Wrap lighting**: `max(0, (dot(L,N) + wrap) / (1+wrap))` — simplest SSS approximation
- **Texture LUT approach**: Encode diffuse+scatter+specular in 2D lookup table indexed by N·L and N·H
- **Color shift trick**: Smooth transition to red at light-shadow boundary simulates blood scattering in skin
- **Performance**: All fragment-shader level, works on mobile GPUs

## Application to SOMA Architecture

1. **Immediate**: Use wrap lighting + scatter color shift for tissue rendering (minimal GPU cost)
2. **Medium**: Implement texture LUT approach for organ surfaces (liver, kidneys show translucency)
3. **Future**: When WebGPU compute shaders mature, adopt diffusion-based SSS from SIGGRAPH 2025 paper
4. **Validation**: WebGPU medical AI paper confirms the platform is production-ready for medical apps

## Shader Code Reference (Wrap Lighting + Scatter)
```glsl
float wrap = 0.2;
float scatterWidth = 0.3;
float3 scatterColor = float3(0.15, 0.0, 0.0);
float NdotL_wrap = (NdotL + wrap) / (1.0 + wrap);
float diffuse = max(NdotL_wrap, 0.0);
float scatter = smoothstep(0.0, scatterWidth, NdotL_wrap) * smoothstep(scatterWidth * 2.0, scatterWidth, NdotL_wrap);
color.rgb = diffuse + scatter * scatterColor;
```


## Sources

- https://advances.realtimerendering.com/s2025/
- https://developer.nvidia.com/gpugems/gpugems/part-iii-materials/chapter-16-real-time-approximations-subsurface-scattering
- https://www.researchgate.net/publication/401110730
- https://www.youtube.com/watch?v=HzcFzCkt5aU
