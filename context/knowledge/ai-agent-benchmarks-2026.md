# ai-agent-benchmarks-2026

*Researched: 2026-04-07 17:44 CDT*

# AI Agent Benchmarks: State of the Art (April 2026)

## SWE-bench Verified
- **Tests**: Real-world Python software engineering tasks from GitHub issues
- **Top scores**: Claude 4.5 Opus (high reasoning) 76.8%, Gemini 3 Flash 75.8%
- **Note**: SWE-bench Pro reveals contamination issues — best model scores 46% on Pro vs 81% on Verified
- **Limitations**: Only Python repos, curated 500-instance subset, doesn't test architecture decisions

## WebArena
- **Tests**: End-to-end web interaction (shopping, forums, CMS, GitLab)
- **Scores**: Improved from 14% to ~60% success rate over 2 years
- **Limitations**: Static snapshots, no dynamic JS-heavy SPAs, no real auth/payment flows
- **Key insight**: Large gap between single-action success and full task completion

## AgentBench
- **Tests**: Multi-domain evaluation (OS, database, web, digital card games)
- **Scores**: Varies by domain; strongest in OS (~60-70%), weakest in complex games
- **Limitations**: Each domain narrow, doesn't test cross-domain transfer
- **Key insight**: Domain-specific performance doesn't correlate across domains

## Cross-Benchmark Analysis
The biggest gap across all benchmarks is between **single-step tool use** and **multi-step planning with error recovery**. The jump from 14% to 60% on WebArena in 2 years shows rapid progress but the plateau suggests fundamental planning limitations.

## Implications for Self-Training
1. Need exercises spanning multiple domains (not just code)
2. Error recovery matters more than raw tool precision
3. Planning length correlates with success — train for longer horizons
4. Contamination is real — verified scores may overestimate true capability

## Sources
- swebench.com (official leaderboard)
- morphllm.com/swe-bench-pro (contamination analysis)
- steel.dev/results (cross-benchmark index)
- github.com/THUDM/AgentBench


## Sources

- https://www.swebench.com
- https://www.morphllm.com/swe-bench-pro
- https://leaderboard.steel.dev/results
- https://github.com/THUDM/AgentBench
