# clinical-agents-mcts-dual-memory-april-2026

*Researched: 2026-04-03 14:06 CDT*

# ClinicalAgents: MCTS + Dual-Memory for Clinical Decision Making (March 2026)

**Date:** April 3, 2026
**Source:** arXiv:2603.26182 (Ge et al., March 27 2026)
**Authors:** Zhuohan Ge, Haoyang Li, Yubo Wang, Nicole Hu, Chen Jason Zhang, Qing Li

## Key Innovation: MCTS Orchestration + Dual-Memory

### Problem
Existing LLM clinical approaches use static linear mappings (symptoms → diagnosis). Real clinicians use iterative, hypothesis-driven reasoning with backtracking.

### Solution: ClinicalAgents Framework

1. **MCTS-Based Orchestrator** — Models clinical reasoning as Monte Carlo Tree Search:
   - Generates diagnostic hypotheses (selection)
   - Actively verifies evidence (expansion)
   - Triggers backtracking when critical info is missing (backpropagation)
   - Non-linear: can revise hypotheses mid-reasoning

2. **Dual-Memory Architecture:**
   - **Working Memory (mutable):** Maintains evolving patient state for context-aware reasoning. Updated as new symptoms/observations are gathered.
   - **Experience Memory (static):** Retrieves clinical guidelines and historical cases via active feedback loop. Serves as the "knowledge base."

3. **Multi-Agent Roles:**
   - Orchestrator (MCTS controller)
   - Specialist agents (cardiology, neurology, etc.)
   - Evidence verifier agent
   - Memory retrieval agent

## Results
- State-of-the-art diagnostic accuracy
- Significantly better explainability than single-agent and multi-agent baselines
- Can backtrack from incorrect hypotheses (key advantage over chain-of-thought)

## SOMA Relevance (HIGH)

### Direct Architecture Mapping:

| ClinicalAgents | SOMA Equivalent | Status |
|---------------|-----------------|--------|
| Working Memory | User health profile (conditions, meds, labs) | Partially built |
| Experience Memory | Medical encyclopedia + FHIR knowledge | Encyclopedia seeded, FHIR planned |
| MCTS Orchestrator | AI assistant (Ask AI feature) | Basic, no backtracking |
| Specialist agents | Body-region specialists (heart, brain, etc.) | Not yet implemented |
| Evidence verifier | Lab-to-region inference | Mapped in FHIR architecture |

### Integration Path for SOMA:

1. **Phase 1 (Current):** Static medical content + simple AI queries per body region
2. **Phase 2:** Add Working Memory for user health state (track conditions, meds, symptoms per region)
3. **Phase 3:** Add Experience Memory using FHIR-mapped clinical guidelines (already designed in soma-fhir-to-3d-mapping-architecture.md)
4. **Phase 4:** MCTS-style hypothesis generation when user reports symptoms via body region selection

### Key Takeaway for SOMA's "My Health" Branch

When a user taps a body region and enters "My Health" → symptoms, SOMA should:
1. Load the user's conditions/medications for that region (Working Memory)
2. Retrieve relevant clinical guidelines for those conditions (Experience Memory)
3. Generate differential hypotheses based on symptoms + region
4. Suggest evidence-seeking questions (not just static content)
5. Allow backtracking if new information changes the picture

This transforms SOMA from a static anatomy reference to an active health reasoning partner — while staying within the "education not diagnosis" boundary.


## Sources

- https://arxiv.org/abs/2603.26182
