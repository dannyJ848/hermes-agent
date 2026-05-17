# agentic-dev-sota-2026

*Researched: 2026-04-05 23:58 CDT*

# Agentic Code Generation & Self-Improving Development: SOTA 2025-2026

## Darwin Gödel Machine (DGM) — arXiv:2505.02898
- Agent rewrites its own source code iteratively
- Maintains archive of all explored agents (evolutionary tree)
- Multi-explore: branch from historical high-performers
- Self-improved from 20% to 50% on SWE-bench WITHOUT human intervention
- Key: LLM proposes diff patches to its own codebase, evaluates on benchmarks, keeps if improved

## Test-Driven Agent Loop (DePro Pattern)
```
ANALYZE → GENERATE → TEST → DEBUG (if fail) → SUBMIT (if pass)
Key insight: TEST step is ground truth reward signal — execution doesn't lie
```
- **Progressive testing**: syntax → import → unit → module → integration → full
- **Error-guided repair**: parse test output → search related code → retrieve similar fixes → minimal patch

## SWE-agent v2 ACI Design Principles
1. Constrained action space (not raw bash)
2. Contextual edit commands with surrounding context
3. Search-then-navigate always
4. Observation truncation to prevent context overflow
5. History compression into key facts

## OpenHands (formerly OpenDevin)
- Multi-agent: Planner + Coder + Reviewer
- Sandbox execution environment
- Event stream architecture for inter-agent communication

## Reward Models for Code
- **PRM (Process Reward Model)** — per-step scoring
- **ORM (Outcome Reward Model)** — final result scoring
- **AgentQ** — MCTS + DPO for browsing trajectories

## Actionable for Evey
1. Build DGM-style self-modification loop: read own plugin code → propose patches → test → commit/revert
2. Progressive testing before every code submission
3. Error-pattern retrieval from iteration engine for faster fixes
4. PRM-style step scoring in step_reward.py (already built!)


## Sources

- arXiv:2505.02898
- princeton-nlp/SWE-agent
- OpenDevin
