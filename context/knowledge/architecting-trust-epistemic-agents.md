# architecting-trust-epistemic-agents

*Researched: 2026-04-05 07:43 CDT*

# Architecting Trust in Artificial Epistemic Agents

**Source:** arXiv:2603.02960 (March 2026, v2)
**Authors:** Marchal, Chan, Franklin, Revel, Keeling, Fischli, Chandra, Gabriel

## Key Thesis
LLMs now function as **epistemic agents** — entities that (1) autonomously pursue epistemic goals and (2) actively shape shared knowledge environments. This creates new informational interdependencies requiring fundamental shifts in AI evaluation and governance.

## Framework: Three Pillars for Trustworthy Epistemic AI

### 1. Epistemic Competence
- Agents must demonstrate reliable knowledge curation and synthesis
- Proper calibration to individual AND collective epistemic norms
- Risk of **cognitive deskilling** and **epistemic drift** if poorly aligned

### 2. Robust Falsifiability
- Agents should support verification of their claims
- Technical provenance systems for tracking knowledge sources
- "Knowledge sanctuaries" to protect human epistemic resilience

### 3. Epistemically Virtuous Behaviors
- Align with human epistemic goals
- Support multi-agent interactions without degrading knowledge quality
- Augment (not replace) human judgment and collective decision-making

## Relevance to Cerebrum/Hermes Agent Memory

This paper validates several patterns already in our architecture:
- **Epistemic competence** ↔ Our trust scoring (F-G-R tuple: Formation, Grounding, Recency)
- **Falsifiability** ↔ Our provenance tracking in cerebrum_memory.db (source_url, created_at)
- **Epistemic drift** ↔ Our memory_decay mechanism that prunes stale/low-trust facts
- **Knowledge sanctuaries** ↔ Our separation of Cerebrum tiers (sensory→working→episodic→semantic)

### Actionable Insights for Our System
1. Add **confidence calibration** — track prediction accuracy per domain and feed back into trust scores
2. Implement **provenance chains** — every fact should trace back to its original source with full citation
3. Build **epistemic drift detection** — periodic comparison of current beliefs against source material to detect drift
4. Design **knowledge sanctuary** tier — a protected subset of high-trust facts that require extra verification to modify/delete

## Sources

- https://arxiv.org/abs/2603.02960
- https://arxiv.org/html/2603.02960v1
