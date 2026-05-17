# hermes-traces-finetuning-guide

*Researched: 2026-04-02 17:12 CDT*

# Fine-Tuning Open Models with Hermes Reasoning Traces

**Source:** lambda/hermes-agent-reasoning-traces (Apache 2.0)
**Date:** April 2026

## Practical Fine-Tuning Path (for SOMA)

### Framework Options
1. **MLX (Apple Silicon)** — Best for Mac Studio M4 with 128GB+ unified memory
   - mlx-lm supports LoRA fine-tuning natively
   - Can handle 27B model with sufficient unified memory
   - ~3-5x slower than A100 but feasible for 7.6K examples

2. **Axolotl** — Native ShareGPT format support, customizable chat templates
   - Well-documented for Hermes-format training
   - Primarily NVIDIA GPUs, MPS backend possible

3. **Unsloth** — Fast training on single GPUs, 2-5x speedup
   - Some Mac support, primarily NVIDIA
   - Supports ShareGPT + thinking blocks

4. **TRL SFTTrainer** — HuggingFace's library, any PyTorch backend
   - Custom chat templates for Hermes format
   - Works with MPS on Mac

### GPU Requirements for ~27B Model
| Method | VRAM | Hardware |
|--------|------|----------|
| Full fine-tuning | 54-108GB | 2x A100 |
| LoRA (rank 16-64) | 20-40GB | A6000/A100 |
| QLoRA (4-bit) | 16-20GB | RTX 3090/4090 |
| MLX LoRA (Mac) | Unified memory | Mac Studio M4 128GB+ |

### Key Practical Details
- **Thinking blocks**: Should be included in training loss (they represent reasoning)
- **Format alignment**: Qwen3 uses `<think`/`</think` natively — Hermes uses `<think reasoning="true">` — compatible as text tokens
- **Loss masking**: Train only on assistant turns (including thinking blocks), not system/human/tool input
- **7.6K examples**: Sufficient for format/style adaptation with LoRA, use 2-4 epochs
- **LoRA rank**: 16-64 recommended
- **Learning rate**: 1e-5 to 5e-5 (low to preserve base capabilities)

### GEPA Integration
- GEPA (Genetic-Pareto Prompt Evolution) can use these traces as ground truth
- DSPy can bootstrap few-shot examples from successful traces
- GRPO as alternative RL approach for reasoning optimization


## Sources

- https://huggingface.co/datasets/lambda/hermes-agent-reasoning-traces
