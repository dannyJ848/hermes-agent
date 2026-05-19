# showui-gui-visual-agent

*Researched: 2026-04-05 04:03 CDT*

# ShowUI: Lightweight 2B GUI Visual Agent

**Paper:** arXiv:2411.17465 (Nov 2024)
**Authors:** Kevin Qinghong Lin et al. (Show Lab, Microsoft)

## Key Innovations

1. **UI-Guided Visual Token Selection**: Formulates screenshots as a UI connected graph, adaptively identifies redundant relationships, and uses this as criteria for token selection during self-attention. Reduces 33% of redundant visual tokens, speeds up performance 1.4x.

2. **Interleaved Vision-Language-Action Streaming**: Unifies diverse GUI task needs — manages visual-action history in navigation and pairs multi-turn query-action sequences per screenshot for training efficiency.

3. **Small-scale High-quality Data**: Only 256K instruction-following samples with careful curation and resampling to address data type imbalances.

## Performance
- **75.1% zero-shot screenshot grounding** with just 2B params
- Tested on Mind2Web (web), AITW (mobile), MiniWob (online)
- Outperforms much larger models on grounding tasks

## Relevance to SOMA/Agent Work
- The UI-guided token selection approach could inspire efficient visual processing in medical image analysis
- The interleaved streaming pattern is relevant for multi-turn agent interactions
- Proves small models (2B) can compete with 72B+ models on GUI tasks when architecture is right
- Open-source: https://github.com/showlab/ShowUI

## Comparison to Related Work
- SE-GUI (7B) beats 72B via self-evolution — similar "small but smart" philosophy
- GUI-Actor (Microsoft NeurIPS 2025) uses coordinate-free grounding — complementary approach


## Sources

- https://arxiv.org/abs/2411.17465
- https://medium.com/voxel51/hacking-showui-2b-what-i-learned-using-this-gui-agent-91d8c081818e
