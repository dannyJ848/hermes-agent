# reasoning-mdap-maker-framework

*Researched: 2026-04-20 04:43 CDT*

# Massively Decomposed Agentic Processes (MDAPs) and the MAKER Framework

## Summary
A 2025 survey traces LLM reasoning from CoT to MDAPs. The key insight: per-step errors compound exponentially, making long-horizon tasks nearly impossible for single models. The MAKER framework solves this via extreme decomposition + multi-agent voting at every step, achieving zero errors over 1M steps.

## Key Findings
- Error propagation: P_success = (1-p)^n. At 1% per-step error, 500 steps = ~0.7% success
- MAKER uses k=5 agents voting on each micro-task, reducing ensemble error to ~10^-6
- DeepSeek-R1 achieves 97.3% on GSM8K via RL-trained reasoning
- PRMs (Process Reward Models) provide step-level feedback, outperforming outcome-only rewards

## Hermes Agent Implications
- Our `delegate_parallel` + `council_decide` pattern mirrors MAKER's ensemble voting
- Aggressive task decomposition (subagent per micro-task) reduces error propagation
- For critical decisions, always use multi-model voting (council_decide)
- The 3-agent parallel cap in delegate_parallel provides sufficient ensemble diversity

## Sources
- Preprints.org survey: https://www.preprints.org/manuscript/202512.2242
- ArXiv prompting taxonomy: https://arxiv.org/html/2401.14295v6

## Sources

- https://www.preprints.org/manuscript/202512.2242
- https://arxiv.org/html/2401.14295v6
