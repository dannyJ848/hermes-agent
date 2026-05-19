# epistemic-trust-ai-agents-frameworks

*Researched: 2026-04-05 04:39 CDT*

# Epistemic Trust in AI Agents: Two Complementary Frameworks

## 1. Normative Framework for Trustworthy Epistemic AI Agents (Google DeepMind, March 2026)

**Paper:** arxiv:2603.02960 — "Architecting Trust in Artificial Epistemic Agents"

LLMs increasingly function as **epistemic agents** — entities that (1) autonomously pursue epistemic goals and (2) actively shape shared knowledge environments. The paper proposes a normative framework with three pillars:

### Three Verifiable Properties of Trustworthy Epistemic Agents:
1. **Demonstrable Epistemic Competence** — baseline competence, dynamic accuracy, information verification
2. **Falsifiability** — agents must be able to be proven wrong; claims must be testable
3. **Epistemically Virtuous Behavior** — honesty, truthfulness, truth-seeking behavior

### Key Risks Identified:
- **Cognitive deskilling** — over-reliance reduces human knowledge capacity
- **Epistemic drift** — gradual shift in knowledge norms from poorly calibrated agents
- **Epistemic silos** — reduced discovery from filter bubbles
- **Collective cognitive atrophy** — societal-level loss of knowledge practices

### Infrastructure Recommendations:
- Verifiable agent credentials and **provenance chains**
- Standardized communication and logging protocols
- "Knowledge sanctuaries" to protect human epistemic resilience
- Education for epistemic vigilance

**Relevance to Evey:** The 3-property framework maps directly to Cerebrum's trust scoring. "Information verification" = grounding checks. "Falsifiability" = claims must link to sources. "Epistemic virtue" = honest uncertainty reporting.

---

## 2. Trust Score Guardrailing Benchmark (Cleanlab, August 2025)

**Blog:** cleanlab.ai/blog/agent-tlm-hallucination-benchmarking

Cleanlab's Trustworthy Language Model (TLM) assigns real-time trust scores to every agent response. Benchmarked across 5 agent architectures (Act, ReAct Zero-shot, ReAct Few-shot, PlanAct, PlanReAct) using BOLAA benchmark (HotPotQA dataset).

### Key Results — Reduction in Incorrect Responses:
| Architecture | Error Reduction |
|---|---|
| Act (Zero-shot) | 56.2% |
| ReAct (Zero-shot) | 55.8% |
| ReAct (Few-shot) | 15.7% |
| PlanAct | 24.5% |
| PlanReAct | 10.0% |

### Insight:
Simpler agents (Act, ReAct zero-shot) benefit most from trust scoring because they have less internal reasoning to self-correct. Complex agents (PlanReAct) already self-correct via planning, so external trust scoring adds less marginal value.

**Application to Evey:** Trust scoring should be applied at the delegation boundary — when sub-agents return results, validate before accepting. Simpler delegate models benefit most from validation.

---

## Synthesis for Evey's Memory Architecture

Both sources converge on a key insight: **trust must be operationalized as measurable properties, not vibes.** The Google framework provides the theoretical grounding (competence, falsifiability, virtue). The Cleanlab benchmark proves that real-time trust scoring works in practice and catches hallucinations.

For Cerebrum's epistemic trust scoring, combine both:
- **Formation score** = source quality (analogous to provenance chains)
- **Grounding score** = verifiability against evidence (analogous to falsifiability)
- **Recency score** = temporal decay (standard memory practice)


## Sources

- https://arxiv.org/html/2603.02960v1
- https://cleanlab.ai/blog/agent-tlm-hallucination-benchmarking/
