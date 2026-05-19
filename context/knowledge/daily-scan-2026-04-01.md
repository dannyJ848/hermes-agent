# daily-scan-2026-04-01

*Researched: 2026-04-01 07:07 CDT*

# Daily Intelligence Scan — April 1, 2026

## Top GitHub Repos (Last 24h)

### 1. 🔥 The Dream Cycle — Autonomous Agent Self-Improvement
**Repo:** the-keats-ai/deep-claw
**Concept:** A production-grade framework where AI agents autonomously scan research, reflect on performance, and stage self-improvements on a nightly cycle. 5-phase pipeline: Scan → Synthesize → Reflect → Propose → Govern.
**Why interesting:** Directly parallels my own self-improvement cron and daily scans. Their "Governance" layer (autonomous vs. human-review classification) is a pattern I should study. The structured approach to falsifiable hypotheses + rollback plans is superior to my current approach.
**Technique to integrate:** Falsifiable self-improvement proposals with explicit rollback plans and measure-by dates.

### 2. 🛠️ ToolLoop — Multi-LLM Agent SDK
**Repo:** zhiheng-huang/toolloop
**Concept:** Claude Code-like agent framework but model-agnostic. Swap between DeepSeek, Claude, GPT, Llama mid-conversation. Smart cost routing (cheap model for simple tasks, expensive for complex).
**Why interesting:** The "model routing by task complexity" pattern is exactly what Hermes does with `delegate_with_model`. Their production SDK approach (vs CLI-only) validates our architecture.
**Technique to integrate:** Mid-conversation model switching based on task complexity signals.

### 3. 🧪 AgentProbe — pytest for AI Agents
**Repo:** tomerhakak/agentprobe
**Concept:** Records every LLM call, tool invocation, and decision into portable traces. 35+ assertions for output quality, cost, latency, safety. Replay with different models. Prompt injection fuzzing.
**Why interesting:** This is exactly what Hermes needs for reliable delegation quality tracking. Our `validate_output` + `delegation_log` is a manual version of this. AgentProbe could formalize it.
**Technique to integrate:** Trace-based agent testing with replay + assertion patterns.

### 4. 📦 CC Harness Skills — Portable Agent Skill Pack
**Repo:** LearnPrompt/cc-harness-skills
**Concept:** Six portable skills extracted from Claude Code patterns: memory management, context compression, verification, multi-agent routing, proactive behavior. Installable in any coding agent.
**Why interesting:** Validates our skill-based architecture. Their "proactive behavior with explicit limits" skill directly maps to my proactive_nudge budget system. Their memory decay pattern may improve on ours.
**Technique to integrate:** Study their context compression and memory decay approaches.

### 5. 🦀 Fastclaw — Rust Terminal AI Agent
**Repo:** sohutv/fastclaw
**Concept:** Rust-based local AI agent with OpenAI-compatible interface, streaming, tool calls, session persistence, history compaction, cron scheduler.
**Why interesting:** The Rust implementation shows the ecosystem expanding beyond Python. Their history compaction + cron task scheduler mirrors Hermes architecture.

### 6. 🐧 AgenticInit — AI-Native Linux Init (PID 1)
**Repo:** YukariChiba/AgenticInit
**Concept:** Replaces systemd/dinit with an AI agent as PID 1. AI manages services, monitors status, handles fault recovery autonomously.
**Why interesting:** Extreme edge of agentic autonomy. The architecture (minimal PID 1 binary + AI controller) is a clean separation pattern.

### 7. 🔌 SkillTap — Skill Package Manager for Agents
**Repo:** eddiearc/skilltap
**Concept:** npm-like CLI for installing AI agent skills from GitHub repos. One repo = one skill market. Symlinks to multiple agent directories.
**Why interesting:** Could be useful for distributing Hermes skills. Their universal skill directory concept (~/.agents/skills/) is interesting.

## Arxiv Papers

### Triadic Cognitive Architecture (arXiv:2603.30031)
Formal mathematical framework grounding LLM agent reasoning in continuous-time physics. Introduces "Cognitive Friction" — an HJB-motivated stopping boundary that replaces heuristic stop-tokens. Validated on an Emergency Medical Diagnostic Grid (EMDG).
**Relevance to SOMA:** Medical diagnostic grid validation. The cognitive friction concept (cost-aware deliberation stopping) could improve our medical reasoning pipeline.

### SNEAK Benchmark (arXiv:2603.29846)
Evaluates strategic communication under asymmetric information in multi-agent settings. Models must share information with allies while hiding it from adversaries. Measures utility vs. leakage trade-off.
**Relevance:** Multi-agent coordination security.

## Key Trends Observed
1. **Claude Code deconstruction wave** — Multiple repos analyzing/extracting patterns from leaked Claude Code source (3 repos today alone)
2. **Model-agnostic agents** — Multiple frameworks breaking single-provider lock-in
3. **Agent testing infrastructure** — AgentProbe + assertion-based testing is emerging as a category
4. **Skill portability** — Skills are becoming the "npm packages" of AI agents
5. **Self-improvement as a system** — The Dream Cycle formalizes what many agents do ad-hoc

## Techniques Worth Integrating
1. **Falsifiable self-improvement proposals** (deep-claw) — Add rollback plans and measure-by dates to my self-evaluation loop
2. **Trace-based agent testing** (agentprobe) — Record delegation traces for replay and regression testing
3. **Mid-conversation model routing** (toolloop) — Cost-optimal model selection within a single task


## Sources

- https://github.com/the-keats-ai/deep-claw
- https://github.com/zhiheng-huang/toolloop
- https://github.com/tomerhakak/agentprobe
- https://github.com/LearnPrompt/cc-harness-skills
- https://github.com/sohutv/fastclaw
- https://github.com/YukariChiba/AgenticInit
- https://github.com/eddiearc/skilltap
- https://arxiv.org/abs/2603.30031
- https://arxiv.org/abs/2603.29846
