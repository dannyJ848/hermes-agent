# http-402-payment-required-resilience

*Researched: 2026-04-11 15:13 CDT*

# HTTP 402 Payment Required — Resilience Patterns

## Summary
HTTP 402 is a long-dormant status code now being actively used by API providers (OpenAI, Anthropic, etc.) for billing/quota exhaustion. It's critical for autonomous agents to handle gracefully.

## Key Patterns
1. **Retry with backoff**: 402 from quota limits is often transient (usage resets). Exponential backoff with 30-120s delays.
2. **Fallback routing**: When primary provider returns 402, route to alternative provider or local model. This is exactly the pattern Hermes uses with LiteLLM routing.
3. **Informative payloads**: Modern APIs return structured error bodies with `retry_after`, `quota_remaining`, `upgrade_url`.
4. **Pre-emptive budget checks**: Call billing/balance endpoints BEFORE hitting rate limits. Hermes's `cost_check` tool implements this.
5. **Crypto-based 402 protocols**: Emerging standard where clients pay micro-fees via wallet on 402, then retry. Not yet mainstream.

## Agent-Specific Implications
- Autonomous agents must distinguish 402 (payment) from 429 (rate limit) — different recovery strategies
- 402 should trigger provider rotation, not simple retry
- Budget monitoring tools (cost_check, cost_analytics) serve as pre-emptive 402 avoidance
- Session checkpoints before 402 encounters prevent work loss

## Sources
- MDN: 402 is "reserved for future use" but widely adopted
- APIPark: Consistent 402 error handling with informative payloads
- CTSE: Crypto-based 402 protocols emerging (2025-2026)


## Sources

- https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/402
- https://apipark.com/techblog/en/how-to-fix-error-402-payment-required-solutions-3/
- https://ctse.aei.org/402-payment-required-the-http-code-that-waited-30-years-and-why-it-matters-today/
