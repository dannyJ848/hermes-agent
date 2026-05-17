# x402 HTTP Payment Protocol for AI Agents

*Researched: 2026-04-11 15:20 CDT*

# x402: HTTP 402 Payment Protocol

x402 (Coinbase + Cloudflare) makes HTTP 402 "Payment Required" a native stablecoin payment mechanism for APIs and AI agents. As of March 2026: 119M+ transactions, ~$600M annualized volume, zero protocol fees. 2-second end-to-end payment flow: client requests → server returns 402 with payment spec → client signs USDC tx → facilitator verifies → resource delivered. No accounts or API keys needed. Key insight for agent systems: autonomous agents need programmatic payment for machine-to-machine commerce. API services may start returning 402 requiring payment retry logic in agent tool calls. Supports Base, ETH, Arbitrum, Polygon, Solana. GENIUS Act (July 2025) provides US regulatory clarity.

## Sources

- https://sherlock.xyz/post/x402-explained-the-http-402-payment-protocol
