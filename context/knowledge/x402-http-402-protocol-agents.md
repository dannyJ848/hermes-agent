# x402-http-402-protocol-agents

*Researched: 2026-04-11 13:36 CDT*

# x402 Protocol: HTTP 402 for Autonomous AI Agent Payments

## Overview
x402 is an open payment standard (released May 2025 by Coinbase Developer Platform) that activates the long-dormant HTTP 402 "Payment Required" status code for machine-to-machine payments. It enables AI agents to make per-request stablecoin micropayments without human intervention, account creation, or credit card management.

## Key Architecture
- **HTTP-native**: Payment is embedded directly in the request-response lifecycle
- **Protocol flow**: Client requests → Server returns 402 with price → Client signs payment → Server verifies onchain → Fulfillment
- **Blockchain-agnostic**: Works with all EVM-compatible chains and Solana
- **Stablecoin-friendly**: Uses USDC/USDT for predictable pricing
- **Zero account setup**: No API keys, no subscriptions, no invoicing

## Why It Matters for Agents
- Removes human bottleneck from autonomous payment workflows
- Agents handle 402/sign/retry loop naturally (just HTTP flow)
- Enables dynamic pricing and true pay-per-use at API granularity
- Critical for agent commerce: agents buying data, compute, and services autonomously

## Implications for Hermes/SOMA
- Could enable agent-to-agent service payments in future
- Relevant to autonomous infrastructure provisioning
- Research angle: how autonomous agents handle payment failures and budget management

## Sources
- Allium guide (Feb 2026): comprehensive technical overview
- Reddit r/ethereum: practical implementation experience with caching
- Coinbase whitepaper (May 2025)


## Sources

- https://allium.so/blog/x402-explained-the-internet-native-payments-standard-for-apis-data-and-agent-commerce/
- https://www.reddit.com/r/ethereum/comments/1r3bm1g/i_got_http_402_working_as_an_actual_payment/
