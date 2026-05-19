# self-improving-agents-ERL-HyperAgents-2026

*Researched: 2026-04-12 18:53 CDT*

# Self-Improving AI Agents: ERL and HyperAgents (March 2026)

## Experiential Reflective Learning (ERL) - ICLR 2026 MemAgents Workshop
**Paper:** arXiv:2603.24639 (Allard, Teinturier, Xing, Viaud)

Framework that reflects on task trajectories and outcomes to generate **transferable heuristics**:
- Heuristics are abstracted lessons from single-attempt experiences
- At test time, relevant heuristics are retrieved and injected into agent context
- **+7.8% success rate** over ReAct baseline on Gaia2 benchmark
- Key finding: selective retrieval is essential; heuristics > few-shot trajectory prompting
- Large gains in task completion reliability

### Relevance to Hermes/Cerebrum
ERL's heuristic extraction mirrors Hermes's distillation pipeline (distilled_tips). The key insight is that **selective retrieval** (not dumping all tips) is critical. This validates our confidence threshold of 0.6 in distilled_tips.

## HyperAgents (Meta/UBC/Oxford/NYU, March 19 2026)
- Transferred self-improvement strategies learned in one domain to completely novel domains
- Scored imp@50 = 0.630 on Olympiad math grading vs human-designed systems scoring 0.0
- **Metacognitive self-improvement**: agents that modify their own modification process
- METR benchmark: AI task-completion horizon doubling every 4 months (accelerated from 7)
- Current frontier: 50% reliability at ~50 minute tasks (was 15 min a year ago)

## Self-Improvement Landscape 2026
- **Evolutionary:** AlphaEvolve, ShinkaEvolve
- **RL methods:** SWE-RL, SAGE
- **Memory systems:** Mem0, MemOS, SimpleMem
- **Production:** Meta REA, Cognition/Devin, Karpathy's autoresearch loop


## Sources

- https://arxiv.org/abs/2603.24639
- https://o-mega.ai/articles/self-improving-ai-agents-the-2026-guide
