# Session-to-Training-Data Pipeline

**Date:** May 14, 2026
**Context:** Built automated pipeline to convert Hermes CLI sessions into training data for continuous Qwen 27B model improvement.

## Problem

Hermes sessions were stored in `~/.hermes/sessions/` as JSON files but there was no automatic export to training format. High-quality conversations with successful tool use, reasoning, and task completion were being lost instead of fed back into model training.

## Solution

Built 5-component pipeline:

### 1. Session Exporter (`export_sessions_to_training.py`)

**Location:** `/data/SpecForge/hermes-agent/scripts/export_sessions_to_training.py`

**Quality Scoring (5 dimensions):**
- `completion_rate` (25%): Did session end with assistant message vs error/crash?
- `tool_success_rate` (25%): % of tool calls that succeeded
- `reasoning_depth` (20%): Presence of `<think>` tags or reasoning content
- `task_complexity` (15%): Number of tool calls (more = complex)
- `user_satisfaction` (15%): No clarify calls needed

**Output Format (ShareGPT):**
```json
{
  "messages": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ],
  "source": "hermes_session",
  "quality_score": 0.85,
  "session_id": "20260514_103756_6aa112"
}
```

**Usage:**
```bash
python3 scripts/export_sessions_to_training.py --min-quality 0.7 --max-sessions 1000
```

### 2. Live Learning Loop (`live_learning_loop.py`)

**Location:** `/data/SpecForge/hermes-agent/scripts/live_learning_loop.py`

**Features:**
- SQLite database (`~/.hermes/live_learning.db`) tracks all processed sessions
- Auto-grades trajectories on 5 dimensions
- Adds high-quality sessions (score >= 0.7) to training buffer
- Prevents duplicate processing via session_id check
- Tracks aggregate stats: total sessions, high-quality rate, avg quality

**Database Schema:**
```sql
CREATE TABLE trajectories (
    id INTEGER PRIMARY KEY,
    session_id TEXT NOT NULL,
    quality_score REAL DEFAULT 0.0,
    added_to_buffer BOOLEAN DEFAULT 0,
    -- ... metrics
);

CREATE TABLE learning_stats (
    total_sessions INTEGER DEFAULT 0,
    high_quality_sessions INTEGER DEFAULT 0,
    avg_quality REAL DEFAULT 0.0
);
```

**Usage:**
```bash
python3 scripts/live_learning_loop.py
```

### 3. Auto-Training Trigger (`auto_training_trigger.py`)

**Location:** `/data/SpecForge/hermes-agent/scripts/auto_training_trigger.py`

**Logic:**
- Counts total sessions in training buffer
- Compares to last known count (stored in `.training_state.json`)
- Triggers training when 100+ new sessions accumulated
- Runs training script in background with nohup

**State File:** `/data/SpecForge/custom_dflash/.training_state.json`
```json
{
  "last_session_count": 500,
  "last_training": "2026-05-14T12:00:00",
  "total_trainings": 3,
  "last_pid": 12345
}
```

### 4. A/B Testing Framework (`ab_test_models.py`)

**Location:** `/data/SpecForge/hermes-agent/scripts/ab_test_models.py`

**Benchmark Tasks:**
- `code_debug`: Debug Python function with TypeError
- `reasoning`: Classic widget-making logic puzzle
- `tool_use`: List files and count them

**Scoring:**
- Checks if expected keywords appear in response
- Score = found_keywords / total_expected
- Measures latency per task

**Usage:**
```bash
python3 scripts/ab_test_models.py --model-a merged-lora --model-b base-model
```

### 5. Orchestrator (`training_orchestrator.py`)

**Location:** `/data/SpecForge/hermes-agent/scripts/training_orchestrator.py`

**Modes:**
- `full`: Run complete pipeline (export → learn → train → eval)
- `export`: Just export sessions
- `learn`: Just run live learning
- `train`: Just trigger training
- `eval`: Just run A/B test

**Usage:**
```bash
python3 scripts/training_orchestrator.py --mode full
```

## Shell Escaping Pitfall

When creating Python scripts via SSH, inline heredocs and f-strings with newlines cause unterminated string literal errors. The shell interprets `\n` and quote characters.

**Failed approaches (5+ attempts):**
- `ssh host "cat > file.py << 'EOF'...EOF"` — heredoc expands locally
- `ssh host "python3 -c '...'"` — f-string quoting breaks
- `execute_code` with triple-quoted strings — sandbox SyntaxError on special chars

**Working approach:**
```python
# Use base64 encoding to avoid ALL escaping
import base64
script = b"#!/usr/bin/env python3\nprint('hello')"
encoded = base64.b64encode(script).decode()
# On remote: echo <encoded> | base64 -d > file.py
```

## Integration with Training Pipeline

The exported training data feeds into the existing 3-tier training system:

```
Hermes Sessions → Live Learning Loop → hermes_sessions/*.jsonl
                                      ↓
                              ConcatDataset (repeated for weighting)
                                      ↓
                              train_qwen_all_tiers.py
                                      ↓
                              New LoRA Adapter → vLLM reload
```

**Data format compatibility:** ShareGPT format matches what `train_qwen_all_tiers.py` expects for Tier 2 (raw chat conversations).

## Files on DGX

| File | Purpose |
|------|---------|
| `/data/SpecForge/hermes-agent/scripts/export_sessions_to_training.py` | Export sessions to training data |
| `/data/SpecForge/hermes-agent/scripts/live_learning_loop.py` | Auto-grade and buffer sessions |
| `/data/SpecForge/hermes-agent/scripts/auto_training_trigger.py` | Trigger training when buffer fills |
| `/data/SpecForge/hermes-agent/scripts/ab_test_models.py` | A/B test models |
| `/data/SpecForge/hermes-agent/scripts/training_orchestrator.py` | Master orchestrator |
| `/data/SpecForge/custom_dflash/datasets/hermes_sessions/` | Training buffer directory |
| `~/.hermes/live_learning.db` | SQLite tracking database |

## Next Steps

1. Fix shell escaping in scripts (use base64 approach)
2. Test exporter with actual session files
3. Verify training data format matches `train_qwen_all_tiers.py` expectations
4. Set up cron job to run live learning loop periodically
5. Integrate auto-training trigger with systemd
