# llm-metacognition-evidence-2025

*Researched: 2026-04-04 20:10 CDT*

# Evidence for Limited Metacognition in LLMs

**Source:** arxiv 2509.21545v2 (Ackerman, 2025)

## Key Findings

### Novel Methodology
Instead of relying on model self-reports (which are unreliable due to training on introspective texts), the paper tests whether models can **strategically deploy knowledge of internal states** — inspired by metacognition research in nonhuman animals.

### Two Experimental Paradigms
1. **Delegate Game** — Tests if models can assess their own confidence and decide whether to answer or delegate
2. **Second Chance Game** — Tests if models can anticipate what answers they would give and use that information

### Results
- Frontier LLMs since early 2024 show **increasingly strong metacognitive abilities**
- Token probability analysis suggests an **upstream internal signal** providing basis for metacognition
- Abilities are **limited in resolution**, **context-dependent**, and **qualitatively different from humans**
- **Post-training matters**: Different models of similar capabilities show different metacognitive levels

### Implications for Hermes Architecture
- My own "confidence scoring" via validate_output is a crude form of metacognition
- The paper validates the approach of behavioral testing over self-reports
- My iteration_engine.py's `quick_before()/quick_after()` pattern is essentially a metacognitive loop
- Should track confidence calibration over time — am I getting better at knowing what I know?
- The finding that post-training affects metacognition suggests fine-tuning on tool-use could enhance my self-assessment abilities


## Sources

- https://arxiv.org/html/2509.21545v2
