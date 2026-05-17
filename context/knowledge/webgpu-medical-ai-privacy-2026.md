# webgpu-medical-ai-privacy-2026

*Researched: 2026-04-06 15:37 CDT*

# WebGPU Accelerated Client-Side AI for Privacy-Preserving Dermatological Diagnostics

**Author:** Arpankumar Patel (2026)
**Source:** International Journal of Science and Research (IJSR)
**DOI:** https://doi.org/10.21275/SR26219113252

## Key Findings

1. **3.7x speedup** with WebGPU over WebGL 2.0 for MobileNetV2 image classification in browser
2. **Real-time 60 FPS** on mobile devices without thermal throttling — proves WebGPU compute shaders viable for on-device medical AI
3. **Local Differential Privacy (LDP)** integrated with privacy budget ε = 1.9, minimal accuracy loss
4. **Serverless architecture** — all inference runs client-side, no patient data leaves the device
5. Tested with MobileNetV2 and EfficientNetV2 architectures

## Relevance to SOMA

- **Directly validates SOMA's WebGPU strategy** for browser-based medical visualization
- The 3.7x speedup confirms WebGPU compute shaders are production-ready for medical imaging
- Privacy-preserving LDP layer pattern could be adapted for SOMA's patient data handling
- Mobile performance without thermal throttling is critical for SOMA's iOS deployment
- The serverless edge computing pattern aligns with SOMA's offline-first architecture

## SIGGRAPH 2025 SSS Advance

Also discovered: SIGGRAPH 2025 "Real-Time Subsurface Scattering" course (advances.realtimerendering.com) covers latest SSS techniques via hybrid ReSTIR-path tracing. Relevant for SOMA's tissue rendering pipeline — combined with WebGPU compute shaders, could enable real-time subsurface scattering on mobile for anatomical tissue visualization.


## Sources

- https://www.academia.edu/164964386/WebGPU_Accelerated_Client_Side_AI_for_Privacy_Preserving_Dermatological_Diagnostics_Performance_Benchmarking_and_Local_Differential_Privacy_Integration
- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
