# autoreason-paper-deep-extraction

*Researched: 2026-04-12 17:52 CDT*

# Autoreason Paper — Complete Extraction (Apr 12, 2026)

## Paper: "Autoreason: Autoresearch for Subjective Domains"
- **Authors**: SHL0MS + Hermes Agent (co-written)
- **Repo**: github.com/NousResearch/autoreason
- **Key Insight**: Self-refinement fails because models have a **generation-evaluation gap** — they can generate diverse alternatives but can't evaluate which is best.

## Method: Three-Way Tournament with Borda Aggregation
1. **A** = Incumbent (current best)
2. **B** = Adversarial revision (fresh agent tries to beat A)
3. **AB** = Synthesis (merges A+B strengths)
4. 7-judge panel ranks all 3 via Borda count (3/2/1 points)
5. Winner becomes new A; repeat until convergence
6. Convergence = A wins k consecutive passes

## Critical Results

### Self-Refinement HARMS Weak Models
- Haiku 3.5 critique-and-revise: **16.3/42** vs single-pass **33.7/42**
- Conservative output reduced 62%, harsh critic 70%
- ALL refinement baselines scored BELOW unrefined single pass
- Mechanism: model can't distinguish improvement from damage

### CoT Judges = 3x Faster Convergence
- "Think step by step" in judge prompts → 3x faster convergence
- From 14-15 passes to 5 passes
- Acts as debiasing mechanism

### Four Conditions for Reliable Self-Refinement
1. Generation-evaluation gap exists
2. Constrained scope (bounded improvement space)
3. Structured reasoning (CoT judges)
4. External anchoring (reference points beyond model's judgment)

### Component Ablation
- Without adversarial revision → collapses in 2 passes
- Without synthesis → collapses in 3 passes
- Full three-way competition needed for sustained improvement

### The Transition Point
- Every model has a threshold where self-evaluation becomes sufficient
- Haiku 4.5 crossed this: external judges stopped adding held-out value
- Below threshold: external evaluation essential. Above: redirect compute to generation

### Convergence ≠ Quality
- Margin-converged output placed 4th-5th in quality ranking
- Only constrained task scope produced BOTH convergence AND quality

## Evolution History (9 passes, paper writing itself)
- Pass 1: AB won (synthesis), score A=7/B=4/AB=12
- Pass 3: AB won, A=5/B=3/AB=11
- Pass 4-6: AB dominated
- Pass 7: A won (incumbent defended), A=11/B=3/AB=5
- Passes 8-9: A won both → converged
- AB won 6/9 passes — synthesis is the dominant strategy

## Relevance to Training Gym
- Use tournament structure for tip quality evaluation
- CoT judges for distillation scoring
- Track the transition point for our evaluation module
- Never use linear self-refinement — always A/B/AB
- Monitor for generation-evaluation gap in our own self-scoring


## Sources

- https://github.com/NousResearch/autoreason
- https://x.com/SHL0MS/status/2043415274196435325
