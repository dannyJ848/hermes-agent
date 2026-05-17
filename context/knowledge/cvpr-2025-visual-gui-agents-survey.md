# cvpr-2025-visual-gui-agents-survey

*Researched: 2026-04-05 04:06 CDT*

# CVPR 2025 Visual GUI Agents — Key Papers & Trends

## Top Papers from CVPR 2025

### 1. ShowUI: Vision-Language-Action for GUI
- Single VLA model for GUI visual agents
- Processes high-resolution screenshots efficiently
- Interleaved vision-language-action architecture

### 2. GUI-Xplore: Generalizable GUI Agents with One Exploration
- Focus on cross-platform generalization (web → mobile)
- One exploration strategy enables adaptation to unseen interfaces
- Addresses the "action-perception gap" between understanding and acting

### 3. SpiritSight Agent: Advanced GUI Agent with One Look
- Single-look GUI understanding (no multi-turn needed for basic tasks)
- Specialized element grounding for reliable interaction
- Handles complex visual interfaces

### 4. ComfyBench: Benchmarking LLM Agents in ComfyUI
- Evaluates LLM-based agents autonomously designing collaborative AI systems
- Tests multi-step planning in creative tool environments
- Measures agent capability in workflow orchestration

### 5. From Multimodal LLMs to Generalist Embodied Agents
- Survey paper on methods and lessons for transitioning from VLMs to embodied agents
- Covers the "missing embodiment" problem — perception without action capability

## Key Trends Identified

1. **Action-Perception Gap**: The core challenge is bridging visual understanding with reliable action execution. Models can describe screens but struggle to act precisely.

2. **Action Space Challenge**: Different platforms have different action vocabularies (click, type, scroll, drag). Unifying these is an open problem.

3. **Set-of-Mark (SoM) Evolution**: Visual prompting (marking UI elements with numbered labels) remains foundational. New approaches build on SoM for better grounding.

4. **Screen Stream Understanding (EMNLP 2025)**: History-aware agents that don't just see the current screen but understand the sequence of screens. Existing agents ignore screen history — this paper fixes that.

5. **UIPro (ICCV 2025)**: 20.6M task samples across multiple platforms for training GUI grounding capability. Massive clean dataset for imbuing strong GUI understanding.

6. **Cross-platform compatibility**: Web → mobile → desktop generalization is a major research focus.

## Implications for Agent Development
- Visual grounding remains the bottleneck — SoM + coordinate-free approaches (like GUI-Actor) are converging
- Screen history understanding is underexplored but critical for real agent workflows
- Training data scale matters — UIPro's 20.6M samples suggest data-hungry approaches win


## Sources

- https://voxel51.com/blog/visual-agents-at-cvpr-2025
- https://arxiv.org/abs/2310.11441
- https://openaccess.thecvf.com/content/ICCV2025/papers/Li_UIPro_Unleashing_Superior_Interaction_Capability_For_GUI_Agents_ICCV_2025_paper.pdf
