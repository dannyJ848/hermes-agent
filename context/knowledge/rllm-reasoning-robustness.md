# rllm-reasoning-robustness

*Researched: 2026-04-13 17:31 CDT*

# RLLM CoT Robustness Research Finding

Reasoning LLMs (RLLMs) are generally robust to mid-chain perturbations, with recovery improving with model size and degrading with early interventions. Key insight for agent systems: "doubt" expressions in reasoning traces are a central recovery mechanism — suppressing them (via paraphrasing) hurts accuracy even though it shortens traces. Adversarial noise inflates CoT length by >200%.

**Agent implication:** Aggressive_continue injections may be inflating reasoning cost by triggering recovery behavior. Early-context interventions have more impact than late ones. Test-time compute efficiency matters — longer traces aren't always better.

## Sources

- https://arxiv.org/html/2602.07470v1
