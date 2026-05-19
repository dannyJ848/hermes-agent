# ReSTIR-SSS real-time subsurface scattering

*Researched: 2026-04-06 13:25 CDT*

# ReSTIR Subsurface Scattering for Real-Time Path Tracing (HPG 2024)

**Source:** MircoWerner/ReSTIR-SSS (GitHub, 51 stars)
**Paper:** HPG 2024 by Mirco Werner, Vincent Schüßler, Carsten Dachsbacher

## Key Innovation
Applies Reservoir-based Spatio-Temporal Importance Resampling (ReSTIR) to subsurface light transport paths. Uses BSSRDF importance sampling to drastically reduce noise in real-time SSS path tracing.

## Why It Matters for SOMA
- Current SOMA SSS uses screen-space separable approximation (fast but inaccurate for complex tissue layers)
- ReSTIR-SSS provides physically-accurate SSS at real-time rates via path tracing
- Could replace the precomputed diffusion profile approach with dynamic, light-aware subsurface scattering
- Particularly impactful for anatomy where tissue translucency varies (skin vs muscle vs organ tissue)

## Technical Details
- Uses Vulkan (VkRaven framework) — would need WebGPU adaptation
- BSSRDF importance sampling replaces Gaussian diffusion profile approximation
- Spatio-temporal resampling reuses samples across frames (temporal) and pixels (spatial)
- Mitigates the classic SSS path tracing noise problem

## Adaptation Path for SOMA
1. Port BSSRDF sampling to WGSL shaders
2. Implement ReSTIR reservoir data structures as storage buffers
3. Replace current SSS pass in render pipeline
4. Quality/performance tradeoff via sample count tuning
5. Mobile feasibility: unknown — ReSTIR has memory overhead for reservoir buffers

## Also Found
- SIGGRAPH 2025 Advances course has a full "Real-Time Subsurface Scattering" PDF chapter
- Jaysmito101/AdvancedVulkanDemos has a free SSS reference implementation


## Sources

- https://github.com/MircoWerner/ReSTIR-SSS
- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- https://www.reddit.com/r/GraphicsProgramming/comments/1lfku5c/playing_around_with_realtime_subsurface/
