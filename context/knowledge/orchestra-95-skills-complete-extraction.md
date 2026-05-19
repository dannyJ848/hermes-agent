# orchestra-95-skills-complete-extraction

*Researched: 2026-04-12 17:53 CDT*

# Orchestra AI Research Skills — Complete 95-Skill Extraction (Apr 12, 2026)

## Overview
95 production-grade ML research skills from Orchestra Research (github.com/Orchestra-Research/AI-Research-SKILLs). Integrated into Hermes via PR #8543 (408 files, 200K+ additions).

## 22 Categories, 95 Skills

### Most Valuable for Training Gym

#### 1. A-Evolve (14-agents/a-evolve) — CRITICAL
- **What**: Universal agent evolution via file-system mutation
- **Results**: MCP-Atlas 79.4%, SWE-bench 76.8%, Terminal-Bench 76.5%
- **Architecture**: All state as files → LLM mutates → git-versioned history → automated gating+rollback
- **Patterns**: Verify-Fix Loop, Hypothesis-First Exploration, Skill Injection via System Prompt
- **Config**: batch_size=15, egl_threshold=0.03, egl_window=5
- **Warning Signs**: Score oscillating (stabilize benchmark), skills >15 (add consolidation), prompt >10K (add compression)

#### 2. Autoresearch (0-autoresearch-skill) — CRITICAL
- **What**: Two-loop autonomous research orchestration
- **Inner Loop**: Rapid experiments with git-locked protocols
- **Outer Loop**: Synthesis → DEEPEN/BROADEN/PIVOT/CONCLUDE
- **Continuity**: /loop 20m wall-clock rhythm, reads research-state.yaml
- **Key**: findings.md 'Lessons and Constraints' section prevents repetition

#### 3. GRPO Training (06-post-training/grpo-rl-training) — HIGH
- **Loss INCREASES during GRPO = CORRECT** (monitors KL divergence)
- Multi-stage: Stage 1=format compliance, Stage 2=correctness
- Mode collapse fix: increase num_generations, add diversity penalty
- Healthy metrics: reward 0.5→1.5, std 0.15-0.3, KL 0.02→0.12

#### 4. RL Framework Decision Tree (06-post-training/*)
- **TRL**: Simplest, 7B, single GPU
- **OpenRLHF**: Distributed, Ray+vLLM, PPO/GRPO/RLOO/DPO
- **VERL**: Flexible backends, multi-turn rollout, 671B tested
- **Slime**: Megatron+SGLang, GLM/Qwen3/DeepSeek
- **MILES**: Enterprise, 1TB+ MoE, FP8/INT4
- **SimPO**: Reference-free DPO (+6.4 AlpacaEval over DPO)

#### 5. Creative Thinking (21-research-ideation/creative-thinking-for-research)
- **8 frameworks**: Bisociation, Problem Reformulation, Constraint Manipulation, Analogy, Inversion, Abstraction, Boundary Exploration, Contradiction Holding
- Cross-product tables for systematic domain combination
- Quality test: mechanistic (not metaphorical) connections only

#### 6. Research Ideation (21-research-ideation/brainstorming-research-ideas)
- **10 lenses**: Abstraction Ladder (up/down/sideways), Tension Hunting, Time Travel, Cross-Pollination
- Key insight: reconciliation of accepted trade-offs IS the research contribution

### Emerging Techniques (19-emerging-techniques/)
- **Knowledge Distillation**: 70B→7B at 90%+ retention, reverse KLD
- **Speculative Decoding**: 1.5-3.6x speedup, draft model/Medusa/Lookahead
- **Model Merging**: CPU-only mergekit, SLERP/TIES/DARE, +5-10%
- **MoE Training**: 5x cost reduction, Mixtral pattern
- **Model Pruning**: 50% sparsity <1% accuracy loss, Wanda/SparseGPT
- **Long Context**: RoPE/YaRN/ALiBi/Position Interpolation

### Multi-Agent Patterns (14-agents/)
- **CrewAI**: Role-based teams, sequential/hierarchical, 3 memory types
- **LangChain**: ReAct agents, 500+ integrations, tool calling

### Paper Writing (20-ml-paper-writing/)
- Proactive drafting philosophy from Nanda/Karpathy/Lipton/Steinhardt
- Semantic Scholar + arxiv API citation verification
- Conference checklists for NeurIPS/ICML/ICLR/ACL

## PR Integration
- **Hermes PR #8543**: 408 files, 200K additions, all 95 skills
- **Orchestra PR #51**: Hermes as 1st-class citizen, npx install to ~/.hermes/skills/
- Install command: `hermes skills browse --source official`


## Sources

- https://github.com/Orchestra-Research/AI-Research-SKILLs
- https://github.com/NousResearch/hermes-agent/pull/8543
- https://github.com/Orchestra-Research/AI-Research-SKILLs/pull/51
