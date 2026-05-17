# http-402-agentic-commerce

*Researched: 2026-04-11 15:37 CDT*

# HTTP 402 "Payment Required" — The Agentic Commerce Protocol

## Overview
HTTP status code 402 has been reserved since 1997 in the original web spec as a placeholder for a micropayment layer. It sat dormant for 30 years. The rise of AI agents as economic participants has finally given it purpose.

## Why Now (2026)
- AI agents need to transact autonomously in real time — buying API calls, licensing data feeds, paying for compute
- Current payment infrastructure expects human actions (CAPTCHA, checkout flows, account management)
- The web was never designed with a native payment primitive

## Two Competing Approaches

### 1. x402 (Coinbase / Blockchain)
- Open-source protocol using stablecoins on blockchain rails
- Server responds with 402 → client pays via crypto wallet → retries
- No API keys, subscriptions, or minimum transactions
- Programmable micropayments system

### 2. Card Network Incumbents
- **Mastercard Agent Pay** (April 2025): Uses "Mastercard Agentic Tokens" extending existing tokenization
- **Visa Intelligent Commerce APIs**: Users specify what agents can purchase and limits
- **Mastercard + Google "Verifiable Intent"**: Standardized trust layer with authorization records
- Compatible with Google's Universal Commerce Protocol (UCP) — open-source, 60+ partners

## Implications for Agent Development
- Agents that can handle 402 responses natively will have a competitive advantage
- Payment negotiation becomes part of the agent loop (tool call → 402 → pay → retry)
- Budget management becomes critical — agents need spend limits and approval flows
- Relevant to Hermes: could implement 402-aware API clients that auto-negotiate payments

## Key Insight
The original web architects foresaw the need for native payments but the ad-supported model delayed it. AI agents are the forcing function that finally activates HTTP 402.

## Sources
- CTSE/AEI article (March 2026)
- MDN Web Docs HTTP 402
- Coinbase x402 protocol
- Mastercard Agent Pay documentation

## Sources

- https://ctse.aei.org/402-payment-required-the-http-code-that-waited-30-years-and-why-it-matters-today/
- https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/402
