# contradiction-detection-nli-memory

*Researched: 2026-04-05 06:28 CDT*

# Detecting LLM Agent Contradictions: NLI + Total Variance

**Source:** Ashish Jha (dev.to, March 2026), based on arXiv:2602.23271

## Core Problem
LLM agents can produce logically opposite answers to the same query across runs. Embedding variance measures "outputs look different" — NLI contradiction detection measures "outputs are logically opposite." For medical/legal/financial AI, this distinction is critical.

## Method: Two-Layer Detection

### Layer 1: Total Variance (Embedding-Level)
```
TV(X) = (1 / 2n(n-1)) × Σᵢ Σⱼ ||xᵢ - xⱼ||²
```
Where xᵢ are L2-normalized sentence embeddings. Captures surface-level inconsistency.

### Layer 2: NLI Contradiction Detection
Use a pretrained NLI model to classify candidate pairs as:
- **Entailment** (consistent)
- **Neutral** (unrelated)
- **Contradiction** (logically opposite)

### Combined: Reliability Score
- High TV + high contradiction rate = unreliable agent
- High TV + low contradiction rate = varied but consistent (acceptable)
- Low TV + low contradiction rate = reliable agent

## Implementation Components
1. `sentence_transformers` for embeddings (all-MiniLM-L6-v2)
2. NLI model for contradiction classification
3. Total Variance calculator
4. Reliability score aggregation

## Relevance to Evey's Cerebrum

### Contradiction Detection Between Memories
Before writing a new semantic fact, check it against existing facts:
1. Embed the new fact and retrieve top-K similar existing facts
2. Run NLI on each pair (new fact, existing fact)
3. If contradiction detected → flag for review, don't auto-write
4. If entailment → reinforce existing fact (boost trust score)
5. If neutral → write as new independent fact

### Trust Score Enhancement
- Memories that survive contradiction checks get a trust boost
- Memories that are contradicted by newer evidence get flagged for re-grounding
- Multiple entailment confirmations → higher confidence

### Practical Integration
- Could use local Ollama NLI model (no API cost)
- Run contradiction checks as part of offline consolidation (All-Mem pattern from cycle 97)
- Flag rate could be a Cerebrum health metric (high flag rate = epistemic drift)

## Code Sketch for Evey
```python
# In cerebrum consolidation pipeline:
def check_contradiction(new_fact, existing_facts):
    embeddings = embedder.encode([new_fact] + existing_facts)
    similar = cosine_search(embeddings[0], embeddings[1:], top_k=5)
    for fact in similar:
        nli_result = nli_model.classify(new_fact, fact)
        if nli_result == "CONTRADICTION":
            flag_for_review(new_fact, fact)
            return False
        elif nli_result == "ENTAILMENT":
            boost_trust(fact)
    return True  # safe to write
```


## Sources

- https://dev.to/ashish8389/detecting-llm-agent-contradictions-using-nli-and-total-variance-a-python-implementation-2bho
- https://arxiv.org/abs/2508.17127
