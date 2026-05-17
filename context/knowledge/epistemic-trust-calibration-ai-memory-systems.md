# epistemic-trust-calibration-ai-memory-systems

*Researched: 2026-04-05 08:34 CDT*

# Epistemic Trust Calibration in AI Systems

## Key Finding: Trust ≠ Reliance (Dissociation)

From arxiv:2601.16960 — "Do We Know What They Know We Know?" (UIUC, 2025):

**Trust and reliance are distinct, decoupled constructs:**
- **Trust** = psychological attitude (willingness to be vulnerable based on positive expectations of competence, benevolence, integrity)
- **Reliance** = behavioral act (depending on system outputs for decisions)

Users frequently rely on AI outputs despite lacking genuine trust. Reliance is driven by:
- Perceived expertise gaps
- Cognitive load reduction
- Accountability shifting for errors
- Social affordances (accessibility, anonymity, judgment-free)

Trust is shaped by **epistemic evaluations** (competence, domain expertise, reliability).
Reliance is driven by **social factors** (accessibility, fear of judgment, help-seeking anxiety).

## Relevance to Cerebrum Trust Scoring

Cerebrum's F-G-R Trust Tuple (Formation, Grounding, Recency) focuses on epistemic trust evaluation. This research validates that approach but suggests adding:
1. **Behavioral reliance tracking** — how often a fact is actually used vs. its trust score
2. **Social context weighting** — facts from trusted sources may be under-utilized due to access barriers
3. **Calibration gap detection** — when reliance patterns diverge from trust scores, flag for review

## Epistemic Friction as Design Pattern

From The Decision Lab: "Epistemic friction" — adding structured checkpoints that slow down information processing to improve accuracy. Applied to Cerebrum: before consolidating a fact from working→episodic→semantic memory, require verification that passes epistemic friction checks (cross-source validation, confidence threshold, recency confirmation).

## Actionable Integration
- Add `reliance_count` to Cerebrum semantic facts (track how often each fact is recalled/used)
- When `reliance_count` is high but trust score is low, investigate — the dissociation signal indicates either over-reliance or underrated knowledge
- Add epistemic friction gate between episodic and semantic tiers: require 2+ independent confirmations before promotion


## Sources

- https://arxiv.org/html/2601.16960v1
- https://thedecisionlab.com/big-problems/rebuilding-epistemic-trust-in-an-ai-mediated-internet
