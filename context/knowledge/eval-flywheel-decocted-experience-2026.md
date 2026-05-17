# eval-flywheel-decocted-experience-2026

*Researched: 2026-04-12 23:43 CDT*

# Evaluation Flywheel: Tournament-Based Tip Evolution

## Status (Apr 13, 2026)
- 1,734 distilled tips across 34 types
- 253+ Elo-rated tips (range 1142-1240, avg 1200)
- 3-judge panel (Phi-3 + Llama 8B + MiniMax) at ~9s per matchup
- Borda aggregation with margin tracking (1.0, 0.67, 0.33)

## Key Research Findings Applied

### Decocted Experience (Shen et al., MIT, Apr 2026)
- arXiv: 2604.04373
- **Core insight**: Effective context construction depends on "decocted" experience -- extracting essence, organizing coherently, retrieving salient info
- Raw memory is insufficient; performance scales with decoction quality, not raw quantity
- Concept trees enable targeted context retrieval by task structure, not surface similarity

### Test-Time Self-Improvement (Acikgoz et al., UIUC, Oct 2025)
- arXiv: 2510.07841
- **Core insight**: Self-awareness + self-data augmentation + test-time fine-tuning
- +5.48% accuracy with 68x fewer training samples
- Key: only augment from uncertain cases (high confidence correct = no learning signal)

### Multi-Elo Rating System (MERS)
- Generalizes scalar Elo to multi-dimensional ratings
- Maintains per-threshold ratings for margin-of-victory (CDF of spread)
- Multivariate Elo with concept association matrices for knowledge domains
- Captures intransitive dynamics (A > B, B > C, C > A)

## Architecture Decisions
1. **Elo over Borda**: Handles varying opponent strength, produces calibrated ratings
2. **3-judge panel**: Creates margin variance (1.0/0.67/0.33) instead of always-1.0
3. **Domain-sweep first**: Rate all domains broadly before deep-diving any one
4. **Research-to-distillation pipeline**: New findings get tips inserted immediately, then rated

## Files
- `~/subconscious/eval_flywheel.py` - Tournament runner (724 lines)
- `~/subconscious/research_distill.py` - Phase 2 distillation pipeline
- `~/.hermes/cerebrum_memory.db` - Tip storage + Elo ratings


## Sources

- https://arxiv.org/abs/2510.07841
- https://arxiv.org/html/2604.04373v1
- https://www.emergentmind.com/topics/multi-elo-rating-system-mers
