---
name: capability-suite
version: 2.0
created: 2026-04-04
updated: 2026-04-04
description: 195 unified capabilities across 13 domains. Master registry at ~/subconscious/capability_registry.py routes any request to the correct subprocess script. Includes medical dosage, perception, communications, integration, and creative tools.
---

# Capability Suite v2 — The Limitless Edition

## Architecture
All capabilities live in `~/subconscious/capabilities/` as standalone Python scripts:

### Wave 1 (102 caps) — Core
- `desktop_control.py` — 20 caps (mouse, keyboard, apps, windows, clipboard, OCR, screenshots)
- `image_tool.py` — 10 caps (crop, resize, filter, annotate, composite)
- `audio_tool.py` — 12 caps (record, convert, trim, transcribe, TTS, play)
- `video_tool.py` — 10 caps (trim, concat, frames, convert, gif, speed)
- `pdf_tool.py` — 8 caps (create, merge, split, extract, encrypt)
- `qr_tool.py` — 4 caps (generate, read, wifi, screen scan)
- `apple_control.py` — 14 caps (Messages, Calendar, Reminders, Notes, Contacts, System)
- `data_tool.py` — 12 caps (spreadsheet, math, units, translate, RSS, DB, text)
- `sys_tool.py` — 12 caps (file watch, processes, network, Docker, backup)

### Wave 2 (93 caps) — Expansion
- `perception_tool.py` — 16 caps (color picker, screen diff/monitor, GPS, ambient sound, table/chart/handwriting/font analysis, OCR stream, screen find text, barcode scan, document scan)
- `comm_tool.py` — 18 caps (email via himalaya, FaceTime audio/video, AirDrop, Bluetooth, WiFi, VPN, printing, webhooks)
- `cognition_tool.py` — 17 caps (descriptive stats, correlation, t-test, sentiment, NER, molar mass, dilution, dosage weight/BSA/pediatric, CrCl, BMI, currency, timezone, diagram, code count)
- `integration_tool.py` — 26 caps (SSH exec/upload/download/tunnel, WebSocket send/listen, API health check, S3 upload/download/list, Keychain secrets, SSL certs, DNS lookup/reverse, GitHub Actions, database query, ports, ping, traceroute, port scan, speed test)
- `creative_tool.py` — 16 caps (tone/melody/chord synthesis, ASCII art/fonts/cowsay, PlantUML/Graphviz diagrams, ASCII flowchart, markdown to HTML/PDF, presentations, GIF creation, video from images, pattern images, image composite, color themes)

## Master Registry
`~/subconscious/capability_registry.py` — unified routing for all 195 caps. Usage:

```bash
# Search for relevant capabilities
python3 ~/subconscious/capability_registry.py search <query>

# Execute a capability
python3 ~/subconscious/capability_registry.py run <cap_id> [args]

# List all capabilities grouped by category
python3 ~/subconscious/capability_registry.py list

# Full system health check (tests all 14 scripts)
python3 ~/subconscious/capability_registry.py status
```

## Medical Capabilities (SOMA-relevant)
Key clinical calculators in `cognition_tool.py`:
- **BMI**: `python3 cognition_tool.py bmi 70 175`
- **CrCl** (Cockcroft-Gault): `python3 cognition_tool.py crcl 45 80 1.2 male`
- **BSA** (Mosteller): `python3 cognition_tool.py dose_bsa 70 175 50`
- **Pediatric dosing** (Clark's + Young's): `python3 cognition_tool.py dose_pediatric 15 24 500`
- **Weight-based dosing**: `python3 cognition_tool.py dose_weight 70 5 2`
- **Molar mass**: `python3 cognition_tool.py molar_mass C6H12O6`
- **Dilution** (C1V1=C2V2): `python3 cognition_tool.py dilution 10 100 5`

## Dependencies
- cliclick, tesseract, fswatch, blueutil (brew)
- Pillow, PyPDF2, fpdf2, openpyxl, sympy, pint, pyzbar, qrcode, deep-translator, feedparser, textblob, pyfiglet, cowsay (pip)

## Brain Integration
- `parallel_brain.py` perceive() phase loads capability_status (195 caps across 13 domains)
- Integrated into the PERCEIVE → THINK → ACT pipeline

## Key Patterns
- Each script is CLI-first: `python3 <script>.py <command> [args]`
- Every call returns JSON: `{"status": "success|error", ...}`
- The registry handles routing; scripts don't import each other
- Always use `/Users/dannygomez/hermes-agent/venv/bin/python3` (not system python 3.8)

## Pitfalls
- **Registry BASE path**: The registry lives at `~/subconscious/capability_registry.py` but scripts are in `~/subconscious/capabilities/`. The `BASE` variable must point to `Path(__file__).parent / "capabilities"`, not just `Path(__file__).parent`.
- **CLI argument parsing**: Some tools expect space-separated args, some comma-separated. Always handle both by doing `args = sys.argv[x].replace(",", " ").split()` for multi-arg commands.
- **pip binary**: venv has `pip3` not `pip`. Always use `/Users/dannygomez/hermes-agent/venv/bin/pip3`
- **eval() namespace**: When using `eval()` for math expressions, import `math as _math` and include both the module object AND its individual functions in the allowed dict.
- **f-strings in terminal()**: Avoid f-strings with braces in terminal() calls — use standalone scripts for complex logic.
- **Delegation fallback**: llama70b-free may fail with HTTP 400. delegate_parallel auto-falls back to glm-5.1, adding latency. For research, prefer direct web_research + web_extract.
- **Adding new capabilities**: When adding a new script, it must be added to the `CAPABILITIES` dict in `capability_registry.py` AND the script must handle a bare `help` command (the status check calls each script with `help`).
