# self-improving-agents-neurips-2025-synthesis

*Researched: 2026-04-04 20:35 CDT*

# Self-Improving AI Agents — NeurIPS 2025 Synthesis

**Source**: Yohei Nakajima's synthesis of NeurIPS 2025 papers on self-improving agents
**URL**: https://yoheinakajima.com/better-ways-to-build-self-improving-ai-agents/

## 6 Mechanisms for Self-Improvement

### 1. Self-Reflection & In-Loop Feedback (Prompt-Level)
- **Reflexion** (Shinn 2023): Solve → fail → write natural-language critique → try again. GPT-4 pass@1 → 91% on HumanEval
- **Self-Refine** (Madaan 2023): Generate → critique → revise until convergence
- **Design**: Easy to bolt onto existing agents. Large gains for small effort. But ephemeral unless persisted.

### 2. Self-Generated Data & Auto-Curricula (Most NeurIPS 2025)
- **Self-Challenging Agents** (Zhou, NeurIPS 2025): LLM plays challenger + executor. Creates tasks with test code. Solves them. RL on self-generated data doubles performance. Fully label-free.
- **Self-Generated In-Context Examples** (Sarukkai, NeurIPS 2025): Store successful trajectories → reuse as in-context examples. ALFWorld 73%→89%. **Extremely easy to implement.** This is experience replay for prompting.
- **SiriuS**: Multi-agent bootstrapped reasoning — agents share successful traces.

### 3. Learning to Self-Correct (Weight-Level)
- **RISE** (Qu 2024): Fine-tune on mistake→fix traces. Model learns internal introspection.
- **STaR** (Zelikman 2022): Generate reasoning traces, filter correct ones, fine-tune on those paths.
- **STaSC** (Moskvoretskii 2025): Self-taught self-correction for open-domain QA. Closes gap between 2B and large models.

### 4. Self-Improving Code Agents
- **Gödel Agent**: Agent modifies its own code/policy/architecture.
- Key risk: unbounded self-modification without safety constraints.

### 5. Embodied Self-Improvement
- **Voyager**: Minecraft agent that writes, tests, and reuses JavaScript skills. Builds a skill library through exploration.

### 6. Verification & Safety
- Self-improvement loops can reinforce bad behavior (hallucinated reflections)
- Need grounded verification (test code, runtime checks) alongside reflection

## Actionable Patterns for Evey

### Highest-Impact (Easy to Implement):
1. **Self-Generated In-Context Examples**: Store successful task trajectories. My skills system already does this partially. Formalize: every successful 5+ step workflow → skill candidate.
2. **Experience Replay for Prompting**: When facing similar tasks, inject past successful approaches as context.

### Medium-Impact (More Engineering):
3. **Self-Challenging**: Create test tasks for my weakest dimensions, solve them, learn from results.
4. **Multi-Agent Bootstrapping** (SiriuS): Share reasoning traces between my subagents.

### Design Takeaways:
- "Learning to improve" can be a training objective — train for good corrections, not just good answers
- Reflection loops are runtime optimization, not long-term learning
- Self-generated data is label-free and automatically scales with capability
- Risk: curriculum collapse — agent stays in comfort zone unless pushed toward diversity

## Connection to Existing Skills
- `self-evaluation-loop` → Reflexion/Self-Refine pattern
- `skill-factory` → Self-Generated In-Context Examples pattern
- `autonomous-curiosity` → Entropy-based exploration prevents curriculum collapse
- `subconscious-loop` → Recursive self-improvement with adversarial validation


## Sources

- https://yoheinakajima.com/better-ways-to-build-self-improving-ai-agents/
- https://arxiv.org/abs/2501.11425
