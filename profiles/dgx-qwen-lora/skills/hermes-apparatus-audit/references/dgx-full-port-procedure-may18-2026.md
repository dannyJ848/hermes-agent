# DGX Full Port Procedure — May 18, 2026

## Context
Port the entire monolithic Hermes cognitive apparatus from MacBook to DGX Spark.

## Prerequisites
- DGX has git clone at `/data/SpecForge/hermes-agent`
- DGX has Python 3.12.3 (externally managed — must use venv)
- MacBook has working hermes-agent at commit 7f6281ca9

## Procedure

### 1. Update DGX to Latest Commit
```bash
ssh djg6228@spark-85e8.local
cd /data/SpecForge/hermes-agent
git pull origin main
```

### 2. Create Python Venv
```bash
cd /data/SpecForge/hermes-agent
python3 -m venv venv
venv/bin/pip install -e .
```

### 3. Copy Configuration from MacBook
```bash
# On MacBook:
scp ~/.hermes/config.yaml djg6228@spark-85e8.local:~/.hermes/
scp ~/.hermes/.env djg6228@spark-85e8.local:~/.hermes/
```

### 4. Sync Skills
```bash
# On MacBook:
rsync -av ~/.hermes/skills/ djg6228@spark-85e8.local:~/.hermes/skills/
```

### 5. Create Symlink
```bash
# On DGX:
mkdir -p ~/.local/bin
ln -sf /data/SpecForge/hermes-agent/venv/bin/hermes ~/.local/bin/hermes
```

### 6. Verify
```bash
hermes doctor
hermes skills list | wc -l
```

## Key Differences
| | MacBook | DGX |
|--|---------|-----|
| Python | 3.10.0 (system) | 3.12.3 (venv) |
| Skills | 384 | 385 |
| Tools | ~27 | ~50 (evey suite active) |
| Entry point | `hermes` | `/data/SpecForge/hermes-agent/venv/bin/hermes` |

## Troubleshooting
- If `hermes` not found: `export PATH=/data/SpecForge/hermes-agent/venv/bin:$PATH`
- If skills missing: re-run rsync, check `~/.hermes/skills/` exists
- If tools disabled: check API keys in `~/.hermes/.env`

## Verification Script
See `scripts/verify_dgx_port.py` for automated verification.
