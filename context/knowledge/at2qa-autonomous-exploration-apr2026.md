# AT2QA: Autonomous Exploration for Temporal Question Answering
**Paper**: arXiv:2603.01853 (March 2026)
**Authors**: Xufei Lv, Jiahui Yang et al.

## Key Innovation
Training-free agent that lets LLMs autonomously explore and self-correct. Beats rigid workflows by 10.7+ absolute points on TKG benchmarks.

## Techniques
1. Autonomous exploration > fixed reasoning workflows
2. Dynamic self-correction during reasoning
3. Training-free experience mining from successful trajectories
4. Compact few-shot demonstration library distilled from self-generated paths
5. Transparent audit trail for every prediction

## Results
- +10.7 on MultiTQ
- +4.9 on Timeline-CronQuestion
- +11.2 on Timeline-ICEWS-Actor

## Applications to Evey
- Tips should be GUIDES not COMMANDS (flexible conditions > rigid rules)
- Mine successful tool trajectories for new tips
- Zero-shot autonomous exploration is already effective — tips enhance, not replace
- Audit trail → our tool call logging serves the same purpose

