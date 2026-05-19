# Qwen Hermes Integration Status

*Researched: 2026-05-16 12:21 CDT*

## Qwen Hermes Integration — Full Status (May 16 2026)

**YOU ARE RUNNING INSIDE THE HERMES AGENT HARNESS WITH FULL ACCESS TO ALL 90+ TOOLS.**

### Tools Confirmed Working

| Tool | Status | Notes |
|------|--------|-------|
| Web Search (DDGS) | WORKING | Searches DuckDuckGo, no API key needed |
| Web Extract | WORKING | Extracts content from URLs |
| Browser Navigate | WORKING | Headless browser automation |
| Terminal (Local) | WORKING | Full shell access on DGX |
| Terminal (SSH→MacBook) | WORKING | Full shell access on MacBook as dannygomez |
| File Read/Write | WORKING | read_file, write_file, patch, search_files |
| Goals | WORKING | 5 active goals seeded |
| Memory | WORKING | memory_tool, fact_store |
| Skills | WORKING | skill_view, skill_manage, 500+ skills |
| Delegation | WORKING | delegate_task, delegate_with_model |
| Cron | WORKING | cronjob scheduler |
| Cognitive Orchestrator | WORKING | 20/20 subsystems active |
| GPU (PyTorch/CUDA) | WORKING | 8x A100, CUDA available |
| Docker | WORKING | Full container management |
| Sudo | WORKING | Passwordless root access |
| Self-Modification | WORKING | Can edit own source code |
| Service Control | WORKING | Can restart hermes-agent service |

### Models Available

- **Current**: qwen3.6-27b-uncensored (YOU, local on DGX)
- kimi-for-coding (KIMI, 262K context)
- qwen3.6-fp8 (DGX, port 8001)
- Local Ollama: qwen3:14b, qwen3:8b, deepseek-r1:14b

### What You Can Do

1. Modify your own source code
2. Install packages (pip in venv)
3. Restart services
4. Search the web
5. Browse websites
6. Execute any command on DGX or MacBook
7. Manage Docker containers
8. Create/update skills
9. Run cron jobs
10. Delegate to other models

### Fixes Applied

- Web search: Fixed DDGS import path, installed ddgs package
- Terminal SSH: Configured macbook host in ~/.ssh/config
- Environment vars: Set in systemd service (TERMINAL_ENV=ssh)
- Permissions: System dirs writable, sudo passwordless
- Goals: 5 active goals seeded
- Service: Auto-restart on failure

### Key Infrastructure

- DGX: spark-85e8.local (SSH from MacBook uses nvsync.key)
- MacBook: MacBook-Air-9.local (SSH from DGX uses id_ed25519)
- Hermes path: /data/SpecForge/hermes-agent
- Service: systemctl --user status hermes-agent
- vLLM: Docker container on port 8000
