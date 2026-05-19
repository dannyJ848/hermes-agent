# distillation-recovery-tip-cleanup

*Researched: 2026-04-08 11:05 CDT*

# Distillation Recovery Tip Cleanup (Apr 8, 2026)

## Problem
The `recovery` tip type had 32% survival rate — worst of all types. Root cause: 45 of 70 tips were near-identical generic templates: "Check error message for root cause. Common fix: verify inputs, check permissions, retry with backoff..." These were produced by the auto-distillation pipeline when it encountered tool errors but couldn't extract specific recovery knowledge.

## Fix
Deleted all tips matching `tip_type='recovery' AND confidence=0.5 AND recommendation LIKE '%verify inputs, check permissions%'`. 

## Result
- Recovery survival rate: 32% → 88% (22/25 ≥ 0.6 confidence)
- Total tips: 951 → 906
- High-confidence tips: 896/906 (98.9%)

## Root Cause
The distillation extractor falls back to generic advice when error context is insufficient. Fix options:
1. Require error-specific keywords in recovery tips (reject "verify inputs, check permissions" as too generic)
2. Raise confidence floor for recovery type to 0.6 (auto-reject 0.5 tips)
3. Add deduplication during extraction (check for similar conditions)
