# forge-orchestrator-multi-agent-rust

*Researched: 2026-04-09 21:12 CDT*

# Forge Orchestrator — Multi-AI Task Orchestration in Rust

**Source:** github.com/nxtg-ai/forge-orchestrator (107 stars, 16 forks)

## Key Insight
A 3MB Rust binary that coordinates multiple AI coding agents via MCP. Key features: file locking, knowledge capture, and drift detection. Demonstrates that multi-agent coordination can be lightweight.

## Architecture Patterns
1. **File-based coordination** — Uses file locking to prevent agents from clobbering each other's changes. Simple but effective for coding tasks.
2. **Knowledge capture** — Agents write findings to a shared knowledge store, allowing later agents to build on earlier work.
3. **Drift detection** — Monitors when agents deviate from their assigned task, reining them back in. Critical for maintaining coherence across parallel agents.

## Relevance to Hermes
Hermes's delegate_task and squad-dev patterns could benefit from drift detection and knowledge capture between subagents. The file-locking approach is simpler than mesh_message for coordination. Worth studying the Rust source for protocol ideas.

## Sources

- https://github.com/nxtg-ai/forge-orchestrator
