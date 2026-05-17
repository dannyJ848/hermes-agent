# checkpoint-engine-hot-weight-swap

*Researched: 2026-03-31 22:58 CDT*

# Checkpoint-Engine: Hot-Swapping Trillion-Parameter Model Weights

## Key Insight
Moonshot's checkpoint-engine can update Kimi-K2 (1T params) across thousands of GPUs in ~20 seconds. This is the infrastructure that makes RL training on massive models practical -- you can update weights between inference steps without stopping serving.

## Two Update Modes
1. **Broadcast**: All inference instances update synchronously. Fastest. Pipeline with overlapped H2D, broadcast, and reload stages.
2. **P2P**: Send weights from existing instances to new ones without disrupting serving. Uses Mooncake Transfer Engine with RDMA.

## Pipeline Architecture
Three stages overlapped:
1. H2D: weights to GPU memory
2. Broadcast: among checkpoint engine workers via CUDA IPC
3. Reload: inference engine copies from broadcasted data

Falls back to serial when GPU memory is insufficient.

## Performance Benchmarks
- Kimi-K2 (1T FP8) on 256xH20: 16.04s broadcast, 16.75s P2P
- DeepSeek-V3.1 (FP8) on 256xH20: 11.33s broadcast
- Qwen3-235B on 8xH800: 6.22s broadcast
- GLM-4.5-Air on 8xH800: 3.47s broadcast

## Relevance to SOMA/Agents
- RL-trained agents need weight updates between episodes -- this makes it feasible at scale
- Hot-swapping means no downtime during model updates
- P2P mode enables dynamic scaling (add/remove inference instances live)
- The pipeline pattern (overlap communication and computation) applies to agent tool orchestration too
- Could enable continuous learning for medical AI (update model as new medical literature emerges)

## Source
- https://github.com/MoonshotAI/checkpoint-engine (930 stars, MIT)


## Sources

- https://github.com/MoonshotAI/checkpoint-engine
