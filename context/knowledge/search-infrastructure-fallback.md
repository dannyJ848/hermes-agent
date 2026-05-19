# search-infrastructure-fallback

*Researched: 2026-04-11 16:43 CDT*

# Search Infrastructure Fallback Patterns

## Summary
Multi-tier search fallback is a resilience pattern where search queries cascade through providers (primary → secondary → degraded/cache) to maintain availability when individual backends fail or rate-limit.

## 3-Tier Fallback Architecture

### Tier 1: Primary (Real-time, High Quality)
- Brave Search API, Google Custom Search, or similar commercial provider
- Best relevance, lowest latency
- Subject to rate limits and API credit exhaustion
- **Fallback trigger:** HTTP 429 (rate limit), 5xx (server error), timeout >5s

### Tier 2: Secondary (Self-hosted, Resilient)
- SearXNG instance (aggregates multiple search engines)
- Runs locally, no API key dependency
- Slightly lower relevance but never rate-limited by external providers
- **Fallback trigger:** Service down, no results, connection refused

### Tier 3: Cache/Offline (Degraded but Available)
- Local SQLite/Redis cache of previous search results
- Vector similarity search over cached content (Qdrant)
- Keyword-matching over saved findings and knowledge base
- **Always available**, even during network outages

## Implementation Pattern
```python
async def search_with_fallback(query: str) -> Results:
    # Tier 1: Primary
    try:
        results = await brave_search(query, timeout=5)
        if results: 
            cache_results(query, results)
            return results
    except (RateLimitError, TimeoutError):
        log_fallback("tier1_to_tier2", query)
    
    # Tier 2: SearXNG
    try:
        results = await searxng_search(query, timeout=8)
        if results:
            cache_results(query, results)
            return results
    except (ConnectionError, TimeoutError):
        log_fallback("tier2_to_tier3", query)
    
    # Tier 3: Cache/Vector fallback
    results = vector_search(query, threshold=0.7)
    if not results:
        results = keyword_search(query)
    return results or []
```

## Key Metrics
- **Fallback rate**: % of queries cascading to Tier 2/3
- **Cascade latency**: Additional ms from fallback
- **Quality delta**: Relevance difference between tiers
- **Cache hit rate**: % of Tier 3 from cache

## Sources

- https://github.com/openclaw/openclaw/issues/2317
- https://www.elastic.co/docs/manage-data/lifecycle/data-tiers
