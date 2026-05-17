# agent-reliability-harness-engineering-2026

*Researched: 2026-04-07 01:59 CDT*

# Agent Reliability: Harness Engineering (2026)

## Key Insight
**The harness — not the model — is the product.** Agents fail because of missing execution infrastructure, not weak models.

## The Compound Reliability Problem
- 85% accuracy per step × 10 steps = **20% end-to-end success**
- 95% accuracy per step × 20 steps = **36% end-to-end success**
- Need 99%+ per-step accuracy for 80%+ end-to-end on 20-step tasks

## Three Eras of Agent Engineering
1. **Prompt Engineering (2022)**: Focus on model instructions
2. **Context Engineering (2025)**: Managing what the model sees
3. **Harness Engineering (2026)**: State persistence, error recovery, context management, independent evaluation

## Nine Failure Modes in Long Sessions
From Anthropic's blueprint (6 publications, late 2024 - March 2026):
- Missing state persistence
- No error recovery
- Context window exhaustion
- Self-evaluation bias
- Tool dispatch failures
- Missing verification loops
- No independent evaluation

## Planner-Generator-Evaluator Architecture
- Separate generator from evaluator to eliminate self-evaluation bias
- Independent evaluation produces concrete cost improvements
- The harness is a durable architectural investment, NOT scaffolding to remove

## Relevance to Hermes Agent
- Our aggressive_continue + cron rescue + checkpoint chain IS harness engineering
- The 3-layer anti-stop architecture maps directly to this pattern
- Next: formalize error recovery patterns into skill documents

## Source
- Article: "How to Build AI Agents That Don't Break After 30 Minutes?" by Jarosław Wasowski (Apr 2026)
- Based on Anthropic's 6 engineering publications (2024-2026)


## Sources

- https://medium.com/@wasowski.jarek/how-to-build-ai-agents-that-dont-break-after-30-minutes-476cb42d133b
