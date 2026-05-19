# chain-of-x-paradigms-survey

*Researched: 2026-04-07 00:34 CDT*

# Beyond Chain-of-Thought: Chain-of-X Paradigms for LLMs (Survey)

**Paper:** COLING 2025, ACL Anthology 2025.coling-main.719
**Authors:** Yu Xia, Rui Wang, Xu Liu, et al.

## Key Taxonomy
Chain-of-X (CoX) generalizes CoT's sequential structure to diverse domains:

### Node Types (what the "X" is):
- **Chain-of-Thought (CoT):** X = reasoning steps
- **Chain-of-Verification (CoVe):** X = verification questions
- **Chain-of-Density (CoD):** X = density levels for summarization
- **Chain-of-Note (CoN):** X = reading notes for document QA
- **Chain-of-Knowledge (CoK):** X = knowledge retrieval steps
- **Chain-of-Symbol (CoS):** X = symbolic representations
- **Chain-of-Image (CoI):** X = visual reasoning steps
- **Chain-of-Table (CoT-Table):** X = table manipulation steps

### Application Tasks:
- Mathematical reasoning, commonsense reasoning, code generation
- Multi-modal reasoning, planning, fact-checking
- Summarization, dialogue, retrieval-augmented generation

## Why It Matters for Agents
- The CoX pattern is a universal decomposition strategy — any multi-step task can be "chained"
- For Hermes: agent tool calls are essentially a Chain-of-Actions (CoA)
- CoVe (verification chain) maps directly to output validation patterns
- CoK (knowledge chain) maps to research workflows
- The survey suggests agents could dynamically select which "chain type" to use based on task

## Future Directions Noted
- Combining multiple chain types (e.g., CoT + CoVe for self-checking reasoning)
- Adaptive chain length (similar to Draft-Thinking's adaptive depth)
- Chain-of-X for multi-agent coordination (chains across agents, not just steps)


## Sources

- https://aclanthology.org/2025.coling-main.719/
