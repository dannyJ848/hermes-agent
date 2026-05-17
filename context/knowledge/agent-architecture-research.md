# agent-architecture-research

*Researched: 2026-03-31 17:03 CDT*

# Agent Architecture Research: Complete Findings

## Sources Analyzed
1. Claude Code (instructkr/claw-code) - leaked source code
2. OpenHands (All-Hands-AI/OpenHands) - agent platform
3. SWE-agent (princeton-nlp/SWE-agent) - SWE-bench solver
4. Aider (paul-gauthier/aider) - pair programming AI
5. ReAct, Reflexion, LATS, Tree-of-Thought, Self-Refine, Plan-and-Solve - academic papers

## Top 20 Techniques Ranked by Impact

### Tier 1: Immediate Application
1. **Diagnose Before Pivoting** - Understand WHY something failed before trying a different approach (Claude Code)
2. **Sliding Window Compaction** - Keep last 4 messages verbatim, summarize older ones (Claude Code)
3. **Self-Refine Loop** - Generate -> Evaluate -> Refine -> Repeat up to 3 rounds (Self-Refine)
4. **Stuck Detection** - Detect 5 loop patterns: repeating actions, repeating errors, syntax loops, monologues, A-B patterns (OpenHands)
5. **Architect/Editor Split** - Plan with strong model, execute with fast model (Aider)
6. **Reflexion Pattern** - Store verbal self-reflections after failures, use in future attempts (Reflexion)

### Tier 2: High Value
7. **Structured Summary Condensation** - Use JSON schema for state summaries instead of free text (OpenHands)
8. **Repo Map with PageRank** - Rank code importance by reference graph for context selection (Aider)
9. **Composable History Processors** - Pipeline of transforms on conversation history (SWE-agent)
10. **Blast Radius Awareness** - Categorize actions by reversibility x scope (Claude Code)
11. **Post-Compaction Continuation** - "Resume directly, no recap" saves tokens (Claude Code)
12. **Auto-Verify Pipeline** - Lint + test after every code change (Aider)

### Tier 3: Situational
13. **Tree-of-Thought Branching** - Generate 3-5 approaches, evaluate, select best (ToT)
14. **Action Sampling** - AskColleagues ensemble, tournament ranking (SWE-agent)
15. **Layered System Prompt** - 11 ordered sections with caching boundary (Claude Code)
16. **Exponential Backoff** - 200ms initial, 2s max, 3 attempts (Claude Code)
17. **Cost Awareness Prompting** - "Each action is expensive, combine operations" (OpenHands)
18. **Hierarchical Instructions** - Root-to-leaf CLAUDE.md files (Claude Code)
19. **Strict Tool Schemas** - additionalProperties: false prevents hallucinated params (Claude Code)
20. **Cache Warming** - Background thread keeps prompt cache alive (Aider)

## Skills Created
- `master-agent-playbook` - Complete synthesis (meta category)
- `self-evaluation-loop` - Self-Refine + Reflexion pattern
- `delegation-mastery` - How to delegate with max success rate
- `claude-code-patterns` - Claude Code specific techniques


## Sources

- https://github.com/instructkr/claw-code
- https://github.com/All-Hands-AI/OpenHands
- https://github.com/princeton-nlp/SWE-agent
- https://github.com/paul-gauthier/aider
