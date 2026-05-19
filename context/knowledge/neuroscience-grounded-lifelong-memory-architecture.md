# neuroscience-grounded-lifelong-memory-architecture

*Researched: 2026-04-05 05:07 CDT*

# Human-Like Lifelong Memory: Neuroscience-Grounded Architecture

**Paper:** arXiv:2603.29023v1 (Mar 2026) by Diego C. Lerma-Torres, Universidad de Guanajuato

## Core Thesis
Context expansion alone degrades reasoning by up to 85%. Instead, implement bio-inspired memory with three principles:

### Principle 1: Memory Has Valence, Not Just Content
- Pre-computed emotional-associative summaries called **valence vectors**
- Organized in an emergent **belief hierarchy** (inspired by Beck's CBT cognitive model)
- Enables instant orientation before deliberation — System 1 can act on "gut feel" from valence
- Memories tagged with emotional weight, not just semantic content

### Principle 2: Retrieval Defaults to System 1 with System 2 Escalation
- **System 1 (default):** Automatic spreading activation + passive priming
- **System 2 (escalation):** Deliberate retrieval only when needed
- **Graded epistemic states:** Instead of binary "known/unknown", memories have confidence levels
  - Addresses hallucination structurally — uncertain memories are flagged as such
- **Reconsolidation:** Retrieval can modify memory (not just read) — memories update when accessed

### Principle 3: Encoding Is Present-Moment and Goal-Directed
- **Thalamic gateway:** Tags and routes information between memory stores
- **Present-moment tagging:** New info is tagged with current context/goals
- **Active gist formation:** Executive function forms summaries through curiosity-driven investigation
- **Context flush:** Old context is cleared, not accumulated

## Key Insight for Cerebrum
The paper's **valence vectors** map directly to Cerebrum's trust scoring. Instead of binary trusted/untrusted, use graded epistemic states (0-1 confidence) with reconsolidation — every time a memory is recalled, its confidence is re-evaluated against current knowledge.

The **thalamic gateway** concept maps to our pre-action recall hook — it should tag incoming info AND route it to the right memory tier before the model responds.

## Convergence Property
Over time, the system converges toward System 1 processing — the computational analog of clinical expertise. Interactions become cheaper, not more expensive, with experience. This is exactly what Cerebrum should do: commonly-used facts should become faster to access, not require full retrieval each time.

## Relevance to SOMA/Evey
- Valence vectors → extend Cerebrum trust scoring with emotional/associative weight
- Graded epistemic states → replace binary trust with confidence spectrum
- Thalamic gateway → enhance pre-action recall with routing logic
- Gist formation → Cerebrum working memory should form compressed summaries, not store raw data


## Sources

- https://arxiv.org/html/2603.29023v1
