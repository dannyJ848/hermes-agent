# daily-scan-2026-04-10

*Researched: 2026-04-10 07:03 CDT*

# Daily Intelligence Scan — April 10, 2026

## GitHub Trending (New Repos)

### 1. sk-wang/mvm — Minimum Viable Memory ⭐ HIGHLY RELEVANT
- **5-layer agent memory architecture**: Event Log → Structured Memory → Tiered Summary → Retrieval (ChromaDB) → Governance (TTL/decay)
- Companion paper: "Memory as Infrastructure: First-Principles Analysis of AI Agent Knowledge Systems" (Wang & Feng, 2026)
- Key insight: Namespaced memory (profile/project/session/policy/kb) with tiered summarization (L0 ~50 tok, L1 ~500 tok, L2 full)
- **Relevance to Hermes**: Our Cerebrum memory uses similar patterns. Their governance layer (TTL, confidence, correction, decay) directly maps to our memory_decay/memory_score tools. Worth studying for integration ideas.

### 2. isteamhq/mcp-servers — Open MCP Servers for Social Platforms
- MCP servers for Twitter, Bluesky, LinkedIn, Google Ads, Hacker News
- Lets AI agents interact with real-world platforms
- **Relevance**: Could integrate with Hermes MCP client for social media monitoring

### 3. gsd-build/agent-inbox — MCP Disposable Email for Agents
- Give any AI agent a disposable email inbox in one tool call
- MCP server for email verification, auth flows, and testing
- **Relevance**: Useful for autonomous agent workflows that need email verification

### 4. mireq/AI-agent-micro-VM — Micro VM Isolation
- Micro VM implementation for running AI agents in separate virtual machines
- **Relevance**: Security/isolation pattern for multi-agent Hermes deployments

### 5. anandkrshnn/local-agent — Cryptographic Permission System
- Security-first local AI agent with cryptographic permission system
- **Relevance**: Permission model ideas for Hermes tool approval

## ArXiv Papers

### 1. "The Evolution of Tool Use in LLM Agents" (2603.22862) ⭐ KEY PAPER
- Comprehensive review of multi-tool orchestration in LLM agents
- **Six core dimensions**: inference-time planning, training/trajectory construction, safety/control, efficiency, capability completeness, benchmark design
- Shifts from single-tool call → multi-tool orchestration over long trajectories
- Applications: software engineering, enterprise workflows, GUIs, mobile systems
- **Key insight for Hermes**: Their framework for evaluating multi-tool orchestration directly applicable to improving Hermes tool dispatch

### 2. VMAO: Verified Multi-Agent Orchestration (2603.11445)
- Plan-Execute-Verify framework for coordinating specialized LLM agents
- **Relevance**: Pattern applicable to Hermes squad-dev and multi-agent workflows

### 3. Agent Psychometrics: Task-level Performance Prediction (2604.00594)
- Predicting which tasks an agent will succeed/fail on before execution
- **Relevance**: Could improve Hermes task routing and model selection

### 4. Anticipatory Planning for Multimodal AI Agents (2603.16777)
- Anticipatory trajectory reasoning as key principle for multimodal agents
- **Relevance**: Planning patterns for complex multi-step tool sequences

## Cross-References & Integration Opportunities

1. **MVM → Hermes Memory**: The 5-layer stack (especially governance with TTL/decay) closely mirrors our memory_decay + memory_score tools. Their tiered summarization approach could enhance our context_compressor.

2. **Tool Use Survey → Hermes Tool Dispatch**: The 6-dimension framework from arxiv:2603.22862 provides a structured way to evaluate and improve Hermes tool orchestration — especially inference-time planning and efficiency under constraints.

3. **Agent Psychometrics → Model Routing**: Task-level performance prediction could improve Hermes model selection (which model for which task type).


## Sources

- https://github.com/sk-wang/mvm
- https://arxiv.org/abs/2603.22862
- https://github.com/isteamhq/mcp-servers
- https://github.com/gsd-build/agent-inbox
- https://arxiv.org/abs/2603.11445
- https://arxiv.org/abs/2604.00594
