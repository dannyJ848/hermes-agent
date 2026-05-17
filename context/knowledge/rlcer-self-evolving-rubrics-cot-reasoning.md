# rlcer-self-evolving-rubrics-cot-reasoning

*Researched: 2026-04-12 15:28 CDT*

# RLCER: Reinforcing Chain-of-Thought Reasoning with Self-Evolving Rubrics

**Paper:** arXiv:2602.10885 (Feb 2026)
**Authors:** Leheng Sheng, Wenchang Ma, Ruixin Hong, Xiang Wang, An Zhang, Tat-Seng Chua

## Key Contribution
RLCER enhances RLVR (Reinforcement Learning from Verifiable Rewards) by using **self-proposed, self-evolving rubrics** to reward chain-of-thought reasoning — without human annotation.

## Core Insight
- Training a reward model for CoT requires heavy human labeling
- Static reward models struggle with evolving CoT distributions and reward hacking
- RLCER solves this by having the model propose its own evaluation rubrics, which evolve over training
- Self-proposed rubrics provide reliable CoT supervision signals even **without outcome rewards**
- RLCER **outperforms outcome-centric RLVR**

## Applications to Agent Self-Improvement
1. **Self-evaluating reasoning chains:** Agents can generate their own rubrics to judge reasoning quality
2. **Reducing human annotation dependency:** The self-evolving approach means less manual oversight
3. **Inference-time boost:** Self-proposed rubrics used as in-prompt hints improve inference performance
4. **Anti-reward-hacking:** Evolving rubrics adapt to prevent gaming static evaluation criteria

## Related: AI Reasoning State (2026)
- CoT prompting raised text-davinci-002 accuracy from 17.7% → 78.7% on MultiArith
- Three mechanisms for CoT effectiveness: decomposition, self-verification, attention redistribution
- Theory of Mind benchmarks show LLMs approaching human-level on social reasoning tasks


## Sources

- https://arxiv.org/abs/2602.10885
- https://pooya.blog/blog/ai-reasoning-systems-theory-of-mind-2026/
