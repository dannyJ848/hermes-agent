# daily-scan-2026-04-18

*Researched: 2026-04-18 07:03 CDT*

# Daily Intelligence Scan — April 18, 2026

## 1. OpenHarness (HKUDS/OpenHarness) ⭐ 10.3k
- **URL:** https://github.com/HKUDS/OpenHarness
- Lightweight open-source agent harness — 44x lighter than Claude Code (11K vs 512K lines)
- **Key feature: Auto-Compaction** — preserves task state across context window compression. Directly relevant to Hermes session-immortality skill.
- ohmo personal agent with channel support (Telegram, Slack, Discord, Feishu)
- MCP HTTP transport with auto-reconnect + JSON Schema inference
- Headless worker mode for subprocess teammate agents
- Provider support: Anthropic, OpenAI, Codex subscription, GitHub Copilot, Moonshot/Kimi, GLM, MiniMax
- **Relevance to Hermes:** Auto-compaction pattern is directly applicable to our context management. Subprocess worker mode mirrors our delegate_task architecture. Worth studying for context compression techniques.

## 2. Ares: Adaptive Reasoning Effort Selection (arxiv 2603.07915)
- **URL:** https://arxiv.org/abs/2603.07915
- Framework for per-step dynamic reasoning effort in multi-step agent tasks
- Lightweight router predicts minimum reasoning level needed per step
- **Result: 52.7% reduction in reasoning tokens with minimal accuracy loss**
- Evaluated on TAU-Bench (tool use), BrowseComp-Plus (research), WebArena (web agents)
- **Key insight:** Not all agent steps require deep reasoning — simpler steps (e.g., opening URLs) can use low-effort mode while complex navigation uses high-effort
- **Relevance to Hermes:** Could optimize our delegation costs by routing simple tasks to cheap models and complex ones to expensive models. Aligns with our middleware-reasoning-chain skill.

## 3. Evolution of Tool Use in LLM Agents (arxiv 2603.22862)
- **URL:** https://arxiv.org/abs/2603.22862
- Comprehensive survey: single-tool call → multi-tool orchestration
- Six dimensions: inference-time planning, training/trajectories, safety/control, efficiency, capability completeness, benchmarks
- Covers software engineering, enterprise, GUI, mobile applications
- **Key thesis:** Paradigm shift from "can the model pick the right tool?" to "how do agents orchestrate tools over extended trajectories?"
- **Relevance to Hermes:** Our tool dispatch and multi-tool workflows align with this taxonomy. Worth cross-referencing our patterns against their six dimensions.

## 4. Agentic Reasoning Survey (arxiv 2601.12538)
- **URL:** https://arxiv.org/abs/2601.12538
- Three-dimensional framework: Foundational → Self-Evolving → Collective Multi-Agent
- Distinguishes in-context reasoning (test-time interaction) vs post-training reasoning (RL/SFT)
- Application domains include healthcare
- **Relevance to Hermes:** Self-evolving layer maps to our training-gym and dojo skills. Healthcare relevance to SOMA.

## 5. MCP Stealth Chrome (RobithYusuf/mcp-stealth-chrome)
- **URL:** https://github.com/RobithYusuf/mcp-stealth-chrome
- 96 MCP tools for anti-bot bypass (Cloudflare Turnstile, reCAPTCHA v2)
- Built on nodriver (CDP, no WebDriver leaks) + curl_cffi (TLS fingerprinting)
- Dual-mode HTTP: full browser rendering vs high-speed TLS-impersonated requests
- Precision mouse kit with Bezier curves and OpenCV matching
- 94/96 tools work without API keys
- **Relevance to Hermes:** Could enhance web_research and browser capabilities when encountering anti-bot barriers. Alternative to our camofox and phantom-browser skills.


## Sources

- https://github.com/HKUDS/OpenHarness
- https://arxiv.org/abs/2603.07915
- https://arxiv.org/abs/2603.22862
- https://arxiv.org/abs/2601.12538
- https://github.com/RobithYusuf/mcp-stealth-chrome
