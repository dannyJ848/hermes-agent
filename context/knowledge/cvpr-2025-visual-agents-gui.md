# cvpr-2025-visual-agents-gui

*Researched: 2026-04-05 03:51 CDT*

# CVPR 2025 Visual Agents for GUI — Key Papers & Trends

## Overview
CVPR 2025 featured a major wave of Visual Agent research — systems that perceive, understand, and act on visual interfaces (GUIs). This represents a shift from perception-only VLMs to action-capable agents.

## Top Papers

### 1. ShowUI (Vision-Language-Action for GUI)
- Single VLA model for GUI visual agent tasks
- Processes interleaved vision-language-action sequences
- Designed for precise element grounding and reliable interaction

### 2. GUI-Xplore
- Empowers generalizable GUI agents through exploration-based learning
- Focuses on cross-platform compatibility (web + mobile)
- Handles interaction histories across multiple observation-action cycles

### 3. SpiritSight Agent
- "Advanced GUI Agent with One Look" — single-screenshot grounding
- Efficiently processes high-resolution screenshots without losing critical details
- Novel architecture for the interleaved nature of VLA sequences

### 4. ComfyBench
- Benchmarks LLM-based agents in ComfyUI for autonomously designing collaborative AI systems
- Demonstrates multi-agent coordination on visual workflows

### 5. From Multimodal LLMs to Generalist Embodied Agents
- Survey/methods paper on transitioning from VLMs to generalist agents
- Covers lessons learned across domains

## Key Technical Challenges Identified
1. **Action-Perception Gap**: VLMs understand images but struggle to translate understanding into precise GUI actions (clicks, drags, typing)
2. **Action Space Challenge**: Defining the right action vocabulary for diverse interfaces
3. **Missing Embodiment**: GUI agents lack physical embodiment metaphors that ground robotic agents
4. **Cross-platform generalization**: Models trained on web often fail on mobile and vice versa
5. **High-resolution processing**: Screens contain dense information; naive downscaling loses critical details

## Trends
- Moving from perception-only to interaction-capable systems
- Specialized architectures for VLA (vision-language-action) sequences
- Exploration-based training replacing pure supervised approaches
- Single-screenshot grounding becoming viable (SpiritSight)
- Multi-agent coordination for complex visual workflows (ComfyBench)

## Relevance to Hermes Agent
- Hermes uses browser_vision for screen understanding — these advances could improve grounding accuracy
- Set-of-Mark (SoM) prompting is the foundation many of these build on
- Cross-platform generalization research is directly relevant to browser automation
- The action-perception gap explains why vision-based GUI agents still make mistakes


## Sources

- https://voxel51.com/blog/visual-agents-at-cvpr-2025
- https://arxiv.org/abs/2310.11441
- https://github.com/OSU-NLP-Group/GUI-Agents-Paper-List
