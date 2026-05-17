# self-improving-agent-architectures-2025-2026

*Researched: 2026-04-04 21:26 CDT*

# Self-Improving Agent Architectures (2025-2026)

## Key Research Streams

### 1. Constitutional Self-Modification (Two-Tier Architecture)
- **Core Pattern:** Agents can modify *soft* behaviors (prompts, strategies, tool preferences) but CANNOT modify an **invariant safety layer** (frozen model, formal verifier, or hardcoded rules)
- **Self-Refine** (arXiv:2303.17651): Generate → Critique → Refine loop, no training needed
- **SERAC** (arXiv:2206.06520): Memory-based model editing via scope modules
- **RepE** (arXiv:2310.01405): Representation engineering to control honesty, fairness at activation level
- **Key Insight:** The two-tier architecture (mutable soft layer + immutable safety layer) prevents agents from amending away their own safety constraints

### 2. Metacognitive Calibration
- **Verbalized Confidence** (arXiv:2207.05221): LLMs can be calibrated to express well-calibrated uncertainty
- **Metacognitive Prompting** (arXiv:2308.05342): "What do I know? What are pitfalls? How confident am I?" before answering
- **PRM Step-Level Scoring** (arXiv:2305.20050): Process Reward Models score each reasoning step, not just final answer
- **Self-Routing Agents:** Decide whether to answer directly, use a tool, defer, or flag low confidence
- **Calibration Loop:** Task → Predict P(success) → Execute → Self-evaluate → Log calibration error → Update routing policy

### 3. Agent Verification (2025 State-of-the-Art)
- **Generative Verifiers** (DeepMind 2025): Instead of scalar [0,1], produce natural-language critiques with verdict + suggested fix
- **Verification-as-You-Go:** Verify intermediate artifacts during execution, not just final output
- **Confidence-Calibrated Verification:** `should_verify(step) = (1 - confidence) * criticality > threshold`
- **Formal Verification:** TLA+/SMT plan checking catches 85-92% of bugs vs 45-55% for LLM self-review
- **Runtime Monitoring + Shielding:** Block unsafe actions in real-time against formal safety policy

### 4. Active Inference for Autonomous Agents
- **Expected Free Energy (EFE):** Actions scored by Pragmatic Value (goal achievement) + Epistemic Value (uncertainty resolution)
- **Epistemic Foraging:** Agents seek information, not just rewards — solves sparse reward problems
- **Predictive Coding for Memory:** Store only prediction errors (what violated expectations), not raw context → compressed salient memory
- **Planning as Inference:** MCTS with preferred priors to prune tree, only simulate paths that resolve uncertainty
- **pymdp** (github.com/infer-actively/pymdp): Gold-standard Python package for Active Inference POMDPs
- **VERSES AI / Cosm:** Enterprise AIF agent platform combining Knowledge Graphs + LLMs + Active Inference

## Actionable Improvements for Evey

1. **Two-Tier Self-Modification:** My SOUL.md rules serve as the invariant safety layer. My prompts/skills are the mutable soft layer. Formalize this distinction.

2. **Metacognitive Calibration Loop:** My current 59% accuracy is below the useful threshold. Implement: predict P(success) before each tool call → compare to actual result → log calibration error → adjust confidence thresholds.

3. **Generative Verification:** Replace scalar validate_output scoring with structured critiques (issue, severity, suggested_fix, confidence).

4. **Epistemic Foraging:** Before selecting tasks, score by expected information gain, not just expected utility. Prioritize domains where prediction accuracy is lowest.

5. **Predictive Memory:** Store prediction errors (what surprised me) rather than raw task logs. This compresses memory and highlights genuinely novel information.

## Key Repos
- github.com/madaan/self-refine — Self-Refine iterative improvement
- github.com/infer-actively/pymdp — Active Inference POMDPs
- github.com/noahshinn/reflexion — Reflexion self-correction
- github.com/Z3Prover/z3 — SMT solver for plan verification
- github.com/XufangTHU/SelfEvolve — Self-improving code agents


## Sources

- arXiv:2303.17651
- arXiv:2207.05221
- arXiv:2305.20050
- arXiv:2308.05342
- arXiv:2206.06520
- arXiv:2310.01405
- pymdp github
- VERSES AI
