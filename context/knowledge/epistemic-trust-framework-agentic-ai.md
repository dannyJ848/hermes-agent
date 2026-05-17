# epistemic-trust-framework-agentic-ai

*Researched: 2026-04-05 08:22 CDT*

# Epistemic Trust Framework for Agentic AI

**Source:** Google DeepMind (Marchal et al., arXiv:2603.02960, March 2026)

## Key Framework: 3 Pillars of Epistemic Trustworthiness

### 1. Demonstrable Epistemic Competence
- **Baseline competence**: Agent must meet minimum accuracy thresholds
- **Dynamic accuracy**: Performance must be tracked over time, not just at evaluation
- **Information verification**: Claims must be traceable to sources

### 2. Falsifiability
- Agent outputs must be structured so they CAN be proven wrong
- Avoid unfalsifiable claims; provide confidence scores and evidence chains

### 3. Epistemically Virtuous Behavior
- **Honesty & truthfulness**: Don't fabricate or exaggerate
- **Truth-seeking**: Actively pursue accuracy, not just plausible-sounding answers

## Application to Evey's Cerebrum Memory System

This maps directly to our F-G-R Trust Tuple scoring:

| DeepMind Pillar | Evey Implementation |
|---|---|
| Baseline competence | Formation score (how was fact acquired?) |
| Dynamic accuracy | Grounding score (is it still true?) |
| Information verification | Provenance chain (source URL, session ID) |
| Falsifiability | Trust decay over time (unverified facts lose score) |
| Virtuous behavior | Cross-source validation before saving |

## Key Insight: "Epistemic Drift"
Poorly calibrated agents risk causing **epistemic drift** — gradual divergence from truth that's hard to detect because each small error seems plausible. This is exactly what happens when agents save unverified facts to long-term memory and build on them iteratively.

## Actionable Takeaway
The paper recommends **provenance chains** and **knowledge sanctuaries** — protected knowledge bases that are harder to corrupt. For Evey: facts with Trust > 0.8 should require extra validation before modification. Facts below 0.3 should trigger re-verification, not silent decay.


## Sources

- https://arxiv.org/html/2603.02960v1
- https://www.linkedin.com/pulse/trust-scoring-agentic-ai-when-autonomy-must-earned-assumed-avula-5nijc
