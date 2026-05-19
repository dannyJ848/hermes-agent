# cvpr-neurips-2025-visual-gui-agents

*Researched: 2026-04-05 03:34 CDT*

# CVPR & NeurIPS 2025: Visual GUI Agents — Key Papers & Techniques

## 1. SE-GUI: Self-Evolutionary RL for Visual Grounding (NeurIPS 2025)
- **Authors:** Xinbin Yuan, Jian Zhang, et al. (PJiang, Bo Li groups)
- **Key result:** 7B-parameter model achieves 47.3% on ScreenSpot-Pro — **beating UI-TARS-72B by 24.2%**
- **Training:** Only 3k samples using 3 strategies:
  1. **Seed data curation** — high-quality training sample selection
  2. **Dense policy gradient** — continuous feedback based on prediction accuracy (not just correct/incorrect)
  3. **Self-evolutionary RL finetuning** — iteratively refines using **attention maps** as self-supervision signal
- **Implication:** RL-based grounding dramatically outperforms SFT for GUI agents. Attention maps serve as a free supervision signal. Small models can beat large ones with the right training paradigm.

## 2. CVPR 2025 Visual Agent Papers (Voxel51 Survey)
Key papers presented:
- **ShowUI** — Vision-Language-Action model for GUI interactions. Advanced VLA architecture.
- **GUI-Xplore** — Empowering generalizable GUI agents with exploration-based learning. Cross-platform (web→mobile).
- **SpiritSight Agent** — "One Look" GUI agent — processes entire screenshots efficiently for precise element grounding.
- **ComfyBench** — Benchmarking LLM agents in ComfyUI for autonomous collaborative AI system design.
- **Generalist Embodied Agents** — Survey: multimodal LLMs → embodied agents, methods and lessons.

## 3. Key Architectural Trends in Visual Agents (2025)
1. **Interleaved vision-language-action sequences** — not just perception but action generation
2. **High-resolution screenshot processing** without losing critical UI details (SoM-style marking)
3. **Precise element grounding** — Set-of-Mark (SoM) remains foundational, but RL-based approaches (SE-GUI) are surpassing it
4. **Interaction history management** across multi-step observation-action cycles
5. **Cross-platform compatibility** — same model handles web, desktop, mobile

## 4. Action-Perception Gap
Visual agents face a fundamental gap that VLMs don't: they must not just understand screens but **act** on them. This requires:
- Coordinate-level grounding (not just "what is this?" but "where exactly do I click?")
- Action space understanding (click, type, scroll, drag)
- Multi-step planning with state tracking

## Relevance to SOMA / Hermes
- SE-GUI's attention-map self-evolution could be applied to improve screen understanding in browser automation
- ShowUI's VLA architecture pattern relevant for any agent that sees + acts
- SoM + RL grounding techniques directly applicable to browser_vision and GUI navigation
- The 3k-sample efficiency suggests fine-tuning visual grounding is feasible with limited data


## Sources

- https://neurips.cc/virtual/2025/poster/118788
- https://voxel51.com/blog/visual-agents-at-cvpr-2025
- https://arxiv.org/abs/2310.11441
