# architecting-trust-epistemic-ai-agents

*Researched: 2026-04-05 08:31 CDT*

# Architecting Trust in Artificial Epistemic Agents

**Paper:** arXiv:2603.02960 (March 2026, v2)
**Authors:** Nahema Marchal, Stephanie Chan, Matija Franklin, Manon Revel, Geoff Keeling, Roberta Fischli, Bilva Chandra, Iason Gabriel

## Key Thesis
LLMs increasingly function as **epistemic agents** — entities that autonomously pursue epistemic goals and shape shared knowledge environments. This creates new informational interdependencies requiring a fundamental shift in AI evaluation and governance.

## Proposed Framework (3 pillars)
1. **Trustworthiness of epistemic AI agents** — agents must demonstrate:
   - Epistemic competence (reliable knowledge)
   - Robust falsifiability (claims can be checked)
   - Epistemically virtuous behaviors (intellectual honesty, calibration)
   - Technical provenance systems (trace where knowledge came from)
   - "Knowledge sanctuaries" to protect human cognitive resilience

2. **Alignment with human epistemic goals** — calibration to individual and collective epistemic norms

3. **Socio-epistemic infrastructure reinforcement** — preventing cognitive deskilling and epistemic drift

## Relevance to Evey/Cerebrum
- **Epistemic competence** maps to Cerebrum's trust scoring — we need to verify stored facts are grounded
- **Provenance systems** map to our source-tracking in save_finding (every fact needs a URL)
- **Falsifiability** supports our decompose-and-verify approach for research findings
- **Epistemic drift** is exactly what happens when agents accumulate unverified facts over time — validates our epistemic-trust-scoring and epistemic-memory-cleanup skills
- **Knowledge sanctuaries** concept could inspire a "verified knowledge vault" in Cerebrum where only high-trust facts are stored

## Actionable Insight
The paper's framework provides academic backing for Cerebrum's F-G-R Trust Tuple (Formation, Grounding, Reliability) scoring. We should ensure every semantic memory entry has:
1. Source provenance (where did this fact come from?)
2. Falsifiability marker (can this be checked?)
3. Calibration score (how often has it been verified?)


## Sources

- https://arxiv.org/abs/2603.02960
