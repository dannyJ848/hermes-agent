# agent-landscape-march-2026

*Researched: 2026-03-31 19:17 CDT*

# AI Agent Landscape - March 2026

## Key Repos to Study

### Tier 1: Must-Read Architecture
- **DeerFlow 2.0** (bytedance/deer-flow, 55.2k stars) - SuperAgent harness for long-horizon tasks. Orchestrates sub-agents, memory, sandboxes, extensible skills. Integrates Claude Code/Codex/Cursor.
- **Deep Agents** (langchain-ai/deepagents, 18.4k stars) - "Batteries-included" agent harness on LangGraph. Planning (write_todos), filesystem tools, shell, sub-agent spawning, auto-summarization. MIT license.
- **mini-SWE-agent** (SWE-agent/mini-swe-agent, 3.6k stars) - ~100 lines of Python, bash-only, >74% SWE-bench verified. Key insight: simpler is better as LMs improve.

### Tier 2: Production Agent Platforms
- **Gemini CLI** (google-gemini/gemini-cli, 99.7k) - Free terminal AI agent, 1M context, MCP support built-in
- **Claude Code** (anthropics/claude-code, 90.7k) - Plugin system with custom commands/agents
- **Codex CLI** (openai/codex, 69.9k) - Rust-based (codex-rs), SDK and skills system
- **OpenHands v1.6** (OpenHands/OpenHands, 70.3k) - SDK, CLI, GUI, Cloud, Enterprise tiers

### Tier 3: MCP Ecosystem Leaders
- **Context7** (upstash/context7, 51.2k) - Up-to-date library docs injected into LLM context
- **Playwright MCP** (microsoft/playwright-mcp, 30.1k) - Browser automation via accessibility tree
- **GitHub MCP** (github/github-mcp-server, 28.4k) - Official GitHub integration
- **Serena** (oraios/serena, 22.3k) - Semantic code retrieval/editing as MCP server

## Key Trends
1. **Simplification over complexity** - mini-SWE-agent proves ~100 lines of bash-only can match complex scaffolds
2. **Terminal agents are dominant paradigm** - Claude Code, Codex, Gemini CLI, Aider all terminal-first
3. **MCP is the universal connector** - 11,000+ MCP server repos on GitHub
4. **Multi-agent orchestration matures** - CrewAI "Crews" vs LangGraph "Graphs" are two dominant paradigms
5. **Phone/GUI agents emerge** - Open-AutoGLM (phone), UI-TARS (desktop GUI)

## Notable arxiv Papers (March 2026)
- "Meta-Harness: End-to-End Optimization of Model Harnesses" (Chelsea Finn's group)
- "Dynamic Dual-Granularity Skill Bank for Agentic RL"
- "CoE: Collaborative Entropy for Uncertainty Quantification in Agentic Multi-LLM Systems"
- "Reasoning as Energy Minimization over Structured Latent Trajectories"


## Sources

- https://github.com/SWE-agent/mini-swe-agent
- https://github.com/bytedance/deer-flow
- https://github.com/langchain-ai/deepagents
- https://github.com/google-gemini/gemini-cli
- https://github.com/openai/codex
