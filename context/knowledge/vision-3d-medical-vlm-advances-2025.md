# vision-3d-medical-vlm-advances-2025

*Researched: 2026-04-07 11:31 CDT*

# Vision & 3D Medical VLM Advances (2025-2026)

## Key Papers

### 1. BTB3D: Better Tokens for Better 3D (NeurIPS 2025)
- Causal convolutional encoder-decoder for VLM in 3D medical imaging
- Generates improved token representations from CT volumes
- Relevance to SOMA: Better 3D tokenization could improve anatomy understanding

### 2. Anatomy-VLM (WACV 2026, arXiv:2511.08402)
- Fine-grained VLM that localizes anatomical features from medical images
- Multi-scale information alignment: localize → enrich with structured knowledge → predict
- Zero-shot anatomy-wise interpretation capability
- Relevance to SOMA: Pipeline mirrors SOMA's needed architecture (anatomical region detection + bilingual enrichment)

### 3. Universal Visual Grounding for GUI Agents (ICLR 2025, 278 citations)
- Human-like embodiment: perceive visually, perform pixel-level operations
- Relevance: GUI grounding is structurally identical to 3D anatomy selection

### 4. GUI-G1: R1-Zero-Like Training (NeurIPS 2025)
- Online RL with explicit chain-of-thought for visual grounding
- No supervised data needed
- Relevance: RL approach adaptable for anatomy selection training

### 5. Aria-UI (ACL 2025, 113 citations)
- SOTA visual grounding for GUI instructions
- Outperforms vision-only and AXTree baselines
- Relevance: Architecture patterns applicable to SOMA element picking

### 6. CT-GRAPH (ICCV 2025 Workshop)
- Hierarchical graph attention for anatomy-guided CT reports
- Relevance: Hierarchical graph structure for anatomy relationships

## Cross-Domain Synthesis
GUI visual grounding techniques map directly to 3D anatomy:
- Bounding box prediction → anatomy region highlighting
- Pixel-level operations → vertex/face selection on meshes
- Multi-step grounding → hierarchical navigation (organ → lobe → segment)


## Sources

- https://arxiv.org/abs/2511.08402
- https://openreview.net/forum?id=jSeWBdH0Xx
- https://openreview.net/forum?id=kxnoqaisCT
- https://aclanthology.org/2025.findings-acl.1152
