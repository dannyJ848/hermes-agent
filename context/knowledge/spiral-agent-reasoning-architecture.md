# SPIRAL agent reasoning architecture

*Researched: 2026-04-13 19:29 CDT*

# SPIRAL: Symbolic LLM Planning via Grounded and Reflective Search (IBM, 2025)

## Key Innovation
Embeds 3 specialized LLM agents (Planner, Simulator, Critic) in an MCTS loop for agent planning. The Simulator grounds the search by predicting realistic outcomes before execution. The Critic provides dense reward signals through reflection, solving the sparse reward problem that kills standard MCTS.

## Results
- 83.6% accuracy on DailyLifeAPIs (+16pp over next-best search framework)
- Substantially outperforms ReAct, LATS, and other state-of-the-art agents

## Relevance to Hermes
Hermes uses linear ReAct-style loop. Key takeaway: adding a "simulate before execute" step (predict tool outcome) and a "critic" step (evaluate result quality) could significantly improve complex task success rates. The aggressive_continue + autonomous_reflect tools already provide primitive versions of this architecture.

## Also Notable
- MSEARCHER (ICLR 2026 submission): Self-reflective search agent with MCTS-based data construction for reasoning

## Sources
- https://arxiv.org/html/2512.23167
- https://openreview.net/pdf?id=vJBMYahZY5

## Sources

- https://arxiv.org/html/2512.23167
- https://openreview.net/pdf?id=vJBMYahZY5
