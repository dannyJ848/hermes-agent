# epistemic-trust-fpf-framework

*Researched: 2026-04-05 06:02 CDT*

# First Principles Framework (FPF) for Epistemic Trust in AI-Assisted Engineering

**Source:** arXiv:2601.21116 — Gilda & Gilda (2025)

## Key Concepts

### 1. F-G-R Trust Tuple
Every claim gets a 3-tuple: **(Formation, Grounding, Recency)** — how the belief was formed, what evidence grounds it, and how recently it was validated.

### 2. Gödel t-Norm Conservative Aggregation
When combining evidence from multiple sources, use the **minimum** confidence (Gödel t-norm) rather than averaging. This prevents weak evidence from inflating overall confidence. Our epistemic-trust-scoring skill already uses this principle.

### 3. Evidence Decay Tracking
Claims have **temporal validity**. The paper found 20-25% of architectural decisions had stale evidence within 2 months. Automated decay tracking surfaces stale assumptions before failures occur. This directly supports Cerebrum's memory_decay mechanism.

### 4. Gamma Invariant Quintet
Five invariants any valid trust aggregation operator must satisfy — ensures mathematical rigor in trust scoring.

### 5. ADI Reasoning Cycle
**Assess → Decide → Implement** — each step carries epistemic metadata forward, preventing trust inflation through the pipeline.

## Application to Cerebrum/Hermes
- Our epistemic-trust-scoring skill's F-G-R Trust Tuple aligns with this paper's formalization
- Evidence decay should be automated: facts lose grounding score over time if not re-verified
- Conservative aggregation (min-based) should be the default for multi-source claims
- The ADI cycle maps to our middleware-reasoning-chain: assess evidence quality before acting

## Research Directions from Paper
- Learnable aggregation operators (ML-based trust scoring)
- Federated evidence sharing across agents
- SMT-based automated claim validation


## Sources

- https://arxiv.org/html/2601.21116v1
