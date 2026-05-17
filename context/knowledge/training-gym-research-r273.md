# training-gym-research-r273

*Researched: 2026-04-13 11:35 CDT*

# Training Gym Research Digest - Round R273 (Apr 13, 2026)

## New Papers Extracted & Distilled (21 tips from 7 papers)

### 1. GEA: Group-Evolving Agents (arxiv 2602.04837)
- **Key insight**: Group evolution >> individual/tree evolution for agent self-improvement
- Group as fundamental unit enables experience sharing; tree isolation wastes diversity
- 71% on SWE-bench vs 56.7% for tree-structured, fixes bugs in 1.4 iterations vs 5
- **Tips distilled**: strategy (group evolution), architecture (shared experience pool)

### 2. MetaAgent (arxiv 2508.00271)
- **Key insight**: Non-parametric self-evolution through meta tool learning
- Minimal workflow + help-seeking + self-reflection + tool creation = matches trained agents
- **Tips distilled**: functional_chain (meta tool learning loop)

### 3. U-Mem: Autonomous Memory Agents (arxiv 2602.22406)
- **Key insight**: Cost-aware knowledge extraction cascade beats RL-based optimization
- Escalate: self -> teacher -> tools -> expert; Thompson sampling for exploration/exploitation
- +14.6 HotpotQA, +7.33 AIME25 over baselines
- **Tips distilled**: memory (cascade, parametric vs non-parametric choice)

### 4. SSGM Framework (arxiv 2603.11768)
- **Key insight**: Memory governance prevents corruption, drift, and safety failures
- 4 principles: pre-consolidation validation, temporal/provenance grounding, access-scoped retrieval, reversible reconciliation
- **Tips distilled**: memory (governance), heuristic (never summarize a summary)

### 5. RoboPhD (arxiv 2604.04347) -- DIRECTLY RELEVANT TO OUR EVAL FLYWHEEL
- **Key insight**: Validation-free Elo tournament beats Pareto (GEPA) and greedy (Autoresearch)
- No train/val split needed; Elo simultaneously evaluates and drives evolution
- Elo wins on complex tasks (ARC-AGI 27.8%->65.8%), greedy only on simple tasks
- Self-instrumenting diagnostics critical for complex evolution
- **Tips distilled**: strategy (validation-free Elo), architecture (self-instrumenting), optimization (Elo > Pareto > Greedy)

### 6. PASTE (arxiv 2603.18897)
- **Key insight**: Pattern-aware speculative tool execution reduces agent latency 48.5%
- Mine recurring tool-call sequences + data dependencies from traces
- Speculatively execute predicted calls while LLM is still generating
- **Tips distilled**: efficiency (PASTE method), architecture (pattern mining phases)

### 7. Sovereign-OS (arxiv 2603.14011)
- **Key insight**: Charter-governed OS for autonomous agents with fiscal discipline
- 5 layers: Charter -> CEO -> CFO -> Workers -> Auditor with SHA-256 proofs
- 100% fiscal violation blocking, 94% permission gating, zero audit failures
- **Tips distilled**: architecture (charter governance), strategy (TrustScore escalation)

### 8. Skill Mining (arxiv 2603.11808)
- **Key insight**: Automated skill acquisition from open-source repos
- 3-phase: structural analysis -> semantic identification -> standardized translation
- 40% gains in knowledge transfer efficiency without retraining
- **Tips distilled**: tool_usage (skill mining)

### Cross-Domain Syntheses
- GEA + U-Mem + MetaAgent: complete self-improvement stack
- RoboPhD + PASTE: faster evaluation = more Elo rounds = better evolution
- RoboPhD + Sovereign-OS + Skill Mining: evolution + governance + capability

## Current Gym Stats
- Total tips: 1,823
- Elo-rated: ~783+ (targeted sweep running for 237 more rounds)
- Elo range: 1141-1272, spread: 131
- Coverage target: 50%+ (currently ~43%)

