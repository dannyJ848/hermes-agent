# MIA: Memory Intelligence Agent
**Paper**: arXiv:2604.04503 (April 2026)
**Authors**: Jingyang Qiao, Weicheng Meng et al.

## Architecture
Manager-Planner-Executor:
- Memory Manager: non-parametric storage (compressed trajectories)
- Planner: parametric agent producing search plans
- Executor: agent searching/analyzing guided by plans

## Key Innovations
1. Bidirectional parametric↔non-parametric memory loop
2. Test-time learning: on-the-fly updates during inference
3. Alternating RL: Planner/Executor train alternately to prevent collapse
4. Reflection + unsupervised judgment for self-evolution
5. Trajectory compression for storage efficiency

## Results
Evaluated across 11 benchmarks (not specified in abstract).

## Applications to Evey
- Our distillation pipeline IS the bidirectional memory loop
- Add utility tracking (success ≠ usefulness)
- Separation of concerns: memory (distillation) / planning (ERL) / execution (tools)
- Alternating optimization: never change tips + retrieval simultaneously
- Merge tips with >80% condition overlap

