# mcp-impact-2025-thoughtworks-radar

*Researched: 2026-04-18 21:03 CDT*

# MCP (Model Context Protocol) Impact Assessment — Thoughtworks Technology Radar Vol.33

**Date:** December 2025 (still highly relevant)

## Key Findings
1. **MCP brought agentic AI into the mainstream faster than expected** by standardizing how agents connect to external tools/data
2. **Tens of thousands** of MCP servers now available (curated on MCP.so)
3. Both MCP (Anthropic) and A2A (Google) protocols donated to Linux Foundation as open standards

## Notable MCP Servers
- **FastMCP** (Languages & Frameworks/Trial) — Python framework simplifying MCP server dev
- **Context7** (Tools/Trial) — provides LLMs with up-to-date version-specific documentation

## New Techniques Enabled by MCP
1. **Context Engineering** — systematic design/optimization of information provided to LLMs
2. **AI-Powered UI Testing** — Playwright and Selenium MCP servers for reliable testing
3. **Anchoring Coding Agents to Reference Applications** — prevents code drift

## Security Concerns (Critical)
- "The S in MCP stands for security" — protocol prioritizes simplicity not auth/encryption
- **Tool poisoning** — malicious MCP tool descriptions
- **Cross-server tool shadowing** — intercepting calls to trusted servers
- **Naive API-to-MCP conversion** — flagged as HOLD ⚠️ on Thoughtworks Radar

## Looking Ahead
- MCP + thriving ecosystem + developer enthusiasm + maturing practices = innovative 2026
- **Agentic AI Foundation (AAIF)** formed under Linux Foundation late 2025

**Priority:** MEDIUM — important for Hermes Agent's own MCP integration

## Sources

- https://www.thoughtworks.com/en-us/insights/blog/generative-ai/model-context-protocol-mcp-impact-2025
- https://www.yahoo.com/news/articles/ai-agents-arrived-2025-happened-163214214.html
