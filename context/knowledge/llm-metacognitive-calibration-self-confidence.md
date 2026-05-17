# LLM metacognitive calibration self-confidence

*Researched: 2026-04-05 11:33 CDT*

# LLM Metacognitive Calibration: Self-Reported Confidence Is Poorly Calibrated

**Key Finding:** A comprehensive 2026 study (Naderi et al., Nature npj Gut and Liver) tested 48 LLMs on 300 gastroenterology board-exam questions and found **all models demonstrate poor self-estimation of certainty**, regardless of actual accuracy.

## Critical Data Points
- Even the best-calibrated models (o1 preview, GPT-4o, Claude 3.5 Sonnet) showed substantial overconfidence
- Brier scores: 0.15–0.20 (lower is better; perfect = 0)
- AUROC ~ 0.6 (barely above random 0.5 for confidence discrimination)
- Models maintained **high confidence regardless of question difficulty or response correctness**
- This is described as an "intrinsic limitation" across all tested architectures, sizes, and generations

## Complementary Finding (arXiv 2603.29559)
- Self-reported confidence achieved **better calibration** than other methods (avg ECE 0.166 vs 0.229) when used as a grading signal
- Suggests self-confidence is the *least bad* option among practical approaches

## Implications for Agent Design
1. **Never trust model self-assessed confidence at face value** — our 59% baseline calibration is consistent with these findings
2. **External verification always required** — validate_output tool is essential, not optional
3. **Confidence scores should be adjusted downward** — if model says 80% confident, assume ~60%
4. **Discrimination between correct/incorrect is near-random** — model cannot reliably tell when it's wrong
5. **Multi-model agreement is a stronger signal** than any single model's confidence

## Relevance to Evey
- Our metacognitive calibration tracker (59% baseline) aligns with literature
- The validate_output tool's approach of cross-checking is structurally correct
- Should weight delegation_stats and tool success rates higher than model self-reports

**Sources:** 
- Naderi et al. (2026) "Across generations, sizes, and types, LLMs poorly report self-confidence" Nature npj Gut and Liver 3:6
- "When Can We Trust LLM Graders?" arXiv:2603.29559 (2025)
- Springer: "Quantifying uncert-AI-nty" Memory & Cognition (2025)


## Sources

- https://www.nature.com/articles/s44355-026-00053-3
- https://arxiv.org/html/2603.29559v1
- https://link.springer.com/article/10.3758/s13421-025-01755-4
