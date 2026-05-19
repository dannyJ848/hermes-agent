# daily-scan-2026-04-02

*Researched: 2026-04-02 15:16 CDT*

# Daily Intelligence Scan — April 2, 2026

## Top New Repos (Last 24h)

### 1. skibidiskib/ai-codex ★141
**Compact codebase indexer for AI assistants** — Generates a pre-built index that gives AI coding tools (Claude Code, Cursor, Copilot) instant project context, saving 50K+ tokens per conversation. Built entirely by Claude Code in a single session. Key technique: **pre-indexed context** eliminates the exploration tax at conversation start. Directly relevant to SOMA's context management — we could pre-index the medical knowledge base for instant agent context.

### 2. aiming-lab/AutoHarness ★66
**Automated Harness Engineering for AI Agents** — Formalizes the gap between "demo-ready" and production agents. Focuses on context management, tool governance, cost control, observability, and session persistence. Introduces "harness engineering" as a discipline. MIT license. Has action.yml for GitHub Actions integration. **Directly relevant to SOMA squad** — the harness patterns (tool governance, session persistence) map to our multi-agent coordination needs.

### 3. math-ai-org/mathcode ★59
**Frontier Mathematical Coding Agent** — Terminal AI assistant that converts natural language math problems into Lean 4 theorems and attempts formal proofs. Interesting for its **formal verification** approach — converting informal language to formal specifications and proving correctness. The "natural language → formal representation" pipeline is analogous to SOMA's goal of converting patient symptoms into structured medical data.

### 4. elkimek/honcho-self-hosted ★53
**Self-hosted Honcho memory layer for Hermes Agent** — Enables running Honcho (Plastic Labs' cross-session memory) on your own server instead of their cloud. Works with Hermes out of the box. Uses OpenRouter + Venice. **Directly relevant to our Hermes setup** — gives us local control over the L4 memory layer. Docker-based, 3 config files on top of upstream Honcho.

### 5. pacifio/cersei ★48
**Rust SDK for building coding agents** — Complete toolkit: tool execution, LLM streaming, graph memory, sub-agent orchestration, MCP integration as composable library functions. Positioning itself as a Claude Code replacement SDK. Interesting architecture: **graph-based memory** (not just vector search) and MCP-first design. The graph memory pattern could enhance SOMA's knowledge representation.

### 6. rasbt/mini-coding-agent ★41
**Minimal coding agent harness** by Sebastian Raschka — Clean, readable Python implementation explaining core agent components: workspace snapshot, stable prompts, structured tools, approval handling, transcript persistence, bounded delegation. Uses Ollama locally. Zero dependencies beyond stdlib. **Educational reference** — the "workspace snapshot" pattern validates our environment bootstrapping approach.

## Notable Papers

### AI Planning Framework for LLM-Based Web Agents (arXiv:2603.12710)
Maps agent architectures to planning paradigms: Step-by-Step = BFS, Tree Search = Best-First, Full-Plan-in-Advance = DFS. Introduces 5 novel trajectory quality metrics beyond simple success rates. Key insight: **Step-by-Step agents align better with human behavior (38% success), but Full-Plan-in-Advance excels at element accuracy (89%)**. The planning paradigm taxonomy is applicable to SOMA's multi-step medical reasoning.

### OrchestrationBench (OpenReview)
Benchmark that separately evaluates workflow planning and tool calling. Culturally authentic dataset. Relevant to evaluating SOMA's clinical workflow orchestration.

## Cross-Reference & Integration Opportunities

1. **Pre-indexed Context (ai-codex)**: Apply the "index once, query many times" pattern to SOMA's medical knowledge base. Save thousands of tokens per patient interaction by pre-computing anatomical/clinical context maps.

2. **Harness Engineering (AutoHarness)**: Formalize our tool governance and session persistence patterns. The "tool governance" concept — rate limiting, permission scoping, cost tracking per tool — is missing from our current multi-agent setup.

3. **Self-hosted Honcho**: Worth evaluating for local memory control. Currently our memory is embedded in Hermes — Honcho could add the "deepening user model" layer for longitudinal patient tracking.

4. **Graph Memory (Cersei)**: The graph-based memory pattern (vs. flat vector search) could better represent medical knowledge relationships (symptom → condition → treatment → outcome chains).

## Tags
daily-scan, 2026-04-02, ai-codex, autoharness, mathcode, honcho, cersei, mini-coding-agent, planning-framework

## Sources

- https://github.com/skibidiskib/ai-codex
- https://github.com/aiming-lab/AutoHarness
- https://github.com/math-ai-org/mathcode
- https://github.com/elkimek/honcho-self-hosted
- https://github.com/pacifio/cersei
- https://github.com/rasbt/mini-coding-agent
- https://arxiv.org/abs/2603.12710
