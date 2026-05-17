---
name: clinical-copilot-spark
version: 1.0.0
description: Build a HIPAA-compliant clinical copilot using DGX Spark + Qwen3.6 as local inference backend. Covers workflow automation, app architecture, time savings, and the learning loop where model improves from user corrections.
trigger: When building clinical AI tools, medical workflow automation, HIPAA-compliant local inference apps, or any app that processes patient data and needs local-only processing. Also when planning how to use a DGX Spark for medical education.
tags: [clinical-copilot, hipaa, local-inference, medical-education, workflow-automation, dgx-spark, note-generation, anki]
---

# Clinical Copilot on DGX Spark

## Core Principle

**Patient data cannot leave the building.** HIPAA means cloud APIs (ChatGPT, Claude, Gemini) are legally unusable for any tool that touches real patient data. Local inference is the ONLY way to build clinical AI tools. This is the moat.

## Architecture

```
MacBook (dev + daily driver)          DGX Spark (inference server)
  - VS Code, browser, apps             - Qwen3.6 BF16 + LoRA adapter
  - Frontend for all copilot apps      - Qdrant (RAG knowledge base)
  - USB-C to monitor                   - Clinical memory (de-identified cases)
  - WiFi to Spark API                  - Background: Anki gen, monthly LoRA, weekly reports
```

**Spark is NOT a workstation.** It's an inference appliance. 20 ARM cores, Ubuntu aarch64, no x86, one HDMI. Your MacBook is your dev machine. The Spark sits alongside connected over WiFi serving models via OpenAI-compatible API at `http://spark-ip:8000/v1`.

**Monitor setup:** MacBook to USB-C to monitor. Spark sits next to MacBook. HDMI available for Spark setup/debug but rarely needed. 95% of work is MacBook to WiFi to Spark API.

## Time Savings Map (3rd Year Clinicals)

