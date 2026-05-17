# sota-dev-domain-improvement-2026

*Researched: 2026-04-05 18:36 CDT*

# SOTA Development Domain Improvement Techniques (2025-2026)

## Key Finding
31% code success rate indicates "write and pray" mode. Biggest gains come from closing the feedback loop.

## Technique 1: Explain-Then-Fix Self-Debug (Chen et al., ICLR 2024)
- Agent explains the bug in natural language BEFORE writing a fix
- Forces causal reasoning about WHY code failed, not just pattern-matching
- Standard self-repair (paste traceback) shows only 2-5% gains
- Explain-then-fix shows 15-25% gains
- Implementation: Loop (max 3-5 iterations): Generate → Execute → IF failure: Explain why → Fix → Retry

## Technique 2: Semantic Tool Retrieval (Two-Stage)
- Embed query, similarity search against tool descriptions, pass only top-k tools
- ToolSandbox (Meta 2024): 15-30% improvement over brute-force
- Alternative: Cross-encoder reranking for second stage

## Technique 3: Tool Call Caching
- Hash tool_name + normalized arguments → cache results
- Semantic deduplication catches equivalent calls with different formatting
- Reduces redundant API calls by 25-40%

## Technique 4: respond_directly Pseudo-Tool
- Give model an explicit "no tool needed" escape hatch
- Without it, models manufacture unnecessary tool calls
- Anthropic best practices: reduces spurious calls 25-40%

## Technique 5: Structured Tool Descriptions
- Include preconditions, postconditions, examples, and anti-patterns
- Clear "DO NOT USE for X" boundaries prevent misapplication
- Berkeley BFCL v3: structured descriptions improve accuracy 10-15%


## Sources

- Chen et al. ICLR 2024
- ToolSandbox Meta 2024
- Anthropic tool use best practices 2025
- BFCL v3 Berkeley 2025
