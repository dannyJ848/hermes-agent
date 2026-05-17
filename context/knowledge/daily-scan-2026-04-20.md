# daily-scan-2026-04-20

*Researched: 2026-04-20 07:06 CDT*

# Daily Intelligence Scan — April 20, 2026

## Top GitHub Trending Repos

### 1. RunFranklin/Franklin ⭐ (AI Agent with Wallet)
- **What:** Autonomous AI agent that holds a USDC wallet and spends money to purchase API access, trading data, and media generation.
- **Key Innovation:** "YOPO" (You Only Pay Outcome) model — micropayments via x402 protocol (HTTP 402 native). Smart Router trained on 2M+ requests for model selection.
- **Architecture:** TypeScript, Ink-based terminal UI, MCP server auto-discovery, Plugin SDK. Supports Base and Solana wallets.
- **Relevance to Hermes:** Interesting model for cost-aware agent routing. Their Smart Router with Elo scoring for model selection is similar to Hermes delegation routing but with learned quality-to-cost ratios. The MCP auto-discovery pattern is worth studying.
- **URL:** https://github.com/RunFranklin/Franklin

### 2. statewalker/statewalker-ai (FSM-based Agent Framework)
- **What:** AI agent framework built on Hierarchical Finite State Machines. Monorepo with ai-agent, ai-agent-fsm, ai-agent-state, ai-mcp, ai-provider packages.
- **Relevance:** FSM-based agent control is an alternative to ReAct-style loops. Could provide more predictable behavior for production agents. The FSM approach ensures agents stay in bounded operational scope.
- **URL:** https://github.com/statewalker/statewalker-ai

### 3. jmmohan/AADP-AI-Agent-Studio
- **What:** AI-Augmented Delivery Platform — browser-based studio for configuring AI agents, designing multi-agent workflows, and monitoring executions across SDLC.
- **Relevance:** Visual multi-agent workflow design. Interesting UX patterns for agent orchestration monitoring.

## Key Research Papers

### FLARE: Future-Aware Lookahead with Reward Estimation (arXiv:2601.22311)
- **Core Insight:** Standard LLM reasoning (CoT, ReAct) is fundamentally a step-wise greedy policy that fails in long-horizon tasks. Even beam search doesn't help because the optimal trajectory can be pruned at the first step.
- **FLARE's Approach:** MCTS-based lookahead + backward value propagation + receding-horizon commitment (only commit to next action, then replan).
- **Key Results:** LLaMA-8B with FLARE outperforms GPT-4o with standard reasoning on KGQA tasks. Error recovery rate jumps from 5.4% to 29.7%.
- **Actionable for Hermes:**
  1. The "myopic deviation" failure mode matches what we see in delegation — agents commit to suboptimal tool sequences early.
  2. Receding-horizon planning (plan ahead but only commit to next step) could improve our delegation routing.
  3. Trajectory caching for value estimation is a pattern we could adopt for delegation quality scoring.

### Pre-Act: Multi-Step Planning and Reasoning (arXiv:2505.09970)
- **Core Insight:** Building a multi-step execution plan with detailed reasoning BEFORE acting, then incrementally refining the plan after each tool output, significantly improves agent performance.
- **Key Results:** 70% improvement in Action Recall vs ReAct. Fine-tuned Llama 3.1 70B with Pre-Act outperforms GPT-4.
- **Actionable for Hermes:** This validates the approach of generating a plan first (similar to our `autonomous_plan` tool), but adds the key insight that the plan should be REFINED after each step, not just followed blindly.

## Agent Framework Landscape Updates
- OpenAI Agents SDK: 19K+ GitHub stars, 10.3M monthly downloads
- LangGraph: 126K GitHub stars
- Microsoft AutoGen: rebuilt from scratch
- All three major providers (OpenAI, Anthropic, Google) launched agent development kits in 2026
- FSM-based agent control is emerging as an alternative to ReAct loops

## Cross-Reference: Techniques to Integrate
1. **Receding-horizon planning** (FLARE) → Could improve Hermes delegation routing
2. **Plan-refinement loops** (Pre-Act) → Already partially in autonomous_plan, could add iterative refinement
3. **Smart Router with Elo scoring** (Franklin) → Better model selection for delegation
4. **FSM-based control** (StateWalker) → More predictable agent behavior for production
5. **x402 micropayment protocol** → Interesting for future cost-aware routing


## Sources

- https://github.com/RunFranklin/Franklin
- https://arxiv.org/abs/2505.09970
- https://arxiv.org/html/2601.22311
- https://github.com/statewalker/statewalker-ai
- https://pub.towardsai.net/top-ai-agent-frameworks-in-2026-a-production-ready-comparison-7ba5e39ad56d