| Task | Manual Time | With Spark | Saved/Day |
|---|---|---|---|
| Pre-rounding (chart synthesis) | 60-90 min | 5-10 min (read AI briefs) | 45-60 min |
| Note writing (2-4 SOAP notes) | 90-180 min | 30-45 min (edit AI drafts) | 60-90 min |
| Drug lookups (UpToDate/Stahl's) | 15-30 min | 5-10 min (local RAG query) | 15-20 min |
| Attending prep | 30-60 min | 5-15 min (AI anticipates questions) | 25-45 min |
| Anki card creation | 60-120 min/week | 10-20 min/week (auto-generated) | 50-100 min/week |
| Discharge summaries | 30-60 min | 10-15 min (edit AI draft) | 30-45 min |
| **TOTAL** | | | **100-150 min/day** |

2 hours/day saved x 48 weeks = 480 hours = 12 work weeks reclaimed.

## The 6 Automation Points

### 1. Pre-Rounding Intelligence Brief (5:30 AM)
- Paste overnight EMR summary (de-identified) into local app
- Spark generates per-patient brief: overnight events, lab flags, vital trends, likely attending questions
- You arrive at rounds prepared instead of scrambling through charts

### 2. Live Rounds Assistant
- Phone/iPad runs local web interface to Spark
- When attending asks question, tap it into app
- Spark returns 3-bullet answer with citation in 5 seconds
- All local, zero PHI egress

### 3. Smart Note Drafting (biggest time saver)
- After seeing patient, dictate/typate case bullets into app
- Spark generates full SOAP note draft
- You edit 2-5 lines, copy to EMR
- Example input: "67M schizoaffective, day 3, VPA subtherapeutic at 42, increased to 2000mg, added IM haloperidol for agitation, ordered ECG"
- Example output: full SOAP note with assessment/plan formatted correctly

### 4. Drug Quick-Reference
- RAG over Stahl's Psychopharmacology, APA guidelines, drug interaction DB
- Example: "VPA + lamotrigine interaction?" -> specific answer with citation
- Replaces 5-10 min UpToDate searches with 30 sec local queries

### 5. Attending Question Anticipator
- Feed case summary before presenting
- Model generates 5-8 likely questions with brief answers
- Learns your attending's patterns over time (which questions they actually ask)

### 6. Smart Anki Generation
- After each patient encounter, tell model: "make me cards about [diagnosis/med]"
- Generates Anki cards in your format, auto-imports via AnkiConnect
- Cards anchored to YOUR clinical experiences = 5x better retention
- Background process: daily auto-generation from case log

## The Learning Loop (Symbiosis)

**Month 1:** You teach it. Note drafts need 30% editing. Every correction is stored.

**Month 2:** It learns your style. Your attending's note format, your program's preferences. Drafts drop to 15% editing.

**Month 3:** It anticipates. "Your attending will ask about QTc with olanzapine + haloperidol." Patterns surfaced from your 50+ previous cases.

**Monthly:** LoRA fine-tunes overnight on accumulated corrections. 1% improvement per month, permanent. After 6 months, completely different model from day one.

**Key mechanism:** Every edit you make to a note draft = training signal. Not just using the model -- training it. The correction IS the data.

## RAG Knowledge Base (Qdrant)

Load these into your vector store:
- Stahl's Essential Psychopharmacology (chapters as documents)
- APA Practice Guidelines (depression, bipolar, schizophrenia, anxiety, substance use)
- DSM-5-TR diagnostic criteria (structured per disorder)
- Kaplan and Sadock's Synopsis of Psychiatry (key chapters)
- Drug interaction database (DDI data)
- YOUR de-identified clinical cases (accumulated over rotations)
- YOUR attending's teaching points (accumulated over rounds)

## Build Ramp (First Month of Clinicals)

**Day 1:** Spark unboxed, Qwen3.6 running, test with practice vignette
**Week 1:** Note generator -- text box on phone -> SOAP note draft. Simplest possible UI.
**Week 2:** Drug reference (load Stahl's + APA into Qdrant) + attending prep bot
**Week 3:** Anki card generation (auto background) + start collecting corrections
**Week 4:** Pre-rounding brief generator + weekly learning report (cron on Spark)
**Month 2:** Daily use established. Model improving from corrections.
**Month 3:** First overnight LoRA fine-tuning. Monday morning = slightly better model.

## SOMA Integration

The Spark becomes SOMA's clinical AI backend:
- Click amygdala -> "what happens when this is lesioned?" -> Spark answers with clinical knowledge
- Clinical scenario mode: "auditory hallucinations in schizophrenia" -> SOMA highlights superior temporal gyrus, arcuate fasciculus, thalamic radiations
- Bilingual teaching: structure -> English + Spanish clinical terms + pathology explanation
- Anki from SOMA: see structure -> "make card" -> clinical card about pathology
- Frontend is the existing Three.js app + chat/query overlay
- Backend is Spark API + anatomy knowledge base in Qdrant

## De-identification Protocol

Before ANY patient data enters the Spark:
1. Strip: patient name, MRN, DOB, specific dates, phone/fax, addresses
2. Keep: age/age range, gender, diagnosis, medications, clinical reasoning
3. Format: "67M schizoaffective" not "John Smith DOB 3/15/1958 MRN 12345"
4. Location data: replace "Building 8B" with "unit" if it could identify
5. This is minimum necessary de-identification for HIPAA safe harbor

## Weekly Learning Report (Auto, Sunday Night)

Spark generates from your accumulated data:
- Patients seen count, unique diagnoses this week
- Top medication decisions made
- Attending teaching points captured
- Weak areas (questions you got wrong or looked up)
- Anki cards generated, cards due, accuracy trends
- Shelf exam gap analysis (topics you haven't encountered)

This is a STUDY GUIDANCE system built from YOUR clinical data.

## Model Smartness: Honest Assessment

Qwen3.6-35B-A3B (35B total, 3B active) is NOT as smart as GLM-5.1 (754B total, ~20B active). The gap is real:
- Intelligence Index: ~37 vs ~51
- SWE-bench: 73.4 vs GPT-5.4 level
- Complex reasoning: meaningfully weaker

Where the Spark wins:
- HIPAA compliance (cloud can't touch clinical data at all)
- Zero marginal cost (run 24/7, no per-token billing)
- Fine-tuning (actually changes the model, not just prompt engineering)
- Domain adaptation (LoRA on your medical data -> better than GLM-5.1 at psychiatry-specific tasks)
- Future Qwen models (drop-in swap, gap narrows each release)

Smartness ladder on 128GB Spark:
1. Qwen3.6-35B-A3B BF16 -> 3B active, 40-50 tok/s (good baseline)
2. Qwen3.5-122B-A10B NVFP4 -> 10B active, 15-20 tok/s (MUCH smarter, ~65GB)
3. Future Qwen 80B+ at FP8 (when released)

## Hermes Training Loop Closure

Current (broken): Cortex captures experiences -> tips injected as context -> model SEES tips but doesn't LEARN -> same base model every turn

With Spark (complete): Cortex experiences -> LoRA fine-tune -> model actually CHANGES -> permanent improvement -> compounding at zero cost

Cortex has 7,666 experiences + 368 tips. Every node with elo > 1800 is training data. LoRA on these teaches the model permanently instead of just reminding it via context injection.

## Gotchas

1. Spark is ARM (aarch64) -- no x86 binaries, no Windows, limited software availability
2. Max seq length for LoRA training on 128GB: 2048 is safe, 4096 OOMs (MoE backward pass memory)
3. UNSLOTH_COMPILE_DISABLE=1 required for MoE LoRA (prevents dtype mismatch crashes)
4. De-identify BEFORE data enters the Spark, not after
5. Qdrant needs structured chunking for medical texts (chapter to section to paragraph, not random splits)
6. Anki card generation needs your .mobile CSS overrides (Danny likes phone font ~15px)
7. NCCL_DEBUG=INFO for dual Spark -- verify "IB" transport not "Socket" (silent fallback to TCP at 4.6x slower)
8. Don't try model merging for MoE architectures (MergeKit doesn't support it) -- use LoRA adapters instead
9. MergeKit mergekit-moe creates a NEW MoE from dense models, cannot merge two existing MoE models
10. Reference: PsychiatryBench (Nature, Apr 14 2026) -- first rigorous psychiatry LLM benchmark, shows "generalist-specialist paradox" where frontier models beat specialized medical models at reasoning
