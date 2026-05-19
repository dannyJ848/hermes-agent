# Dataset Consolidation for Tiered Training (May 13, 2026)

## Overview

When training on tiered datasets (reasoning, health, code, etc.), raw data comes in many formats. Before PEFT/LoRA training, all datasets must be consolidated into a single format: JSONL files with `{"input": "...", "output": "..."}` records.

## Raw Dataset Formats Encountered

### Tier 1: Reasoning (Already Correct Format)
- **Format:** JSONL with `{"input": "...", "output": "..."}`
- **Size:** 2.15M records, 29GB typical
- **Action:** Use directly — no conversion needed

### Tier 2: Mixed Domain (Structured Formats)
- **Format variants:**
  - `messages` array (OpenAI chat format): `[{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]`
  - `tool_calls` format with function calling
  - `conversations` array with turns
  - Flat `instruction`/`response` pairs
- **Size:** 130K+ records, 79MB-177GB
- **Action:** Parse structured formats, extract user/assistant turns into input/output

### Tier 3: Health / Synthea (Structured Medical Records)
- **Format:** Parquet tables — NOT conversational
  - `patients.parquet`: demographics, birth date, gender
  - `conditions.parquet`: diagnoses with SNOMED-CT codes, onset dates
  - `encounters.parquet`: visit types, dates, procedures
  - `medications.parquet`: prescriptions, start/stop dates
  - `careplans.parquet`: treatment plans
- **Size:** 575K patients, 56M conditions, 134GB+ raw
- **Action:** Generate synthetic instruction-response pairs using medical templates

## Consolidation Script Pattern

### For Tier 1 (Direct Use)
```python
# Already in correct format — just verify
import json
with open("tier1-reasoning.jsonl") as f:
    sample = json.loads(f.readline())
    assert "input" in sample and "output" in sample
```

### For Tier 2 (Parse Messages Array)
```python
import json

def convert_messages_to_input_output(record):
    """Convert OpenAI messages format to input/output."""
    messages = record.get("messages", [])
    if len(messages) >= 2:
        # Find first user message and first assistant response
        user_msg = next((m["content"] for m in messages if m["role"] == "user"), "")
        assistant_msg = next((m["content"] for m in messages if m["role"] == "assistant"), "")
        return {"input": user_msg, "output": assistant_msg}
    return None
```

### For Tier 3 (Synthea Medical Records)

**Key insight:** Synthea data is structured EMR data, not conversational. You must generate synthetic clinical scenarios.

```python
import pyarrow.parquet as pq
import pandas as pd
import random

def generate_patient_summary(patient, conditions, medications, encounters):
    """Generate a clinical summary instruction-response pair."""
    input_text = f"""Generate a clinical summary for the following patient:

Patient: {patient.get('FIRST', '')} {patient.get('LAST', '')}
Gender: {patient.get('GENDER', 'Unknown')}
Birth Date: {patient.get('BIRTHDATE', 'Unknown')}
"""
    if len(conditions) > 0:
        input_text += "\nConditions:\n"
        for _, cond in conditions.head(10).iterrows():
            input_text += f"- {cond['DESCRIPTION']} (onset: {cond['START']})\n"

    # ... generate output_text with structured clinical summary ...
    return input_text, output_text

def generate_condition_qa(condition, patient):
    """Generate Q&A about a specific condition."""
    input_text = f"What is {condition['DESCRIPTION']} and how should it be managed?"
    output_text = f"# {condition['DESCRIPTION']}\n\n## Overview\n{condition['DESCRIPTION']} is a documented medical condition..."
    return input_text, output_text

def generate_encounter_summary(encounter, patient, conditions_during_encounter):
    """Generate a clinical encounter note."""
    input_text = f"Write a clinical encounter note for: {encounter.get('DESCRIPTION', 'Unknown')} on {encounter.get('START', 'Unknown')[:10]}"
    output_text = f"# Encounter Note\n\n## Visit Information\n..."
    return input_text, output_text
```

**Processing pattern for Synthea:**
1. Load all parquet tables into pandas DataFrames
2. Sample patients (e.g., 50K out of 575K — full dataset is too large)
3. For each sampled patient, look up their conditions, medications, encounters
4. Randomly select template type (summary, Q&A, encounter note)
5. Generate 1-3 examples per patient
6. Write to JSONL

**Performance note:** Synthea processing is VERY SLOW. 575K patients × 56M conditions = massive joins. Expect hours for even 50K sampled patients. Consider:
- Sampling fewer patients (10K-20K)
- Pre-filtering patients with interesting conditions (not just "Medication review due")
- Running overnight

## Dataset Size Targets

| Tier | Records | Size | Training Value |
|------|---------|------|----------------|
| tier1-reasoning | 2.15M | 29GB | Primary — high-quality reasoning |
| tier2-reasoning | 130K | 79MB | Secondary — mixed domain |
| tier3-health | 50K-100K | ~50MB | Niche — medical reasoning |

**Minimum viable:** tier1 alone (2.15M records) is sufficient for effective LoRA training.
**Optimal:** tier1 + tier2 (2.29M records) — good diversity without health data complexity.
**Full:** tier1 + tier2 + tier3 (~2.35M records) — maximum diversity but health data requires significant preprocessing.

## Verification

After consolidation, verify:
```bash
# Count records
wc -l /data/SpecForge/custom_dflash/datasets/*.jsonl

# Check format
head -1 /data/SpecForge/custom_dflash/datasets/tier1-reasoning.jsonl | python3 -m json.tool

# Verify keys present
python3 -c "
import json
with open('tier1-reasoning.jsonl') as f:
    r = json.loads(f.readline())
    assert 'input' in r and 'output' in r, 'Missing keys!'
    print(f'Input length: {len(r[\"input\"])} chars')
    print(f'Output length: {len(r[\"output\"])} chars')
"
```

## Common Pitfalls

- **Missing `input`/`output` keys:** Some datasets use `instruction`/`response` or `messages` — standardize to `input`/`output`
- **Empty outputs:** Filter out records where output is empty or just whitespace
- **NaN values in Synthea:** Parquet nulls become `nan` strings — handle with `pd.isna()` or `str(val) == "nan"`
- **Memory exhaustion:** Don't load entire Synthea dataset into memory — use sampling and chunked processing
- **Format mismatch:** PEFT/LoRA training expects flat text, not nested structures — flatten before tokenization
