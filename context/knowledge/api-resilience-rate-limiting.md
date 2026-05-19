# api-resilience-rate-limiting

*Researched: 2026-04-11 17:56 CDT*

# API Resilience: Rate Limiting & 402/Payment Handling

## Key Patterns (Ines Panker, Feb 2026)

1. **Rate limits are inevitable** — any production API call will eventually get rate-limited (429). The problem is: we never test this path because manual testing averages <50 calls/hr.

2. **Two common failure modes:**
   - Option A: No error handling at all (happy path only)
   - Option B: All errors treated equally → code stops on recoverable errors

3. **Not all errors are equal** — 429 (rate limit) is recoverable; 402 (payment required) means quota exhausted; 403 is auth failure. Each needs different handling.

4. **Redis-based rate limit caching pattern:** Use a shared Redis key to communicate "wait 30s" across all workers/tasks. Key components:
   - Store the full HTTP response in Redis with TTL
   - Include tenant information in the key
   - Hash tokens for security
   - Set TTL to match the retry-after header

## Application to Agent Systems
- When delegating to external APIs, cache 429/402 responses and back off
- Distinguish quota errors (402) from rate limits (429) — 402 needs human escalation
- Build shared state so parallel tool calls don't all retry simultaneously

## Sources
- Ines Panker, "If the API Says Wait 60 Seconds, Actually Wait 60 Seconds" (Feb 2026)
- AWS Lambda error handling patterns (2026 edition)


## Sources

- https://www.ines-panker.com/2026/02/06/api-resilience-caching-429.html
- https://www.jeeviacademy.com/from-retries-to-resilience-modern-error-handling-patterns-in-aws-lambda-2026-edition/
