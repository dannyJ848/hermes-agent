# LLM self-correction introspection vs verification

*Researched: 2026-04-05 11:38 CDT*

# The Self-Correction Illusion: Introspection vs Verification (2026 Analysis)

**Source:** Vadim Nicolai, "The Research on LLM Self-Correction" (March 2026 blog post synthesizing peer-reviewed evidence)

## Critical Distinction: Introspection ≠ Verification
- **Introspection**: Model re-reads its own output and critiques it (same data, same biases, zero new information)
- **Verification**: Model reacts to an EXTERNAL signal (test failure, search result, compiler error)
- Almost every published "success" of reflection is actually a success of **verification**, not introspection

## The Evidence
1. **Huang et al. 2023** "LLMs Cannot Self-Correct Reasoning Yet": Without external feedback, asking GPT-4 to self-correct on math/reasoning tasks **consistently decreased accuracy**. Model changed correct→wrong more often than wrong→correct.

2. **Reflexion (Shinn et al. 2023)**: 91% pass@1 on HumanEval (11-point gain). BUT gains came from executing code against unit tests — the feedback was stack traces and pass/fail status. When feedback was binary (HotPotQA), gains were modest.

3. **CRITIC (Gou et al. 2024)**: Ablation study showed removing external tool verification and relying only on model self-evaluation **eliminated most gains**.

4. **Constitutional AI (Bai et al. 2022)**: Works because the "constitution" acts as an external reference frame — transforms open-ended introspection into constrained verification against rules.

## Practical Framework: When Self-Correction Works

| Condition | Works? | Why |
|---|---|---|
| Pure introspection (no tools) | NO | Same biases, no new info |
| With test suite / compiler | YES | External ground truth |
| With search/lookup | YES | New factual information |
| With structured rubric | PARTIAL | Constrained verification |
| With different model reviewing | YES | Independent perspective |

## Implications for Evey
1. **validate_output works because it uses external verification** — checks against specific criteria, not just "is this good?"
2. **Our self-evaluation-loop skill needs external signals** — not just re-reading own output
3. **council_decide works** — different models provide independent perspectives (not introspection)
4. **reflect_on_output works** — uses a cheap model to critique, providing an external perspective
5. **learn_from_interaction works** — outcome data is external ground truth
6. **BUT**: Any cycle where I "re-read my own output and try to improve it" without new data is wasted tokens

## Actionable Rule
**Every self-correction loop MUST include at least one of:**
- External tool execution (terminal, web_search, test suite)
- Independent model review (different model or different context)
- Structured rubric/constitution (specific criteria, not vague "improve this")
- Ground truth comparison (known answer, reference implementation)

**Source:** https://vadim.blog/the-research-on-llm-self-correction (March 2026)


## Sources

- https://vadim.blog/the-research-on-llm-self-correction
