# realtime-sss-advances-2025

*Researched: 2026-04-06 00:43 CDT*

# Real-Time Subsurface Scattering Advances (2025)

## SIGGRAPH 2025: Advances in Real-Time Rendering
- **Source**: SIGGRAPH 2025 course "Advances in Real-Time Rendering in Games"
- **Key paper**: "Real-Time Subsurface Scattering" — hybrid ReSTIR Path Tracing + Diffusion approach
- Combines path tracing (for accuracy) with screen-space diffusion approximation (for performance)
- Achieves significantly better skin detail matching to ground truth vs prior methods
- Reference: https://advances.realtimerendering.com/s2025/

## NVIDIA RTX Skin (GDC 2025)
- First implementation of SSS in ray-traced gaming via RTX Remix
- Part of NVIDIA RTX Kit neural rendering suite
- Light transmits and scatters through skin geometry realistically
- Built on RTX 50 Series hardware

## NVIDIA Neural Shaders (DirectX 12, April 2025)
- Cooperative Vectors support added to DirectX/HLSL via Agility SDK Preview
- Enables neural networks inside programmable shaders via RTX Tensor Cores
- Applications: textures, materials, lighting — directly relevant to SSS shader optimization
- Could enable learned SSS profiles that outperform analytical models

## Key Insight for SOMA
The hybrid ReSTIR+diffusion approach is the state-of-the-art for real-time SSS. For WebGPU/mobile:
- Can't use ray tracing, but the **diffusion approximation** part (screen-space blur with profile kernels) is GPU-friendly
- Neural shaders suggest future possibility of learned SSS on mobile GPUs
- The SIGGRAPH paper's diffusion component maps well to SOMA's existing SSS shader approach (separable Gaussian blur)
- Potential upgrade path: replace fixed Gaussian kernels with **normalized diffusion profiles** from the paper

## Sources
- SIGGRAPH 2025 course: https://advances.realtimerendering.com/s2025/
- NVIDIA RTX Skin: https://developer.nvidia.com/blog/nvidia-rtx-advances-with-neural-rendering-and-digital-human-technologies-at-gdc-2025/
- Community implementations: https://github.com/Jaysmito101/AdvancedVulkanDemos (Vulkan SSS demos)

## Sources

- https://advances.realtimerendering.com/s2025/
- https://developer.nvidia.com/blog/nvidia-rtx-advances-with-neural-rendering-and-digital-human-technologies-at-gdc-2025/
- https://github.com/Jaysmito101/AdvancedVulkanDemos
