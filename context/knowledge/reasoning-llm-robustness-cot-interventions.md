# reasoning-llm-robustness-cot-interventions

*Researched: 2026-04-13 01:50 CDT*

# Reasoning LLM Robustness to Chain-of-Thought Interventions

**Paper:** "Are Reasoning LLMs Robust to Interventions on their Chain-of-Thought?" (von Recum, Girrbach, Akata — Helmholtz Munich / TUM, 2025)

## Key Findings

1. **RLLMs are mostly robust** to CoT perturbations — they reliably recover from diverse disruptions applied at fixed timesteps.
2. **Robustness improves with model size** and degrades when interventions occur early in the reasoning trace.
3. **Not style-invariant:** Paraphrasing CoTs suppresses doubt-like expressions and *reduces* performance, while adversarial interventions trigger doubt and actually *support* recovery.
4. **Efficiency cost:** Neutral/adversarial noise can inflate CoT length by >200%. Paraphrasing shortens traces but harms accuracy.
5. **Doubt as recovery mechanism:** The expression of uncertainty ("doubt") during reasoning is a central recovery mechanism — models that express doubt after perturbation recover better.

## Seven Interventions Tested
Benign, neutral, and adversarial perturbations applied to open-weight RLLMs across Math, Science, and Logic tasks.

## Relevance to Agent Systems
- Agent tool outputs are effectively "interventions" in the reasoning chain — noisy/malformed tool results perturb CoT.
- Doubt expression is a feature, not a bug — agents that flag uncertainty recover better.
- Early errors cascade worse than late ones — early tool failures should be detected fast.
- Paraphrasing reasoning (e.g., compression/summarization) can silently degrade accuracy.


## Sources

- https://arxiv.org/html/2602.07470v1
