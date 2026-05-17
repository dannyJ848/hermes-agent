# cvpr-2025-visual-gui-agents

*Researched: 2026-04-05 04:09 CDT*

# CVPR 2025 Visual GUI Agents — Key Papers & Trends

## Overview
CVPR 2025 featured a wave of Visual Agent papers标志着从学术好奇心到实际技术的转变。关键的互补研究包括：

## Top Papers from CVPR 2025

### 1. ShowUI (Vision-Language-Action for GUI)
- Single VLA model for GUI visual agent tasks
- Handles interleaved vision-language-action sequences
- Efficient high-resolution screenshot processing

### 2. GUI-Xplore (Generalizable GUI Agents)
- Empowers generalizable GUI agents through exploration-based learning
- Focus on cross-platform compatibility (web + mobile)
- One exploration paradigm for diverse interfaces

### 3. SpiritSight Agent
- "One Look" approach — advanced GUI agent with minimal observation
- Precise element grounding for reliable interaction
- Manages interaction histories across multiple observation-action cycles

### 4. ComfyBench (LLM Agents in ComfyUI)
- Benchmarks LLM-based agents in collaborative AI systems
- Tests autonomous design of AI workflows within ComfyUI

### 5. From Multimodal LLMs to Generalist Embodied Agents
- Methods and lessons for transitioning from perception-only to interaction-capable agents
- Addresses the Action-Perception Gap and Action Space Challenge

## GUI Agent Autonomy Levels (GAL) Framework (arXiv:2602.11514)
Proposed 6-level autonomy scale (inspired by SAE driving levels):
- **Level 0**: No automation (manual interaction)
- **Level 1**: Minimal assistance (suggestions)
- **Level 2**: Basic automation (single-step actions)
- **Level 3**: Conditional automation (multi-step with oversight)
- **Level 4**: High automation (autonomous with fallback)
- **Level 5**: Full automation (end-to-end autonomous)

## Key Industry Deployments
- **OpenAI ChatGPT Atlas**: AI browser for web navigation
- **Perplexity Comet**: Autonomous web browsing agent
- **Anthropic Claude Computer Use**: Full desktop environment control
- **Doubao AI Phone**: On-device mobile GUI agent

## Relevance to Hermes Agent
Hermes's browser tools (browser_navigate, browser_snapshot, browser_click) implement Level 2-3 autonomy. The GAL framework provides a roadmap for upgrading to Level 4-5. ShowUI and SpiritSight's "one look" approach could inform more efficient snapshot-to-action pipelines.


## Sources

- https://voxel51.com/blog/visual-agents-at-cvpr-2025
- https://arxiv.org/html/2602.11514
