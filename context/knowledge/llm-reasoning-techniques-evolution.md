# llm-reasoning-techniques-evolution

*Researched: 2026-04-20 01:21 CDT*

# LLM Reasoning Techniques: Evolution & Taxonomy (2024-2026)

## Three Paradigms

### 1. Prompting-Based (No Training)
- **Chain-of-Thought (CoT):** "Let's think step by step" → 30-40% math benchmark improvement
- **Self-Consistency:** Multiple reasoning paths + majority vote. GSM8K: 56.5% → 74.5%
- **Tree-of-Thoughts (ToT):** Branching with backtracking. Game of 24: CoT 4% → ToT 74%
- **Graph of Thoughts (GoT):** Non-linear connections. Sorting: CoT 62% → GoT 95%
- **ReAct:** Thought→Action→Observation cycle for tool use
- **Least-to-Most:** Decompose complex→simple subproblems
- **Program of Thoughts (PoT):** Generate executable code instead of text

### 2. Training-Based (Parameter Modification)
- **RLHF:** InstructGPT 1.3B outperformed GPT-3 175B — alignment beats scale
- **Process Reward Models (PRMs):** Step-level rewards. MATH: 72.4% → 78.2%
- **STaR:** Self-bootstrapping — generate reasoning, filter correct, fine-tune
- **Specialized Models:** o1 (AIME: GPT-4 12% → o1 74%), DeepSeek-R1

### 3. Multi-Agent Systems
- **AutoGen:** Flexible multi-turn, human-in-the-loop
- **MetaGPT:** Mimics software teams, 100% task completion in specific tests
- **Multi-Agent Debate:** Argue positions to expose logical flaws
- **MAKER Framework:** 1M+ reasoning steps with zero errors

### Key Insight
Google DeepMind 2024: Increasing test-time compute lets 14x smaller models outperform larger ones.

### Production Best Practices
- Match technique to task complexity
- Self-Consistency: 5-10x cost for significantly higher accuracy
- ToT/GoT: Very high latency, use only for high-stakes tasks
- ReAct: Best for tool use and external information
- DSPy for automatic prompt optimization

## Implications for Agent Systems
- Hybrid architectures (trained models + multi-agent + prompting) are the future
- Process reward models > outcome reward models for step-by-step reasoning
- Test-time compute scaling is a viable alternative to model scaling


## Sources

- https://pr-peri.github.io/blogpost/2026/03/21/blogpost-adv-prompt-engineering.html
- https://medium.com/@joszhang16/reasoning-in-llms-evolution-from-chain-of-thought-to-multi-agent-systems-part-2-taxonomy-of-5a7a3cdc01ed
