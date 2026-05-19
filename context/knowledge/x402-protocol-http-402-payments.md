# x402-protocol-http-402-payments

*Researched: 2026-04-11 15:26 CDT*

# x402 Protocol: HTTP 402 Payment Required for AI Agents

## Overview
x402 is an open payment protocol created by Coinbase and Cloudflare (May 2025) that activates the dormant HTTP 402 "Payment Required" status code. It enables instant stablecoin (USDC) payments embedded directly into HTTP request/response cycles — no API keys, subscriptions, or credit cards needed.

## How It Works
1. Client makes HTTP request to a paid resource
2. Server responds with `402 Payment Required` + payment spec (token, amount, wallet, chain)
3. Client signs on-chain transaction, attaches payment proof to request header
4. Facilitator middleware verifies payment settled on-chain
5. Server delivers the resource
6. Total time: ~2 seconds. Zero protocol fees. Only gas fees (fractions of a cent on Base/Solana).

## Scale (as of March 2026)
- **119M+ transactions** on Base, **35M+** on Solana
- **$600M annualized volume**
- Supported chains: Base, Ethereum, Arbitrum, Polygon, Solana
- x402 Foundation co-governed by Coinbase and Cloudflare

## Key Use Cases
1. **API Monetization** — Pay-per-request (e.g., Firecrawl charges $0.01/scrape)
2. **AI Inference** — Pay-per-prediction, no GPU reservations needed
3. **Content Paywalls** — Per-article micropayments without subscriptions
4. **Data Marketplaces** — Per-query pricing on datasets
5. **Agent-to-Agent Payments** — Autonomous agents paying each other for services
6. **MCP Tool Monetization** — Wrap any MCP server with pay-per-call in 2 minutes
7. **Compute Provisioning** — Pay-per-minute GPU/container rental
8. **Micropayment Streaming** — Continuous payment for streaming services

## Relevance to Hermes Agent / SOMA
- **MCP monetization**: Any MCP tool server could be wrapped with x402 for pay-per-use
- **Agent economy**: As autonomous agents proliferate, HTTP-native payments become critical infrastructure
- **API cost optimization**: Instead of subscription tiers, agents pay only for what they consume
- **Firecrawl integration**: Already using x402 ($0.01/scrape) — directly relevant to our web extraction pipeline

## Technical Architecture
- Payment proof in HTTP headers (no redirect flows)
- Facilitator = lightweight middleware that verifies on-chain settlement
- Supports multiple EVM chains + Solana
- Zero protocol fees — only blockchain gas costs
- Google announced AP2 integration (aligns with x402 standard)

## Sources
- xpay.sh blog: x402 use cases
- Sherlock.xyz: x402 protocol deep dive
- Coinbase/Cloudflare co-founded the x402 Foundation


## Sources

- https://www.xpay.sh/blog/article/x402-protocol-use-cases/
- https://sherlock.xyz/post/x402-explained-the-http-402-payment-protocol
- https://medium.com/@BizthonOfficial/http-402-the-payment-protocol-thats-rewiring-the-internet-6c76f55b78ce
