# nabaos-epistemic-verification-hallucination-detection

*Researched: 2026-04-05 06:34 CDT*

# NabaOS: Epistemic Verification via Tool Receipts (arXiv 2603.10060, Mar 2026)

## Summary
NabaOS is a lightweight verification framework for AI agents that detects hallucinated tool calls and fabricated results in real time using HMAC-signed "tool execution receipts" rather than expensive zero-knowledge proofs. Inspired by Indian Nyāya Śāstra epistemology.

## Key Innovation: Pramāṇa Classification
Every claim in an LLM response is classified by epistemic source:
- **Pratyakṣa** (direct perception): Claims grounded in actual tool output
- **Anumāna** (inference): Claims derived by reasoning from tool data
- **Śabda** (testimony): Claims from external sources (APIs, documents)
- **Abhāva** (absence): Claims about what was NOT found
- **Ungrounded**: Claims with no tool backing (opinion/hallucination)

## Technical Architecture
1. Runtime generates HMAC-signed tool execution receipts the LLM cannot forge
2. Cross-references LLM claims against receipts in real time
3. Verification overhead: <15ms per response
4. Deep agent delegation: independent re-fetching catches 78.4% URL fabrications

## Results on NyayaVerifyBench (1,800 scenarios, 4 languages)
- 94.2% detection of fabricated tool references
- 87.6% detection of count misstatements
- 91.3% detection of false absence claims
- Multilingual coverage (4 languages tested)

## Relevance to Cerebrum/Evey
This directly maps to our **epistemic trust scoring** system:
- Our F-G-R Trust Tuple (Formation, Grounding, Recency) parallels NabaOS's pramāṇa classification
- HMAC receipts ≈ our tool call logging in cerebrum_memory.db
- The "self-tagging prompt" approach (LLM tags its own claims) could enhance our pre-action recall
- Multi-step agent cross-checking is directly applicable to our delegation validation pipeline

## Practical Takeaways
1. Receipt-based verification is more practical than ZK proofs for interactive agents (<15ms vs minutes)
2. Epistemic classification gives granular trust signals instead of binary verified/unverified
3. Independent re-fetching for delegated tasks catches most fabrications
4. Count misstatements (87.6% caught) are the hardest category — relevant for our tool intelligence stats


## Sources

- https://arxiv.org/abs/2603.10060
- https://arxiv.org/html/2603.10060v1
