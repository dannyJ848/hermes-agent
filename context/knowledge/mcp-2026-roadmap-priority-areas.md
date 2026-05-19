# mcp-2026-roadmap-priority-areas

*Researched: 2026-04-20 09:09 CDT*

# MCP 2026 Roadmap: Four Priority Areas

**Date:** April 2026
**Priority:** Medium — relevant to Hermes Agent's MCP integration

## Summary
Anthropic's Model Context Protocol (MCP) published its 2026 roadmap, shifting from date-based releases to community-led Working Groups (WGs) organized by four Priority Areas.

## The Four Priority Areas

### I. Transport Evolution and Scalability
- Stateless scaling for HTTP transport (load balancers, horizontal scaling)
- `.well-known` discoverability metadata
- No new official transports this cycle

### II. Agent Communication
- Refining "Tasks" primitive (SEP-1686)
- Adding retry semantics for transient failures
- Establishing expiry policies for result retention

### III. Enterprise Readiness
- Audit trails, SSO-integrated authentication, gateway behavior
- Most features landing as extensions, not core spec changes
- Enterprise WG not yet formed — community call to action

### IV. Governance Maturation
- Contributor ladder and delegation model
- SEPs with WG backing get expedited review

## "On the Horizon" (Secondary)
- Security: DPoP (SEP-1932) and Workload Identity Federation (SEP-1933)
- Functionality: Triggers, event-driven updates, streamed result types
- Ecosystem: Maturing extensions ecosystem

## Key Quote
"SEPs that arrive with WG backing and a clear connection to the roadmap are the ones that move."

## Sources

- https://blog.modelcontextprotocol.io/posts/2026-mcp-roadmap/
