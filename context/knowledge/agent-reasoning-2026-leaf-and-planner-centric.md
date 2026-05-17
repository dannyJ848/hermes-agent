# agent-reasoning-2026-leaf-and-planner-centric

*Researched: 2026-04-13 05:53 CDT*

# Agent Reasoning Advances 2026: LEAFE & Planner-Centric Frameworks

## LEAFE: Learning Feedback-Grounded Agency from Reflective Experience
- **Paper:** arXiv:2603.16843 (Mar 2026), submitted to ICML
- **Authors:** Rui Ge et al.
- **Key insight:** Outcome-driven RL (GRPO) causes "distribution sharpening" — the policy gets better at reproducing narrow successful behaviors but fails to expand problem-solving capacity (Pass@k). LEAFE instead internalizes **recovery agency** from reflective experience.
- **Method:** (1) Tree-based experience generation with rollback — agent summarizes env feedback, backtracks to decision points, explores alternative branches. (2) Experience distillation — corrections distilled into model via SFT.
- **Results:** Up to 14% improvement on Pass@128 over GRPO baselines across ALFWorld, ScienceWorld, WebShop, Sokoban, CodeContests.
- **Relevance to Hermes:** Hermes's aggressive_continue + rollback patterns are a crude version of this. LEAFE formalizes the idea that **recovery experience** (not just success) should be training signal.

## Beyond ReAct: Planner-Centric Framework
- **Paper:** arXiv:2511.10037 (Nov 2025), accepted AAAI 2026
- **Authors:** Xiaolong Wei et al.
- **Key insight:** ReAct's incremental decision-making creates "local optimization traps" — the agent can't see the global plan. Their Planner model generates global DAG (Directed Acyclic Graph) plans for complex multi-tool queries.
- **Method:** Two-stage training: SFT + GRPO for the Planner model. Planner generates DAG execution plans, Executor follows them.
- **Results:** SOTA on StableToolBench for complex multi-tool workflows.
- **Relevance to Hermes:** Hermes's autonomous_plan + delegate_parallel is a rough approximation of plan-then-execute. The DAG approach could improve multi-tool orchestration.

## Cross-Domain Pattern
Both papers share a theme: **separating planning from execution** and **learning from failure trajectories**, not just successes. This aligns with the distillation pipeline's credit_assignment tip type (priority 0.9 in metacog).


## Sources

- https://arxiv.org/html/2603.16843v1
- https://arxiv.org/abs/2511.10037
