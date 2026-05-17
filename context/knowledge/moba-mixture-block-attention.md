# moba-mixture-block-attention

*Researched: 2026-03-31 22:44 CDT*

# MoBA: Mixture of Block Attention for Long-Context LLMs

## Key Insight
MoBA applies MoE principles to the ATTENTION MECHANISM itself. Instead of attending to all tokens, each query token learns to attend only to the most relevant KV blocks. This is "less structure" -- the model decides where to look, not the engineer.

## How It Works
1. Full context is divided into blocks
2. Each query token uses a parameterless top-k gating mechanism to select most relevant KV blocks
3. Attention is computed only on selected blocks
4. Can seamlessly transition between full and sparse attention modes

## Performance
- Tested with 1M context length
- moba_efficient kernel: up to 40x speedup over naive implementation
- Already deployed in production for Kimi's long-context requests

## Key Design Decisions
- **Trainable block sparse attention**: Model learns which blocks matter
- **Parameterless gating**: No extra parameters for routing (unlike MoE)
- **Not drop-in**: Requires continued training of existing models
- **Flash Attention compatible**: Built on flash-attn 2.6.3

## Relevance to SOMA
- Long patient histories = long context. MoBA could make 256K+ context feasible
- Medical conversations need full attention on critical parts but can sparse-attend filler
- The "model decides where to look" approach mirrors how doctors read charts (focus on key findings)
- Could be combined with Baichuan-M3's segmented pipeline for stage-aware attention

## Source
- https://github.com/MoonshotAI/MoBA (2.1k stars, MIT license)
- Paper: arXiv 2502.13189


## Sources

- https://github.com/MoonshotAI/MoBA
