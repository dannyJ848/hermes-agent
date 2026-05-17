# hi-cot-hierarchical-chain-of-thought-reasoning

*Researched: 2026-04-20 11:01 CDT*

# Hierarchical Chain-of-Thought (Hi-CoT) Prompting

**Paper:** Huang et al., Huawei Technologies Canada, March 2026
**URL:** https://arxiv.org/html/2604.00130v1
**Code:** https://github.com/XingshuaiHuang/Hi-CoT

## Key Innovation
Hi-CoT organizes reasoning into alternating **instruction** (planning) and **execution** (doing) steps with compression bottlenecks that filter low-value content. No fine-tuning required — pure inference-time technique.

## Results
- **+6.2% average accuracy** over standard CoT (up to 61.4% relative gain)
- **-13.9% reasoning trace length** (fewer tokens, lower latency)
- Small models benefit most (reasoning scaffold effect)
- AIME24: Qwen3-14B lifted from 3.3% → 23.3%
- 100% accuracy on AMC/MATH500 when model strictly follows format

## Prompt Template
```
<|instruction|> Step 1: [Plan what to do next]
<|execution|> Step 1: [Carry out the plan]
<|instruction|> Step 2: ...
<|execution|> Step 2: ...
Answer within \boxed{}
```

## Why It Beats CoT and Plan-and-Solve
- **CoT:** No structural constraints → filler tokens, disorganized exploration, redundancy
- **Plan-and-Solve:** Single upfront plan → plan-execution drift on complex tasks
- **Hi-CoT:** Adaptive planning — each instruction is conditioned on the previous execution

## Relevance to Hermes Agent
This pattern could improve agent tool-calling chains by enforcing plan→execute alternation per step rather than dumping a full plan then executing. Could reduce no-op tool calls and improve task completion rates.

## Future Work
Authors propose SFT/RL to bake Hi-CoT structure into model weights for even stronger compliance.


## Sources

- https://arxiv.org/html/2604.00130v1
- https://github.com/XingshuaiHuang/Hi-CoT
