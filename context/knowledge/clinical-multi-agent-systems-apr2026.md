# clinical-multi-agent-systems-apr2026

*Researched: 2026-04-02 21:40 CDT*

# Clinical Multi-Agent Systems for Medical Apps (April 2026)

## VoxTell — Free-Text 3D Medical Segmentation
- **Repo**: MIC-DKFZ/VoxTell (from the nnU-Net team)
- **What**: Open-vocabulary, free-text-prompted 3D segmentation. User provides natural language ("left kidney", "hepatic tumor") and model produces 3D binary mask from CT/MRI volume
- **Architecture**: Vision-language fusion — 3D U-Net/ViT backbone + CLIP text encoder + cross-attention decoder
- **Modality**: CT primary, MRI likely supported
- **SOMA Relevance**: Could power interactive "click to segment" anatomy exploration. User selects region in 3D viewer, VoxTell segments it. However, inference requires GPU — not mobile-ready yet.

## Clinical Multi-Agent Architecture Patterns

### Common Agent Roles in Clinical Systems
1. **Orchestrator/Router** — task decomposition, delegation, conflict resolution
2. **History & Intake Agent** — patient data collection, symptom extraction
3. **Diagnostic Reasoning Agent** — differential diagnosis generation
4. **Treatment Planning Agent** — medication/therapy recommendations
5. **Verification/Safety Agent** — drug interaction, contraindication checking
6. **Communication Agent** — patient-facing output, readability, empathy

### Coordination Mechanisms
| Pattern | Use Case |
|---|---|
| Sequential pipeline | Diagnosis workflows (intake → reasoning → plan → verify) |
| Debate/Adversarial | Differential diagnosis (multiple proposals, judge resolves) |
| Hierarchical | Multi-comorbidity cases (specialist agents per condition) |
| Red-team/Critic | Drug safety checks before delivery |
| Tool-augmented | External APIs (drug DBs, calculators, guidelines) |

### Key Benchmarking Findings
- Single-agent LLMs approach clinician-level on structured Q&A but degrade on multi-step reasoning
- Multi-agent systems improve consistency and reduce hallucination vs single-agent
- Agents still fail on: rare conditions, multi-morbidity, longitudinal reasoning, guideline conflicts
- **Tool use often helps more than agent count** — adding retrieval/calculators > adding more agents

### Proposed SOMA Multi-Agent Architecture
```
SOMA Orchestrator (routes queries, enforces scope)
├── Education Agent — anatomy, pathology, pharmacology explanations
├── Health Data Agent — personal conditions, medications, lab results
├── Safety Verification Agent — drug interactions, contraindications
├── Cultural/Language Agent — bilingual adaptation, health literacy adjustment
└── Explanation Agent — patient-friendly output, empathy calibration
```

### Safety Considerations for SOMA
1. **Never provide diagnoses** — education only, clear disclaimers
2. **Safety agent must run on all medication interactions** — non-negotiable
3. **Cultural sensitivity** — Spanish-speaking, low-income context awareness
4. **Health literacy adjustment** — plain language at appropriate reading level
5. **Hallucination guardrails** — verify all medical claims against structured databases (BioMCP)


## Sources

- https://github.com/MIC-DKFZ/VoxTell
- arxiv 2603.26182 (ClinicalAgents)
- Nature digital medicine LLM agent benchmarking
