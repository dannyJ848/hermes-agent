# r1-self-evolving-agents-research

*Researched: 2026-04-14 15:41 CDT*

# R1 Research: Self-Evolving Agents, Metacognition, Tool Learning

## Papers Reviewed (via 3-way parallel delegation)

### Self-Evolving Agents
1. **ADAS** (2408.08435) — Meta-agent discovers novel agent architectures by writing Python code. Outperforms human-designed agents (ReAct, Reflexion).
2. **SelfDiscover** (2402.03620) — Agents self-compose reasoning modules into custom reasoning prompts. Smaller models match GPT-4 on complex tasks.

### Metacognition & Self-Reflection
3. **Self-RAG** (Asai et al., 2024) — Reflection tokens ([Retrieve], [IsRel], [IsSup], [IsUse]) create self-correcting loops. Inference-time beam search over self-evaluated paths.
4. **Reflexion** (Shinn et al., 2024) — Verbal reflections stored in episodic memory outperform simple retry. "I failed because X, next time I should Y" pattern.
5. **LATS** (Zhou et al., 2024) — Unifies MCTS + ReAct + ToT. Self-value estimation at each step, backpropagation of terminal rewards.

### Tool Learning
6. **ToolRL** (2024) — Multi-factor reward shaping for tool use: syntax + execution + relevance + efficiency. Outperforms binary rewards.
7. **CREATOR** (2024) — Agents create tools before reasoning. Abstract-Create-Execute pipeline.
8. **TroVE** (2024) — Evolutionary tool verification — keep tools that work, discard failures over episodes.

## What Was Built
**R168: Self-Critic Reflection Module** (~500 lines, ~/subconscious/self_critic.py)
- 4-axis self-critique: IsRel, IsSup, IsUse, IsEff
- Silent failure detection (pattern matching on result text)
- Per-tool success rate tracking with health warnings
- Death spiral detection (3+ consecutive failures → force strategy change)
- Verbal lesson generation + task-relevant retrieval
- Wired into distillation plugin: post_tool_call (recording) + pre_llm_call (injection)


## Sources

- arxiv:2408.08435
- arxiv:2402.03620
- Self-RAG: Asai et al. 2024
- Reflexion: Shinn et al. 2024
- LATS: Zhou et al. 2024
- ToolRL: 2024
