# Context Gauge → Handoff → Resume Flow

## The Complete Loop

```
[Session Running]
    ↓
[Context Compression #1-4] — Normal, LCM handles it
    ↓
[Context Compression #5] — CRITICAL THRESHOLD
    ↓
[hermes_self_manager.py --handoff]
    ├── full_checkpoint(label)
    ├── distill_all_context()
    │   ├── knowledge doc: ~/.hermes/knowledge/session-handoff-<ts>.md
    │   ├── rapid learning: "Resume from checkpoint <label>"
    │   └── handoff file: ~/.hermes/workspace/handoff_pending.json
    └── generate_resume_script(label)
    ↓
[User opens new terminal]
    ↓
[hermes_cli_resume.py auto_resume()]
    ├── detects handoff_pending.json
    ├── prints resume summary
    └── shows: "Resume from checkpoint <label>"
    ↓
[User says: "resume from checkpoint <label>"]
    ↓
[Full context restored — session continues]
```

## Key Files

| File | Purpose |
|------|---------|
| `~/subconscious/hermes_self_manager.py` | Orchestrates handoff |
| `~/subconscious/hermes_cli_resume.py` | Detects and displays handoff |
| `~/.hermes/workspace/handoff_pending.json` | Handoff state between sessions |
| `~/.hermes/workspace/checkpoints/auto-handoff-*.json` | Full checkpoints |
| `~/.hermes/workspace/auto_resume.sh` | Generated resume script |
| `~/.hermes/knowledge/session-handoff-*.md` | Human-readable handoff docs |

## Critical Implementation Detail

The self-manager CANNOT spawn a new terminal on macOS (security restriction). Instead:

1. Generate `auto_resume.sh` with explicit instructions
2. Print clear message: "Open new terminal, run hermes, say 'resume from checkpoint X'"
3. Save handoff file that `hermes_cli_resume.py` detects on startup

## Compression Tracking

Compressions logged to `~/.hermes/workspace/compression_log.jsonl`:
```json
{"timestamp": 1778364076, "event": "compression", "session_id": "..."}
```

Threshold: 5 compressions triggers auto-handoff.
