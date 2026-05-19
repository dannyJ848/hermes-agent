# self-evolving-agents-april-2026

*Researched: 2026-04-13 11:11 CDT*

# Self-Evolving Agent Systems - April 2026 Research Digest

## Key Papers

### 1. EvoSkills (arxiv 2604.01687) - Co-Evolutionary Skill Generation
- Skills are multi-file artifact bundles (not single tools): instructions + code + config + recovery logic + validation
- Co-evolution: Skill Generator + Surrogate Verifier improve together
- Self-evolved skills outperform human-curated due to "human-machine cognitive misalignment"
- Achieves highest pass rate on SkillsBench across Claude Code and Codex
- Key insight: verifier quality determines skill evolution ceiling

### 2. ERL - Experiential Reflective Learning (arxiv 2603.24639)
- Reflect on task outcomes → generate heuristics (actionable rules)
- Separate failure heuristics (guide search) from success heuristics (guide execution)
- Retrieval quality > quantity. Too many heuristics hurts performance
- Improved Gaia2 by 7.8% over ReAct

### 3. AgentHER (arxiv 2603.21357) - Hindsight Experience Replay for Agents
- Relabel failed trajectories by detecting what they actually achieved
- 97.7% relabeling precision with confidence gating
- Converts 85%+ wasted failures into training data
- +7.1-11.7pp improvement over success-only SFT

### 4. MT-GRPO+GTPO+IRC (arxiv 2604.02869) - Multi-turn RL for Tool-Calling
- Dense per-turn rewards DEGRADE performance by up to 14pp
- GTPO hybrid advantage fixes misalignment
- IRC: analyze rollout data empirically to design rewards
- Learning rate explains 70% of sparse reward success

### 5. Agent-as-Annotators (arxiv 2604.07776) - Distillation
- Lower reasoning budgets for teachers produce BETTER training data
- Model recency does NOT predict teaching effectiveness
- 6 training environments sufficient for generalization

### 6. Trace2Skill (arxiv 2603.25158) - Skill Evolution from Trajectories
- Parallel error analysts + success analysts propose patches
- Error analysis more reliable than success analysis
- Conflict-free merging of patches

### 7. Adaptive Parallel MCTS (arxiv 2604.00510) - Test-Time Compute
- Negative early exit: prune unproductive MCTS trajectories
- Adaptive boosting: reallocate freed compute
- Integrated into vLLM for p99 latency reduction

### 8. MemMachine (arxiv 2604.04853) - Ground-Truth-Preserving Memory
- 3-tier: short-term episodic, long-term episodic, profile/semantic
- Retrieval stage dominates accuracy over model choice
- Late binding + multi-query reranking

### 9. Synapse (arxiv 2601.02744) - Spreading Activation Memory
- Unified episodic-semantic graph with spreading activation
- Fan effect + lateral inhibition for relevant memory retrieval
- Uncertainty-aware rejection prevents false memory recall


## Sources

- https://arxiv.org/html/2604.01687v1
- https://arxiv.org/html/2603.24639v1
- https://arxiv.org/html/2603.21357v2
- https://arxiv.org/html/2604.02869v1
- https://arxiv.org/html/2604.07776v1
- https://arxiv.org/html/2603.25158v1
- https://arxiv.org/html/2604.00510v1
- https://arxiv.org/html/2604.04853v1
- https://arxiv.org/html/2601.02744v3
