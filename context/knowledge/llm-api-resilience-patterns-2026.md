# llm-api-resilience-patterns-2026

*Researched: 2026-04-11 14:34 CDT*

# LLM API Resilience Patterns (2026)

## Key Findings

### API Reliability is Declining
- OpenAI's largest outage: June 2025, 34 hours, routing node memory limits
- Anthropic: 114 incidents in 90 days (early 2026), 30 major, median resolution 1h9m
- Claude 529 "Overloaded" rate: 3.2% → 11.7% (June→September 2025)
- Average API uptime fell from 99.66% to 99.46% (Q1 2024→Q1 2025) — 60% more downtime YoY

### Failure Taxonomy & Response Strategy

| Failure Type | Example | Strategy |
|---|---|---|
| Rate limit (429) | TPM/RPM exhausted | Retry with backoff, or reroute |
| Server error (500/503) | Provider processing failure | Fallback to secondary model |
| Overloaded (529) | Provider-wide capacity | Circuit breaker, fallback |
| Connection error | Network/DNS failure | Retry with jitter |
| Context exceeded | Token limit hit | Truncate input, switch models |
| Quality failure | Hallucinated/refused output | Validation layer, re-prompt or fallback |
| Payment required (402) | Account/quota exhausted | Model fallback chain |

### Core Patterns
1. **Retry with exponential backoff + jitter** — for transient 429/500 errors
2. **Multi-model fallback chains** — when primary provider is down
3. **Circuit breakers** — stop hitting a failing provider for a cooldown window
4. **Validation layers** — catch 200-OK-but-wrong responses (quality failures)
5. **Graceful degradation UX** — show partial results, queue for retry, don't spin forever

### Relevance to Hermes Agent
Hermes already implements some of these (model fallback in LiteLLM, retry in resilient_delegation skill). Gaps:
- No circuit breaker for repeated 402/payment-required errors
- Quality failure detection is manual (validate_output tool)
- 529 handling is implicit (rely on LiteLLM retry)


## Sources

- https://www.buildmvpfast.com/blog/building-with-unreliable-ai-error-handling-fallback-strategies-2026
