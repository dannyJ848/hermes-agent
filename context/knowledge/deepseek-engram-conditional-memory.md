# deepseek-engram-conditional-memory

*Researched: 2026-03-31 22:38 CDT*

# DeepSeek Engram: Conditional Memory via Scalable Lookup

## Key Insight
Engram is a new sparsity axis for LLMs -- conditional memory via O(1) n-gram lookup. It's complementary to MoE (which sparsifies computation). Engram sparsifies MEMORY ACCESS.

## How It Works
- Modernizes classic N-gram embeddings for O(1) lookup
- Retrieves static N-gram memory and fuses with dynamic hidden states
- Deterministic addressing (not learned routing like MoE)
- Can offload massive embedding tables to host memory with minimal inference overhead

## Key Findings
1. **U-Shaped Scaling Law**: There's an optimal allocation between neural computation (MoE) and static memory (Engram)
2. **Iso-parameter tests**: Engram-27B beats MoE baselines on knowledge, reasoning, code, and math
3. **Mechanistic insight**: Engram relieves early layers from static pattern reconstruction, preserving effective depth for complex reasoning
4. **System efficiency**: Deterministic addressing means massive tables can live in RAM, not GPU

## Agentic Relevance
- Could enable agents with massive fact stores without GPU memory cost
- The "preserving depth for reasoning" insight applies to agent architectures
- O(1) lookup is essential for real-time tool/knowledge retrieval
- Complementary to vector DB approaches (faster, more deterministic)

## Source
- https://github.com/deepseek-ai/Engram (4.2k stars, Apache-2.0)


## Sources

- https://github.com/deepseek-ai/Engram
