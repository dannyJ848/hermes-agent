# llm-inference-provider-comparison-friendliai-gmi

*Researched: 2026-04-15 09:47 CDT*

# LLM Inference Provider Comparison: FriendliAI vs GMI Cloud (Apr 2026)

## For autonomous agent use (24/7 training gym, coding, research, no use-case restrictions)

### API Compatibility
Both are OpenAI-compatible — swap base_url and api_key, no code changes needed.

### Key Model Pricing (per 1M tokens, input/output)

#### GLM-5.1 (primary brain candidate)
| Provider | Input | Output | Speed | TTFT |
|----------|-------|--------|-------|------|
| FriendliAI | $1.40 | $4.40 | 108.2 t/s | 1.12s |
| GMI Cloud | N/A | N/A | N/A | N/A |

Note: FriendliAI shows $0.95/$3.15 on some benchmark pages vs $1.40/$4.40 on their pricing page. Verify current rate at signup.

#### DeepSeek V3.2
| Provider | Input | Output |
|----------|-------|--------|
| FriendliAI | $0.50 | $1.50 |
| GMI Cloud | $0.27 | $0.41 |

#### Qwen3-235B-A22B
| Provider | Input | Output |
|----------|-------|--------|
| FriendliAI | $0.20 | $0.80 |
| GMI Cloud | $0.17 | $1.09 |

#### Other notable models (GMI only)
- GLM-4.6: $0.60/$2.00
- GLM-4.5-Air-FP8: $0.20/$1.10
- Qwen3 Coder 480B: $0.29/$1.20
- DeepSeek R1 0528: $0.70/$2.30

### Rate Limits (TPM)
| Tier | FriendliAI | GMI Cloud |
|------|-----------|-----------|
| Free/Tier 1 | Not published | 100K TPM |
| $5 paid | Not published | 450K-2M TPM |
| $1000 | Not published | 30M-150M TPM |

### Free Credits
- **FriendliAI**: $10K launch credit, up to $50K switch-from-competitor credit
- **GMI**: No published free tier, pay-as-you-go from $0

### Dedicated GPU Pricing
| GPU | FriendliAI | GMI Cloud |
|-----|-----------|-----------|
| H100 | $3.90/hr | $2.98/hr |
| H200 | $4.50/hr | $3.98/hr |
| B200 | $8.90/hr | N/A |

### Architecture
- **FriendliAI**: Serverless, proprietary continuous batching, best raw throughput
- **GMI**: Bare-metal H100/H200 with InfiniBand, best latency stability, no noisy-neighbor problem

### Verdict for Our Use Case
1. **Primary brain (GLM-5.1)**: FriendliAI — only provider with GLM-5.1, 108 t/s, $10K free credit
2. **Budget brain**: GMI's DeepSeek V3.2 at $0.27/$0.41 — 80% cheaper than GLM-5.1
3. **Judge/delegation**: FriendliAI's MiniMax-M2.5 at $0.30/$1.20

### Use-Case Restrictions
- **Neither** has published use-case restrictions (unlike Z.AI's Apr 2026 coding-only enforcement)
- FriendliAI explicitly supports "frontier model inference" with no mention of coding-only
- GMI serves research models (DeepSeek R1, etc.) which implies general use is fine

### Wiring Into Hermes
- FriendliAI serverless base_url: `https://api.friendli.ai/serverless/v1`
- Token from: friendli.ai/suite/~/setting/tokens
- OpenAI-compatible: just swap base_url + api_key in config.yaml


## Sources

- https://friendli.ai/pricing
- https://docs.gmicloud.ai/inference-engine/billing/price
- https://docs.gmicloud.ai/inference-engine/api-reference/rate-limit
- https://friendli.ai/docs/guides/openai-compatibility
- https://friendli.ai/promotions/10k-promotion
