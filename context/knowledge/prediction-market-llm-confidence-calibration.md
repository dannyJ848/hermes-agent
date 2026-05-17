# prediction-market-LLM-confidence-calibration

*Researched: 2026-04-05 11:15 CDT*

# Fake Prediction Markets for LLM Confidence Calibration

**Source:** Todasco, SDSU (arXiv 2512.05998, Dec 2025) — "Going All-In on LLM Accuracy: Fake Prediction Markets, Real Confidence Signals"

## Key Findings

1. **Prediction market framing surfaces calibrated confidence**: When LLMs are asked to bet fictional "LLMCoin" (1-100,000) on their predictions instead of just saying yes/no, the wager amount becomes a reliable confidence signal.

2. **Whale bets = near-perfect accuracy**: Bets of 40,000+ coins were correct ~99% of the time. Small bets (<1,000 coins) showed only ~74% accuracy. This creates a natural calibration curve from wager size alone.

3. **Accuracy improvement**: Incentive condition showed modestly higher accuracy (81.5% vs 79.1%, p=.089) but significantly faster learning across rounds (12.0 vs 2.9 percentage-point improvement Round 1→4, p=.011).

4. **Setup**: 100 math/logic questions, 6 baseline models answering, 3 predictor models forecasting correctness with/without betting mechanism. 5,400 predictions per condition.

5. **Core insight**: The betting mechanic creates a **legible confidence signal** absent from binary yes/no outputs. Simple financial framing helps transform LLMs into risk-aware forecasters, making internal beliefs visible and usable.

## Relevance to Hermes/Evey Agent

- **Delegation confidence scoring**: Instead of just validating output (validate_output tool), could ask the delegating model to "bet" 1-10 tokens on its confidence. Higher bets = higher reliability signal.
- **Autonomous decision calibration**: When Evey decides between autonomous action vs. deferring to Danny, could use a wager-style confidence estimate as the routing signal.
- **Practical implementation**: Add a "confidence_wager" field to delegation prompts — "How many of your 10 tokens would you bet on this answer being correct?" Map wager → reliability score.

## Sources

- https://arxiv.org/abs/2512.05998
