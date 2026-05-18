# Dollar-Aware Token Audit for Paid Providers (Apr 15, 2026)

When using a paid per-token provider, EVERY injected token = real money.
The audit shifts from "is this noisy?" to "what does this cost per 1000 turns?"

## Full-Stack Token Cost Measurement

System prompt components (cacheable if provider supports prefix caching):

| Component | How to measure | Typical size |
|---|---|---|
| Tool schemas | Count tools x ~800 chars/schema | 80 tools = ~16K tokens |
| Agent memory file | measure chars in memory store | 5K-8K tokens depending on staleness |
| Dev docs file | measure chars in codebase documentation | ~5K tokens (often irrelevant!) |
| Available skills list | Count skills x ~80 chars | 44 skills = ~3K tokens |
| SOUL.md / identity | measure chars | ~750 tokens |
| User profile | measure chars | ~300 tokens |

Per-turn injection NOT cacheable — changes every call.
Measure each R-module's build_injection() output individually.

## Cost Calculation Template

Provider prices vary. Key formula:
- system prompt cost per turn = system_tokens x INPUT_PRICE / 1M x api_calls_per_turn
- With prefix caching: use CACHED_PRICE instead of INPUT_PRICE
- Per-turn injection cost = injection_tokens x INPUT_PRICE / 1M x api_calls_per_turn
- Per-turn injection is NEVER cacheable (it changes every call)

## Top 4 Paid-Provider Optimizations (Ranked by Dollar Impact)

1. Dev codebase docs (~5K tokens) — often irrelevant if using not developing. Gate to CWD.
2. Stale MEMORY.md events (~3.7K tokens trimmable) — past debugging notes cost forever
3. Unused tool schemas (~8K tokens trimmable) — disable 30+ irrelevant tools
4. R-module repeated phrase bloat (~116 tokens/turn) — deduplicate per-step lines

Total potential savings: ~17.5K system tokens + ~116 injection tokens/turn
At cached FriendliAI rates: ~$3.45/1K turns (48% system prompt reduction)

## MEMORY.md Staleness Audit Pattern

When on a paid provider, audit memory for one-time debugging events:
- Each historical event = ~200-500 tokens of permanent cost every turn
- Rule: If a memory entry describes a PAST EVENT (not an active rule),
  move it to searchable knowledge, not always-injected memory.
- Memory should only contain RULES and CURRENT STATE.

## R-Module build_injection() Size Guard

After building a new R-module with build_injection(), check maximum output:
- Test worst case with complex task messages
- If output > 500 chars (~125 tokens): too verbose, trim it
- Common bloat: repeated phrases on every step, verbose labels,
  task-type prefixes, listing ALL modules when only 2-3 are relevant
