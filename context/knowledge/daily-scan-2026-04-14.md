# daily-scan-2026-04-14

*Researched: 2026-04-14 07:03 CDT*

# Daily Intelligence Scan — 2026-04-14

## Key Papers

### 1. ToolTree (ICLR 2026) — MCTS-Based Tool Planning
- **URL:** https://arxiv.org/abs/2603.12740
- **Key Idea:** Uses Monte Carlo Tree Search with dual-stage LLM evaluation + bidirectional pruning for tool planning. Prunes unpromising branches BEFORE and AFTER tool execution.
- **Result:** ~10% average gain over SOTA on 4 benchmarks.
- **Relevance to Hermes:** Directly applicable to Hermes' tool dispatch. Current approach is greedy — ToolTree's MCTS pattern could improve multi-step tool orchestration. The bidirectional pruning (pre+post execution) is a novel efficiency technique.

### 2. Evolution of Tool Use in LLM Agents (Survey)
- **URL:** https://arxiv.org/abs/2603.22862
- **Key Idea:** Comprehensive survey of multi-tool orchestration. Identifies 6 core dimensions: inference-time planning, training/trajectory construction, safety/control, efficiency, capability completeness, benchmark design.
- **Relevance:** Framework for evaluating Hermes' own tool orchestration. The trajectory construction dimension is especially relevant for our delegation patterns.

### 3. MagicAgent — Generalized Agent Planning via MoE + RL
- **URL:** https://arxiv.org/html/2602.19000v1
- **Key Idea:** Foundation model for generalized agent planning using Mixture-of-Experts with load-balanced training. 5 task categories: hierarchical decomposition, tool-augmented planning, multi-constraint scheduling, procedural logic orchestration, long-horizon execution. Uses both offline and online RL with entropy regularization.
- **Relevance:** The multi-task reward function and MoE load-balancing approach could inform how we structure Hermes' tool-calling training.

## Industry News

### Microsoft Agent Framework 1.0 GA
- Production-ready for .NET and Python with stable APIs and LTS.
- **URL:** https://devblogs.microsoft.com/agent-framework/microsoft-agent-framework-version-1-0/

### Google ADK (Agent Development Kit) Released April 2026
- Google's answer to OpenAI Agents SDK and Anthropic Agent SDK.
- Part of the "Big 3" agent SDK ecosystem now: OpenAI (March), Google ADK (April), Anthropic (with Claude 4.6).

### State of AI Agent Memory 2026 (Mem0)
- **URL:** https://mem0.ai/blog/state-of-ai-agent-memory-2026
- LOCOMO benchmark now standard for evaluating agent memory.
- Benchmarked 10 approaches including LangMem, RAG, MemGPT, A-Mem, OpenAI Memory, Zep, full-context.
- Key finding: multi-dimensional evaluation (BLEU, F1, LLM-score, token consumption, latency) prevents gaming one metric.

## Notable GitHub Repos (Last 24h)

| Repo | Description | Interesting For |
|------|-------------|-----------------|
| HaowenYoung/HW_MyJarvis | L1-L6 self-evolving memory + Karpathy-style LLM Wiki template | Memory tiering pattern |
| Ginny-Binny/whysh | Explains WHY your AI agent ran a command | Agent transparency/observability |
| Suffynux/ai-agent-skills | Community plug-and-play skill library | Skill standardization |

## Cross-References for Hermes

1. **ToolTree's MCTS pattern** → Could replace greedy tool dispatch in Hermes for complex multi-step tasks. Bidirectional pruning is a concrete technique we could implement in the middleware reasoning chain.

2. **whysh's transparency approach** → Hermes' reasoning traces already capture some of this, but structured "why" explanations for each tool call could improve debugging and user trust.

3. **Mem0's LOCOMO benchmark** → We should evaluate our own memory providers against LOCOMO's dimensions. Our cerebrum/episodic memory approach needs formal benchmarking.

4. **Google ADK entering the space** → MCP is now adopted by all 3 major providers (OpenAI, Google, Anthropic). This validates Hermes' MCP-native architecture.


## Sources

- https://arxiv.org/abs/2603.12740
- https://arxiv.org/abs/2603.22862
- https://arxiv.org/html/2602.19000v1
- https://mem0.ai/blog/state-of-ai-agent-memory-2026
- https://devblogs.microsoft.com/agent-framework/microsoft-agent-framework-version-1-0/
- https://github.com/HaowenYoung/HW_MyJarvis
- https://github.com/Ginny-Binny/whysh
