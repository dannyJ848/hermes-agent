# set-of-mark-visual-grounding-for-gui-agents

*Researched: 2026-04-05 03:58 CDT*

# Set-of-Mark (SoM) Visual Prompting for GUI Agents

## Foundational Paper
**Set-of-Mark Prompting Unleashes Extraordinary Visual Grounding in GPT-4V** (arXiv:2310.11441, Oct 2023)
Authors: Jianwei Yang, Hao Zhang, Feng Li, Xueyan Zou, Chunyuan Li, Jianfeng Gao (Microsoft)

### Core Technique
SoM overlays alphanumeric marks, masks, and boxes onto image regions segmented by SAM/SEEM. GPT-4V then references these numbered marks to perform precise visual grounding. Zero-shot GPT-4V + SoM outperforms fully fine-tuned SOTA on RefCOCog.

**Pipeline:**
1. Segmentation model (SAM/SEEM) partitions image into regions at multiple granularities
2. Each region gets a mark (alphanumeric label + colored mask/box)
3. Marked image is fed to LMM as input
4. LMM references mark IDs in its response for precise grounding

### Key Design Choices
- **Granularity levels**: Fine (all segments), coarse (merged), or auto
- **Mark types**: Alphanumerics, colored masks, bounding boxes
- **Zero-shot capable**: No training required, purely prompt-based
- **Open-source**: Code at github.com/microsoft/SoM

### Evolution to GUI Agents (2024-2025)

**GUI-Actor** (Microsoft, NeurIPS 2025, arXiv:2506.03143):
- Coordinate-free visual grounding — no need to output pixel coordinates
- Attention-based action head replaces coordinate regression
- Includes a verifier to validate grounding quality
- Outperforms coordinate-generation approaches on GUI benchmarks
- Better generalization across platforms (web, mobile, desktop)

**SE-GUI** (NeurIPS 2025):
- Self-evolutionary training for GUI grounding
- Only 3K training samples needed
- 7B parameter model beats 72B models on grounding benchmarks
- Self-evolutionary data pipeline generates high-quality training pairs

### Relevance to Hermes Agent
- SoM could enhance `browser_vision` and `vision_analyze` tools for more precise element identification
- GUI-Actor's coordinate-free approach aligns with Hermes's ref-based (@eN) element selection
- Self-evolutionary training (SE-GUI) pattern could apply to improving Hermes's tool-use accuracy with minimal data

### Integration Ideas
1. **Annotated screenshots**: Apply SoM marks to browser screenshots before vision analysis for more accurate element grounding
2. **Hybrid ref+SoM**: Combine DOM-based refs with visual marks for redundant element identification
3. **Training data**: Use SE-GUI's self-evolutionary approach to generate Hermes-specific grounding training data


## Sources

- https://arxiv.org/abs/2310.11441
- https://github.com/microsoft/SoM
- https://arxiv.org/abs/2506.03143
- https://neurips.cc/virtual/2025/poster/118788
