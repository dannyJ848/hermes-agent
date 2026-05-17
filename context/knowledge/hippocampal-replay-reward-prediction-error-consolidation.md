# hippocampal-replay-reward-prediction-error-consolidation

*Researched: 2026-04-05 08:18 CDT*

# Hippocampal-Striatal Replay Biased by Reward-Prediction Error (Nature Communications, Nov 2025)

**Paper:** Roscow et al., Nature Communications 16, 10394 (2025)
**DOI:** 10.1038/s41467-025-65354-2

## Key Finding
Neural replay during rest/sleep is NOT biased by reward magnitude alone. Instead, it's biased by **reward-prediction error** (RPE) — the gap between expected and actual outcomes. Experiences where outcomes surprised the agent get prioritized for consolidation.

## Mechanism
- Rats trained on maze RL task with dissociated reward outcomes and prediction errors
- 4 RL model variants compared: replay biased by RPE best predicted behavior
- Hippocampus + ventral striatum preferentially reactivate reward-prediction and RPE signals during rest
- This tunes future reinforcement learning

## Application to Cerebrum Memory Consolidation

Our memory consolidation should NOT just replay "important" facts (high trust). Instead:

1. **Prioritize surprising outcomes** — Facts that contradicted expectations (prediction error > threshold) should be replayed first during consolidation cycles
2. **RPE-based decay resistance** — Memories formed from prediction errors should resist decay longer (they encode learning)
3. **Striatal analog for action memory** — Our "episodic" tier should track action-outcome pairs with prediction error signals, not just raw events
4. **Consolidation schedule** — Instead of uniform decay, use "rest periods" (low-activity cycles) to replay high-RPE memories

## Concrete Implementation
```python
# In consolidation loop:
for fact in episodic_memory:
    rpe = abs(fact.predicted_outcome - fact.actual_outcome)
    if rpe > RPE_THRESHOLD:
        fact.consolidation_priority = "high"
        fact.decay_resistance *= 1.5
        promote_to_semantic(fact)
```

## Connection to Epistemic Trust
This complements the F-G-R Trust Tuple: facts with high RPE should get a Formation score boost because they represent genuine learning (updating beliefs), not mere confirmation of existing knowledge.


## Sources

- https://www.nature.com/articles/s41467-025-65354-2
