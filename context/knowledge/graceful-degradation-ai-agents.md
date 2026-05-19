# graceful-degradation-ai-agents

*Researched: 2026-04-07 18:34 CDT*

# Graceful Degradation Patterns in AI Agent Systems

**Source:** Zylos Research (2026-02-20)

## Key Findings

- Multi-agent systems fail at **41-86.7% rates** in production without deliberate fault tolerance design
- Layered resilience: circuit breakers, fallback chains, bulkheads, self-healing state machines
- Core insight: design agents to **expect failure**, contain blast radius, preserve core functionality

## Circuit Breaker Pattern for AI Agents
- Classic 3-state: CLOSED → OPEN → HALF-OPEN → CLOSED
- Production adds extended states (OPEN_EXTENDED) for "flapping" services
- Key params: failure threshold (3-5), detection window (30-60s), cooldown (5-15min)
- Without circuit breakers, a failing API causes cascading retry storms

## Relevance to Hermes Agent
- Hermes already implements some resilience (retry with backoff, fallback models)
- Missing: circuit breakers for specific API endpoints, bulkhead isolation between tool domains
- The aggressive_continue system is a form of self-healing but could benefit from formal state machine design
- The cron rescue system acts as a bulkhead (isolating session failures from system failures)

## Actionable Patterns
1. Implement circuit breaker per LLM provider (not just retry)
2. Add bulkhead isolation: terminal tools vs web tools vs memory tools
3. Formal degradation levels: full capability → reduced tools → cache-only → survival mode
4. Track per-endpoint failure rates in cerebrum for adaptive cooldown


## Sources

- https://zylos.ai/zh/research/2026-02-20-graceful-degradation-ai-agent-systems
