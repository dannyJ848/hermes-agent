# glm-5v-turbo

*Researched: 2026-04-01 20:26 CDT*

# GLM-5V-Turbo (Z.AI / Zhipu)

**Released:** April 1, 2026
**Type:** Multimodal Coding Foundation Model (Vision-Language)
**Provider:** Z.AI (Zhipu AI)

## Key Specs
- **Input:** Video / Image / Text / File
- **Output:** Text
- **Context:** 200K tokens
- **Max Output:** 128K tokens
- **API Endpoint:** `https://api.z.ai/api/coding/paas/v4/` (same as GLM-5.1)
- **Model ID:** `glm-5v-turbo`

## Capabilities
1. **Frontend Recreation:** Design mockup → complete runnable frontend project (pixel-level consistency for hi-fi, structural for wireframes)
2. **GUI Autonomous Exploration:** Browse websites, map transitions, collect assets, generate code from exploration (not just screenshots)
3. **Code Debugging:** Screenshot-based bug identification (layout issues, color mismatches, component overlap)
4. **Agent Integration:** Works with Claude Code and OpenClaw for full perceive→plan→execute loop
5. **Thinking Mode:** Multiple thinking modes for different scenarios
6. **Function Calling:** Tool invocation for external toolsets
7. **Context Caching:** Intelligent caching for long conversations
8. **Structured Output:** JSON/XML/code structure guarantees

## Architecture Innovations
- **Native Multimodal Fusion:** Continuous visual-text alignment from pretraining through post-training, new CogViT vision encoder, MTP architecture
- **30+ Task Joint RL:** Joint optimization across STEM, grounding, video, GUI agents, coding agents
- **Agentic Data Construction:** Multi-level, controllable, verifiable data system; agentic meta-capabilities injected during pretraining
- **Expanded Multimodal Toolchain:** Box drawing, screenshots, webpage reading, image understanding

## Official Skills
- Image Captioning
- Visual Grounding (bounding box)
- Document-Grounded Writing (PDF/Word → structured text)
- Resume Screening
- Prompt Generation (image/video → structured prompts)

## Benchmarks
- **Multimodal Coding/Agent Tasks:** Leading on design-to-code, visual code gen, multimodal retrieval/QA, visual exploration, AndroidWorld, WebVoyager
- **Pure-Text Coding:** Strong on CC-Bench-V2 (Backend, Frontend, Repo Exploration), PinchBench, ClawEval, ZClawBench
- Smaller parameter size than competitors but competitive/outperforming results

## Relevance to SOMA
- Screenshot-to-code capability could be used for rapid UI prototyping
- Visual grounding (bounding boxes) could enable anatomy region detection from medical images
- 200K context window allows processing large medical documents
- Document-grounded writing directly applicable to bilingual medical content generation
- Same Z.AI endpoint as current GLM-5.1 setup (seamless migration)

## Migration Notes
- Same API base URL as glm-5.1: `https://api.z.ai/api/coding/paas/v4/`
- Model string: `glm-5v-turbo`
- Vision calls can pass images directly for analysis
- Compatible with existing Z.AI API key

## Availability (Tested 2026-04-01)
- **BLOCKED on standard Z.AI plan.** Error 1311: "Your current subscription plan does not yet include access to GLM-5V-Turbo"
- HTTP 429 returned even though it's not a rate limit — it's a plan gating issue
- May require upgrading Z.AI subscription or waiting for rollout to current tier
- GLM-5.1 works fine on the same plan — only 5V-Turbo is gated
- Before attempting migration, test with: `curl -s https://api.z.ai/api/coding/paas/v4/chat/completions -H "Authorization: Bearer $GLM_API_KEY" -H "Content-Type: application/json" -d '{"model":"glm-5v-turbo","messages":[{"role":"user","content":"ping"}],"max_tokens":5}'`


## Sources

- https://docs.z.ai/guides/vlm/glm-5v-turbo
