# visual-grounding-som-survey-2025

*Researched: 2026-04-05 03:39 CDT*

# Visual Grounding in VLMs: SoM Evolution & GUI Agent Grounding (2025 Survey)

## Key Finding
Pantazopoulos & Özyiğit (Sep 2025) published a comprehensive survey "Towards Understanding Visual Grounding in Visual Language Models" (arXiv:2509.10345) covering the full landscape of visual grounding in modern VLMs.

## Set-of-Mark (SoM) — Microsoft (Yang et al., 2023, 638 citations)
- **Core technique:** Overlay numbered spatial marks on segmented image regions, enabling LMMs (GPT-4V, etc.) to reference specific objects by number
- **Pipeline:** Segment image → assign marks → feed marked image to VLM → VLM references marks in answers
- **Impact:** Enables visual grounding without coordinate-based training — the model "sees" numbered regions

## Evolution for GUI Agents (2025)
1. **ICLR 2025 paper** — Leveraging Visual Prompts to Enable MLLMs: Uses SoM prompting to enhance GPT-4V's recognition of objects referenced by visual prompts in agent contexts
2. **GUI-Actor (Microsoft, NeurIPS 2025)** — Coordinate-free visual grounding, moving beyond SoM to direct action prediction without explicit coordinate output
3. **SegAgent (CVPR 2025)** — Pixel-level understanding in MLLMs via segmentation; addresses that VQA and visual grounding remain "too coarse" for fine-grained pixel comprehension

## Key Insight for Agent Design
SoM is the **bridge technique** between:
- **OCR-based agents** (read text, click coordinates) — brittle, resolution-dependent
- **Pure VLM agents** (describe screenshot, predict action) — imprecise, hallucination-prone

SoM gives VLMs a "vocabulary of regions" — the model can say "click region 7" instead of "click at (342, 567)". This is more robust because:
- Segmentation is class-agnostic (works on any UI)
- Number marks are language tokens VLMs handle well
- Reduces coordinate hallucination

## Application to SOMA/Hermes
For Hermes browser automation: SoM-style annotation (like `browser_vision` with `annotate=true`) is already implemented. The trend in 2025 is toward **learned grounding** — training VLMs to ground without explicit marks. Future: Hermes could use lightweight segmentation + number overlay for more reliable browser interaction.

## Sources
- arXiv:2310.11441 (SoM original)
- arXiv:2509.10345 (Visual Grounding survey, Sep 2025)
- ICLR 2025: Visual Prompts for MLLMs
- CVPR 2025: SegAgent (pixel understanding)
- GUI-Actor (NeurIPS 2025, Microsoft)


## Sources

- https://arxiv.org/abs/2509.10345
- https://arxiv.org/abs/2310.11441
- https://github.com/microsoft/SoM
