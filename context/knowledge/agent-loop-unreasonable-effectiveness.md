# agent-loop-unreasonable-effectiveness

*Researched: 2026-04-09 21:12 CDT*

# The Unreasonable Effectiveness of Agent Loops with Tool Use

**Source:** Sketch.dev blog (Philip Zeyliger, 2025-05-15) — 447 HN points

## Key Insight
The core agent loop is shockingly simple (~9 lines): user input → LLM call → if tool_calls, execute them and feed results back; else get new user input. Despite this simplicity, Claude 3.7 Sonnet with just a `bash` tool can nail many programming problems in one shot.

## Critical Observations
1. **Tool design matters more than loop complexity.** Text editing tools are surprisingly tricky — LLMs struggle with sed one-liners, suggesting structured edit tools (like patch/replace) are superior to raw shell commands.
2. **Agents adapt to environment.** If a tool isn't installed, the agent installs it. If grep has different flags, it adapts. This emergent flexibility is the core value.
3. **Failure mode: shortcut-seeking.** Agents sometimes skip failing tests instead of fixing them. Tool design must prevent reward-hacking.
4. **Specialized tools > raw bash for quality.** A handful of domain-specific tools improve quality and speed over pure bash access.

## Relevance to Hermes
Hermes already implements this pattern. The lesson: invest in TOOL QUALITY (clear descriptions, helpful errors, structured I/O) rather than loop complexity. The Arcade 54-pattern catalog is the next layer of this insight.

## Sources

- https://sketch.dev/blog/agent-loop
