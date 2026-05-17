# google-a2ui-agent-driven-interfaces

*Researched: 2026-04-16 09:05 CDT*

# Google A2UI: Open Project for Agent-Driven Interfaces

**Date:** December 15, 2025 | **Repo:** github.com/google/A2UI | **License:** Apache 2 | **Format Version:** v0.8

## What It Is
A2UI is an open-source format and renderer set for **agent-generated UIs**. Agents (LLMs, orchestrators, remote A2A subagents) generate rich interfaces as **declarative data messages** — not executable code — for native rendering by client apps.

## Key Design Principles
- **Security first:** Declarative data format, not executable code. Client maintains catalog of trusted, pre-approved components. Agent can only request components from that catalog.
- **LLM-friendly:** UI represented as flat list of components with ID references — easy for LLMs to generate incrementally.
- **Framework-agnostic:** Separates UI structure from implementation. Same A2UI JSON renders on Web Components, Angular, Flutter, etc.

## Ecosystem Integration
- **A2UI + AG UI:** AG UI provides scaffolding; A2UI is the data format for rendering responses from host and remote agents
- **A2UI + A2A:** Send directly to client front end
- **vs MCP Apps:** A2UI is "native-first" — agent sends blueprint of native components, not opaque sandboxed HTML iframes

## Transport
A2A, AG UI (REST and others feasible but not yet available)

## Partners
- CopilotKit/AG UI (day-zero compatibility)
- Google Opal (AI Mini-Apps)

## Why It Matters
This is Google's play to standardize how agents communicate UI across trust boundaries in multi-agent meshes. Could become the standard for agent→human UI rendering, comparable to what MCP is becoming for agent→tool communication.

## Sources

- https://developers.googleblog.com/introducing-a2ui-an-open-project-for-agent-driven-interfaces/
