# gepa-deepeval-production-prompt-optimization

*Researched: 2026-04-03 13:08 CDT*

# GEPA Integration via DeepEval: Production-Ready Prompt Optimization (April 2026)

**Date:** April 3, 2026
**Source:** https://deepeval.com/docs/prompt-optimization-gepa

## Key Discovery
GEPA is no longer just a research paper — it's a **production-ready library** integrated into DeepEval (the LLM evaluation framework). This means SOMA can use it directly without implementing the algorithm from scratch.

## Installation
```bash
pip install deepeval
```

## Usage for SOMA
```python
from deepeval.metrics import AnswerRelevancyMetric
from deepeval.prompt import Prompt
from deepeval.optimizer import PromptOptimizer
from deepeval.optimizer.algorithms import GEPA

# SOMA medical explanation prompt template
prompt = Prompt(
    text_template="""
    You are a bilingual (EN/ES) medical education tutor.
    Explain the anatomy of {structure_name} at {audience_level} level.
    Include: location, function, related structures, clinical significance.
    Language: {language}
    """
)

optimizer = PromptOptimizer(
    algorithm=GEPA(
        iterations=10,        # 10 mutation cycles
        pareto_size=5,        # 5 goldens in Pareto validation
        minibatch_size=4      # 4 goldens per feedback round
    ),
    model_callback=model_callback
)

# Optimize with quiz score metrics
optimized_prompt = optimizer.optimize(
    prompt=prompt,
    goldens=medical_education_goldens,
    metrics=[AnswerRelevancyMetric()]
)
```

## GEPA Parameters
| Parameter | Default | SOMA Recommendation |
|-----------|---------|---------------------|
| iterations | 5 | 10 (more data = better optimization) |
| pareto_size | 3 | 5 (balance EN + ES performance) |
| minibatch_size | 8 | 4 (lower cost per iteration) |
| random_seed | time-based | 42 (reproducibility) |
| tie_breaker | PREFER_CHILD | PREFER_CHILD (favor innovation) |

## 5-Step Algorithm
1. **Golden Splitting** — Split evaluation data into validation (D_pareto) and feedback (D_feedback) sets
2. **Pareto Selection** — Choose parent prompt from Pareto frontier
3. **Feedback & Mutation** — Collect metric feedback on minibatch, use LLM to rewrite prompt
4. **Acceptance** — If child improves over parent, add to candidate pool
5. **Final Selection** — Return best prompt from Pareto frontier

## SOMA Integration Plan
1. **Phase 1:** Create golden evaluation dataset for anatomy explanations (EN + ES, 3 audience levels = 6 combinations)
2. **Phase 2:** Run GEPA optimization on explanation template for each combination
3. **Phase 3:** Deploy optimized prompts to SOMA's explanation engine
4. **Phase 4:** Continuous optimization using real quiz performance data

## Multilingual Note
GEPA paper tested only English. For SOMA's bilingual use case:
- Run optimization separately for EN and ES prompts
- Use a bilingual metric (cross-lingual semantic similarity) to ensure EN/ES explanations are consistent
- Consider treating language as a dimension in the Pareto frontier

## Why This Matters for SOMA
- **75% time reduction** in prompt engineering (per JMIR SNOMED mapping paper's similar approach)
- **35x fewer API calls** than RL-based optimization (per GEPA paper)
- **Measurable improvement** via DeepEval metrics (can track quiz score improvements)
- **Reproducible** with random_seed parameter

## Sources
- https://deepeval.com/docs/prompt-optimization-gepa
- https://arxiv.org/abs/2507.19457 (original GEPA paper)


## Sources

- https://deepeval.com/docs/prompt-optimization-gepa
- https://arxiv.org/abs/2507.19457
