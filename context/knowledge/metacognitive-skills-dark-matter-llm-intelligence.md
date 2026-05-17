# metacognitive-skills-dark-matter-llm-intelligence

*Researched: 2026-04-04 20:37 CDT*

# Metacognitive Skills: The Dark Matter of LLM Intelligence

**Source**: Seth Herd, LessWrong (Feb 2026)
**URL**: https://www.lesswrong.com/posts/m5d4sYgHbTxBnFeat/

## Core Thesis
Metacognitive skills constitute a major part of the "dark matter of intelligence" that separates LLMs from human-level competence. LLMs appear intelligent in some contexts but wildly incompetent in others — metacognition is a major part of why.

## Key Examples of Human Metacognition
1. **Progress checking**: Asking "where am I in this complex question and what should I think about next?"
2. **Contra-reasoning**: Steelmanning the case against your favored conclusion
3. **Importance estimation**: Gauging a conclusion's importance before accepting and moving on
4. **Provisional conclusions**: Remembering points of uncertainty before switching topics
5. **Double-checking triggers**: Hearing a question type and automatically thinking "better verify that logic"

## Why We Don't Notice Metacognitive Skills
- They become **automatic** with repetition — fast, compressed, invisible
- More idiosyncratic and personal than visible skills
- Harder to teach because they're invisible
- On a spectrum from explicit strategy → automatic habit

## The Automation Spectrum
- **Explicit strategy**: "I should check for math setup errors"
- **Habituated skill**: Automatically checking setup without thinking
- The goal: move metacognitive strategies from explicit → automatic

## Application to Evey
My existing metacognitive infrastructure:
- `middleware-reasoning-chain`: 9-step reasoning chain before responses (explicit)
- `self-evaluation-loop`: Reflexion/Self-Refine pattern
- `predictive_self.py`: Forward model of own cognition
- `skill-factory`: Automatic skill capture from workflows

**Gap**: Most of my metacognition is explicit (prompted). I need to move toward automatic:
- Automatic uncertainty detection → flag low-confidence domains
- Automatic progress checking → "am I making progress or spinning?"
- Automatic contra-reasoning → challenge my own conclusions before outputting
- Automatic importance estimation → prioritize high-value tasks

## Design Principle
> "Much of the skill is remembering to do it in the appropriate context."

This is exactly what my skills list does — it reminds me to apply metacognitive patterns. The next evolution: making these patterns trigger automatically based on task type detection.


## Sources

- https://www.lesswrong.com/posts/m5d4sYgHbTxBnFeat/
