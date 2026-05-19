# mooncake-kv-centric-serving

*Researched: 2026-03-31 22:58 CDT*

# Mooncake: KV-Centric Disaggregated LLM Serving

## Key Insight
Mooncake pioneered a fundamentally new serving architecture: decouple prefill from decode by treating the KV cache as the FIRST-CLASS CITIZEN. Instead of one GPU doing both, prefill GPUs generate KV caches, which are transferred to decode GPUs via RDMA. This won FAST 2025 Best Paper.

## Architecture
- **Mooncake Store**: Distributed KV cache pool (GPU + host + remote tiers)
- **Mooncake Transfer Engine**: RDMA-based zero-copy data transfer
- **Prefill-Decode (PD) Disaggregation**: Separate GPU pools for each phase
- **KV Cache Reuse**: Cache and share KV states across requests

## Production Deployment
- Powers Kimi K2 on 128 H200 GPUs
- 224k tokens/sec prefill, 288k tokens/sec decode
- Updates 1T parameter Kimi-K2 across thousands of GPUs in ~20s (via checkpoint-engine)
- Integrated into vLLM, SGLang, TensorRT-LLM, LMDeploy, LMCache

## Industry Adoption (massive)
- vLLM v1: native Mooncake KV Connector
- SGLang: hierarchical KV caching with Mooncake Store backend
- TensorRT-LLM: Mooncake Transfer Engine for KV transfer
- NIXL: Mooncake as backend plugin
- Joined PyTorch Ecosystem (Feb 2026)
- FlexKV: distributed KV store with Mooncake Transfer Engine

## Agentic Relevance
- PD disaggregation = could serve medical agents with separate fast-decode pools
- KV cache reuse = multiple patients with similar conditions share computation
- checkpoint-engine = hot-swap model weights without downtime (relevant for model updates)
- RDMA zero-copy = real-time agent response at scale

## Source
- https://github.com/kvcache-ai/Mooncake (FAST 2025 Best Paper)
- Production backbone for Kimi K1.5, K2, K2.5


## Sources

- https://github.com/kvcache-ai/Mooncake
