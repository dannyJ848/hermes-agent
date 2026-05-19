---
name: hybrid-inference-bridge
version: 1.0
created: 2026-04-10
description: Set up local LLM inference servers (llama.cpp) on Mac, bridge them to a remote Hermes agent via SSH reverse tunnel. Enables hybrid "brain + reflexes" architecture where expensive reasoning runs on API but quality scoring/classification/embeddings run locally for free.
tags: [inference, llama-cpp, tunnel, launchd, embedding, hybrid-architecture]
---

# Hybrid Inference Bridge

Connects local Mac inference servers to a remote Hermes VPS instance via SSH reverse tunnel. The remote agent can call local models for tip scoring, reward judging, and embedding search — all for free, without burning API credits.

## Architecture

```
Hostinger VPS (brain)          Mac M2 Air (reflexes)
┌──────────────────┐           ┌──────────────────┐
│  Hermes Agent    │           │  Phi-3 (8081)    │
│  GLM-5.1 API     │◄──SSH────│  Llama 8B (8082) │
│                  │  reverse  │  nomic-embed      │
│  cron jobs       │  tunnel   │  (8083)          │
│  distillation    │           │                  │
└──────────────────┘           └──────────────────┘
```

## Prerequisites

- Mac with Apple Silicon (M1/M2/M3) and 16GB+ RAM
- llama.cpp built with Metal support (`cmake -DGGML_METAL=ON`)
- GGUF models downloaded to `~/llama.cpp/models/`
- Remote server with SSH access

## Step 1: Build llama.cpp with Metal

```bash
cd ~/llama.cpp
cmake -B build -DGGML_METAL=ON
cmake --build build --config Release -j$(sysctl -n hw.ncpu)
```

Verify: `ls ~/llama.cpp/build/bin/llama-server` should exist.

## Step 2: Download Models

Recommended models for agent reflexes:

| Model | File | Size | Port | Use Case |
|-------|------|------|------|----------|
| Phi-3 Mini 3.8B Q4_K_M | `phi-3-mini-q4km.gguf` | ~2.2GB | 8081 | Fast classification, tip scoring |
| Llama 3.1 8B Q4_K_M | `llama-3.1-8b-q4km.gguf` | ~4.6GB | 8082 | Reward judging, deep evaluation |
| nomic-embed-text v1.5 Q4_K_M | `nomic-embed-text.gguf` | ~80MB | 8083 | 768-dim embeddings, semantic search |

Download from HuggingFace (bartowski quantizations):
```bash
mkdir -p ~/llama.cpp/models
cd ~/llama.cpp/models
# Download all three in parallel
curl -L -o phi-3-mini-q4km.gguf "https://huggingface.co/bartowski/Phi-3-mini-4k-instruct-GGUF/resolve/main/Phi-3-mini-4k-instruct-Q4_K_M.gguf" &
curl -L -o llama-3.1-8b-q4km.gguf "https://huggingface.co/bartowski/Meta-Llama-3.1-8B-Instruct-GGUF/resolve/main/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf" &
curl -L -o nomic-embed-text.gguf "https://huggingface.co/nomic-ai/nomic-embed-text-v1.5-GGUF/resolve/main/nomic-embed-text-v1.5.Q4_K_M.gguf" &
wait
```

## Step 3: Create launchd Services

Create a plist for each model in `~/Library/LaunchAgents/`:

**com.llama.phi3.plist** (port 8081):
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.llama.phi3</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/YOURUSER/llama.cpp/build/bin/llama-server</string>
        <string>-m</string>
        <string>/Users/YOURUSER/llama.cpp/models/phi-3-mini-q4km.gguf</string>
        <string>--port</string>
        <string>8081</string>
        <string>--host</string>
        <string>127.0.0.1</string>
        <string>-ngl</string>
        <string>99</string>
        <string>-c</string>
        <string>8192</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/llama-phi3.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/llama-phi3-err.log</string>
</dict>
</plist>
</plist>
```

**com.llama.8b.plist** (port 8082) — same pattern, change port and model path.

**com.llama.embedding.plist** (port 8083) — add `--embedding` flag and use `-c 512`:
```xml
    <string>--port</string>
    <string>8083</string>
    ...
    <string>-c</string>
    <string>512</string>
    <string>--embedding</string>
```

Load all services:
```bash
launchctl load ~/Library/LaunchAgents/com.llama.phi3.plist
launchctl load ~/Library/LaunchAgents/com.llama.8b.plist
launchctl load ~/Library/LaunchAgents/com.llama.embedding.plist
```

Verify: `curl http://127.0.0.1:8081/health` → `{"status":"ok"}`

## Step 4: SSH Reverse Tunnel

Create `~/Library/LaunchAgents/com.hermes.inference-tunnel.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.hermes.inference-tunnel</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/ssh</string>
        <string>-N</string>
        <string>-R</string>
        <string>8081:127.0.0.1:8081</string>
        <string>-R</string>
        <string>8082:127.0.0.1:8082</string>
        <string>-R</string>
        <string>8083:127.0.0.1:8083</string>
        <string>-o</string>
        <string>ServerAliveInterval=30</string>
        <string>-o</string>
        <string>ServerAliveCountMax=5</string>
        <string>-o</string>
        <string>ExitOnForwardFailure=yes</string>
        <string>-o</string>
        <string>StrictHostKeyChecking=no</string>
        <string>root@YOUR_SERVER_IP</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/hermes-tunnel.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/hermes-tunnel-err.log</string>
</dict>
</plist>
```

On the server, enable port forwarding in sshd:
```bash
# On remote server
grep -q "GatewayPorts" /etc/ssh/sshd_config || echo "GatewayPorts clientspecified" >> /etc/ssh/sshd_config
systemctl restart ssh  # Ubuntu uses 'ssh' not 'sshd'
```

Load the tunnel: `launchctl load ~/Library/LaunchAgents/com.hermes.inference-tunnel.plist`

## Step 5: Python Client (local_inference.py)

Save to `~/subconscious/local_inference.py`. Key functions:

```python
PHI3_URL = "http://127.0.0.1:8081"
LLAMA8B_URL = "http://127.0.0.1:8082"
EMBED_URL = "http://127.0.0.1:8083"

def classify(prompt, max_tokens=10) -> str:
    """Fast classification via Phi-3"""
    # Uses /v1/chat/completions

def score_tip(tip_text) -> dict:
    """Score tip quality 1-10 via Phi-3"""
    # Returns {"score": N, "raw": "N"}

def judge_outcome(task, result) -> dict:
    """Judge task outcome quality via Llama 8B"""
    # Returns {"judgment": text, "tok_per_sec": N}

def generate_embedding(text) -> list[float]:
    """768-dim embedding via nomic-embed"""
    # Uses /v1/embeddings with {"input": text, "model": "embedding"}

def cosine_similarity(a, b) -> float:
    """Cosine similarity between two embedding vectors"""

def semantic_search(query, candidates, top_k=5) -> list[tuple]:
    """Rank candidates by semantic similarity"""
    # Returns [(index, text, score), ...]
```

## Pitfalls & Gotchas

### Embedding API format
llama.cpp embedding server uses the **OpenAI-compatible** endpoint:
- CORRECT: `POST /v1/embeddings` with `{"input": text, "model": "embedding"}`
- WRONG: `POST /embedding` with `{"content": text}`
- Response: `{"data": [{"embedding": [...]}]}` — access via `result["data"][0]["embedding"]`

### Nested quoting via SSH
Running inline Python via `ssh server 'python3 -c "..."'` breaks with nested quotes.
**Solution**: Write script to `/tmp/`, `scp` it to server, then `ssh server 'python3 /tmp/script.py'`.

### Ubuntu sshd restart
Ubuntu 24.04 uses `systemctl restart ssh`, NOT `systemctl restart sshd`.

### Embedding server context size
Use `-c 512` for embedding server (not 2048) — embeddings are short texts, smaller context = faster.

### llama-server FIRST LOAD hangs with -ngl 99
On first launch, `llama-server` with `-ngl 99` (offload all layers to GPU) can hang for 5+ minutes during Metal shader compilation. The process appears dead but is actually compiling Metal kernels.
- **Symptom**: No output, no health response, terminal timeout after 2620+ seconds
- **Fix 1**: Use `-ngl 1` for first test to verify the model loads at all, then increase
- **Fix 2**: Wait longer — Metal shader cache builds once, subsequent loads are fast
- **Fix 3**: Run `llama-cli` first (not server) with a short prompt to warm the Metal cache:
  ```bash
  timeout 120 ~/llama.cpp/build/bin/llama-cli -m MODEL.gguf -p "hello" -n 5 -ngl 1 --temp 0.1
  ```
  Then launch llama-server with full `-ngl 99`
- **Fix 4**: Use a reasonable middle ground: `-ngl 33` for Phi-3 (has 33 layers), `-ngl 32` for Llama 8B

### cmake build flags for Metal (updated 2026-04)
llama.cpp moved from `make` to `cmake` only. The correct build:
```bash
cd ~/llama.cpp
cmake -B build -DGGML_METAL=ON -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release -j$(sysctl -n hw.ncpu)
```
Old `make` commands will fail. Metal is auto-detected on Apple Silicon but `-DGGML_METAL=ON` makes it explicit.

### Model download verification
After downloading GGUF files, verify integrity:
```bash
ls -lh ~/llama.cpp/models/
# Expected sizes (approximate):
# phi-3-mini-q4km.gguf: ~2.2GB
# llama-3.1-8b-q4km.gguf: ~4.6GB
# nomic-embed-text.gguf: ~80MB (Q4_K_M) or ~274MB (Q5_K_M)
```
If a file is much smaller than expected, the download was interrupted. Re-download.

### Server must allow forwarding
Without `GatewayPorts clientspecified` in sshd_config on the server, the reverse tunnel binds fail silently.

## Verification Checklist

Run this from the REMOTE SERVER to verify everything:
```bash
# All three models healthy?
curl http://127.0.0.1:8081/health  # Phi-3
curl http://127.0.0.1:8082/health  # Llama 8B
curl http://127.0.0.1:8083/health  # Embedding

# Can the server actually run inference through the tunnel?
curl -s -X POST http://127.0.0.1:8081/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"phi-3","messages":[{"role":"user","content":"Say YES if you can hear me."}],"max_tokens":5}'
# Should return "Yes" with timing info
```

Expected throughput on M2 Air 24GB (benchmarked 2026-04-11, optimized context):
- Phi-3 (ctx=1024): 33 tok/s, 2.4s for classification tasks
- Llama 8B (ctx=2048): 17.5 tok/s, 4.0s for scoring tasks
- nomic-embed (ctx=512): 0.08s latency, 768-dim vectors
- MiniMax M2.7 (API): ~12s/call including reasoning phase

NOTE: With 4+ Hermes instances + other processes running, swap usage is the bottleneck.
Check with `sysctl vm.swapusage`. If swap > 20GB, reduce context windows or kill processes.

## Step 6: Wire into Hermes Plugin (post_tool_call + pre_llm_call)

Create `~/subconscious/local_inference_enhancer.py` as a thin wrapper over `local_inference.py` that handles:
- **Fallback to heuristics** when local servers are down (graceful degradation)
- **Usage stats tracking** for injection display
- **Semantic similarity** for tip dedup (0.80+ = duplicate, 0.55-0.70 = related)

### Plugin post_tool_call integration (error classification):
```python
# In distillation plugin post_tool_call, after error predictor:
if error:
    try:
        from local_inference_enhancer import get_enhancer
        _lie = get_enhancer()
        _error_type = _lie.classify_error(error)
        if _error_type and _error_type != "other":
            # Feed classified error type back into error predictor
            _ep2 = _get_ep(os.environ.get("HERMES_SESSION_ID", "default"))
            _ep2.record_outcome(tool_name, f"error:{_error_type}", error[:100])
    except Exception:
        pass
```

### Plugin pre_llm_call integration (status injection):
```python
# In distillation plugin pre_llm_call:
try:
    from local_inference_enhancer import get_enhancer
    _lie = get_enhancer()
    _lie_injection = _lie.build_injection(user_message or "")
    if _lie_injection:
        lines.append(_lie_injection)
except Exception:
    pass
```

### Semantic similarity benchmarks (tested):
- "database lock error" vs "sqlite database is locked" → 0.796 (true duplicate)
- "terminal command failed" vs "syntax error in python" → 0.553 (related but different)
- "use web_search for research" vs "search the web for information" → 0.815 (paraphrase)

## Hindsight Local Embedded — WORKING (2026-04-10)

Hindsight API's `retain` pipeline works with llama.cpp via a schema echo proxy. Three issues were debugged and fixed:

### Bug Chain (each fix revealed the next)

1. **Context window too small** — Default `-c 2048` insufficient for Hindsight's extraction prompt (~4K tokens of JSON schema).
   - Fix: Restart llama-server with `-c 8192` minimum

2. **Timeout too short** — Hindsight default `LLM_TIMEOUT=120s`. Prompt processing on 8B model at 19 tok/s takes ~210s alone.
   - Fix: Set `HINDSIGHT_API_LLM_TIMEOUT=600` env var

3. **Schema echo (FIXED)** — llama.cpp with `response_format: json_object` echoes the JSON schema from the system prompt before the actual extraction output. Produces two concatenated JSON objects: `{schema...}{actual_facts...}`.
   - Fix: `~/subconscious/llama_schema_echo_proxy.py` — lightweight HTTP proxy on port 9082 that strips the schema echo
   - Proxy parses response, finds the JSON object with actual data keys (`facts`, `reflection`, etc.), discards the schema echo object
   - Strips ~5K chars of schema echo, keeps actual extracted facts JSON
   - Tested: 2 nodes, 6 links extracted successfully from test input

### What works

| Use Case | Works? | Notes |
|----------|--------|-------|
| Direct `/v1/chat/completions` calls | YES | Classification, scoring, judging all fine |
| Direct `/v1/embeddings` calls | YES | Semantic search, similarity, dedup |
| Hindsight `retain` (extraction) | YES | Via echo proxy on port 9082 |
| Hindsight `recall` (retrieval) | YES | Works normally |
| Hindsight Cloud mode | YES | Needs API key, uses cloud LLM for extraction |

### Full Local Hindsight Setup

```bash
# 1. Start echo proxy (sits between Hindsight and llama.cpp)
nohup python3 ~/subconscious/llama_schema_echo_proxy.py \
  --backend-port 8082 --proxy-port 9082 \
  > /tmp/echo-proxy.log 2>&1 &

# 2. Start Hindsight API pointing at PROXY (not llama.cpp directly)
export HINDSIGHT_API_LLM_PROVIDER=openai
export HINDSIGHT_API_LLM_MODEL=llama-3.1-8b-instruct
export HINDSIGHT_API_LLM_BASE_URL=http://127.0.0.1:9082/v1   # PROXY PORT
export HINDSIGHT_API_LLM_API_KEY=local-no-key-needed
export HINDSIGHT_API_LLM_TIMEOUT=600
export HINDSIGHT_API_LOG_LEVEL=info

cd ~/hermes-agent && source venv/bin/activate
nohup hindsight-api --port 8890 > /tmp/hindsight-api.log 2>&1 &

# 3. Create bank and retain
curl -X PUT http://127.0.0.1:8890/v1/default/banks/hermes-training \
  -H "Content-Type: application/json" \
  -d '{"mission": "Agent training knowledge", "retain_mission": "Extract all actionable knowledge."}'

curl -X POST http://127.0.0.1:8890/v1/default/banks/hermes-training/memories \
  -H "Content-Type: application/json" \
  -d '{"items":[{"content":"Your text here","context":"optional context"}]}'
```

### Architecture with Proxy

```
Hindsight API (8890)
    ↓ LLM_BASE_URL=http://127.0.0.1:9082/v1
Echo Proxy (9082) — strips schema echo
    ↓ backend http://127.0.0.1:8082/v1
Llama 3.1 8B (8082) — 19 tok/s with Metal
```

### Debug commands

```bash
# Check proxy is stripping correctly
cat /tmp/echo-proxy.log | grep "Stripped"
# Expected: "Stripped schema echo: 6483 -> 834 chars (118.4s)"

# Check Hindsight extraction logs
strings /tmp/hindsight-api.log | grep -i "extract\|facts"
# Expected: "Extract facts: 2 facts, 1 chunks from 1 contents in 118.421s"

# Check stored graph
curl -s http://127.0.0.1:8890/v1/default/banks/hermes-training/graph | python3 -c "
import sys,json; d=json.load(sys.stdin)
print(f'Nodes: {len(d[\"nodes\"])}, Edges: {len(d[\"edges\"])}')
for n in d['nodes'][:5]:
    print(f'  - {n[\"data\"][\"label\"][:80]}')
"

# Monitor LLM slots during extraction
curl -s http://127.0.0.1:8082/slots | python3 -c "import sys,json; [print(f'Slot busy={s.get(\"is_processing\")}') for s in json.load(sys.stdin)]"
```

### Performance characteristics

- Single retain call: ~120s (mostly prompt eval at 19 tok/s for ~4K token schema)
- Output: ~800 chars of extracted facts JSON (stripped from ~6K with echo)
- Extracted: 2 facts + 6 entity links from one test input
- Token usage: ~3.5K input + ~1.6K output = ~5K total per retain

### Context Window Optimization (CRITICAL)

**Oversized context windows cause swap thrashing on M2 Air.** Default configs use way more GPU memory than needed for agent reflexes. Reducing context sizes gave 2-4x speedup:

| Model | Old ctx | New ctx | Speed Before | Speed After | Why |
|-------|---------|---------|-------------|-------------|-----|
| Phi-3 3.8B | 2048 | 1024 | 14 tok/s | **33 tok/s** | Classifier only needs short prompts |
| Llama 8B | 8192 | 2048 | 4 tok/s | **17.5 tok/s** | Reward judge doesn't need 8K context |
| Nomic embed | 512 | 512 | instant | instant | Already optimal |

**Before optimization**: 22.5 GB swap used out of 23.5 GB — system thrashing
**After optimization**: 12.2 GB swap — 10 GB freed

Diagnosis: `sysctl vm.swapusage` — if swap is near max, context windows are too large.
Fix: Restart llama-servers with `-c` matching actual use case. For scoring/classification, 1024 is plenty. For reward judging, 2048 is plenty.

**Only use large context (8192+) for Hindsight extraction** — which needs ~4K tokens for the JSON schema prompt.

### Cloud Reasoning Models (MiniMax M2.7 + GLM-5.1)

Both MiniMax M2.7 and GLM-5.1 are reasoning models with built-in thinking phases. They use tokens differently than standard models.

#### MiniMax M2.7

- **Base URL**: `https://api.minimax.io/v1` (international endpoint)
  - WRONG: `api.minimax.chat` (returns auth errors)
- **Model name**: `MiniMax-M2.7`
  - WRONG: `MiniMax-M1`, `m2.7`, `minimax-m2.7` (case-sensitive)
- Thinking output in `<think\n...reasoning...\n</think\n>` within `content` field
- Local wrapper server on port 8084: `~/subconscious/minimax_wrapper.py`
  - Strips think tags automatically, returns clean content
  - Falls back to Llama 8B if MiniMax API unavailable
  - OpenAI-compatible `/v1/chat/completions` endpoint

#### GLM-5.1 (Z.AI)

- **Base URL**: `https://api.z.ai/api/coding/paas/v4/chat/completions`
- **Model name**: `glm-5.1`
- Also a reasoning model — uses `reasoning_content` field in response
- With max_tokens=200, it spends ALL tokens on reasoning and returns empty `content`
- **Must set max_tokens >= 2000** to leave room for actual output after reasoning

#### Critical Gotchas for ALL Reasoning Models

1. **Thinking tokens consume max_tokens** — Both M2.7 and GLM-5.1's reasoning phase uses tokens from your max_tokens budget. If you set max_tokens=200 and reasoning uses 201 tokens, you get EMPTY output.
   - M2.7: set max_tokens >= 4000 for JSON extraction, >= 2000 for scoring
   - GLM-5.1: set max_tokens >= 2000 for any non-trivial task

2. **Thinking tag format (M2.7)** — M2.7 outputs `<think\n...content...\n</think\n>` where `\n` is a real newline. The actual answer comes AFTER `</think\n>`.

3. **Robust tag stripping** — Use this pattern:
   ```python
   if content.startswith("<think"):
       think_end = content.find("</think")
       if think_end >= 0:
           gt_pos = content.find(">", think_end)
           if gt_pos >= 0:
               content = content[gt_pos + 1:].strip()
           else:
               content = ""  # thinking consumed all tokens
   ```

4. **JSON extraction** — After stripping thinking, use `rfind("{")` / `rfind("}")` to extract JSON. Both models sometimes add conversational wrapper text around JSON responses.

5. **GLM-5.1 migration scripts** — When using GLM-5.1 for bulk extraction (e.g., migrating tips), the response `content` field may be EMPTY while `reasoning_content` has the full chain. Check both fields.

### Integration in local_inference.py

Functions added:
- `m27_analyze(prompt, max_tokens)` — general analysis, returns text
- `m27_score_tip(condition, recommendation, rationale)` — 4-dimension tip quality scoring (overall/novelty/actionability/specificity)
- `m27_reward_step(tool_name, task_description, success, result_summary)` — multi-factor step reward (reward/tool_fitness/execution_quality/outcome_quality)
- `m27_critique_trajectory(tool_calls, task_goal)` — trajectory-level critique
- `m27_best_of_n(tips, n)` — rank and select best N tips

### MiniMax M2.7 Local Wrapper (port 8084)

A local OpenAI-compatible server that wraps MiniMax M2.7 API with automatic think-tag stripping and fallback to local Llama 8B.

**File**: `~/subconscious/minimax_wrapper.py`
**Port**: 8084
**Start**: `nohup python3 ~/subconscious/minimax_wrapper.py > /tmp/minimax_wrapper.log 2>&1 &`

Endpoints:
- `GET /health` — status + stats
- `GET /v1/models` — lists MiniMax-M2.7 + llama-3.1-8b-local
- `POST /v1/chat/completions` — routes by model name
  - Model containing "minimax" or "m2" → MiniMax API
  - Other models → local Llama 8B fallback
- `GET /stats` — call/fallback/error counts

Features:
- Strips `<think...>...</think\n>` from content automatically
- Preserves reasoning in `reasoning_content` field
- If MiniMax API fails, auto-falls back to local Llama 8B
- No external dependencies (stdlib only)

### Plugin Wiring (R142)

M2.7 reward scoring wired into distillation plugin `post_tool_call` hook:
- Only fires on successful tool calls (not errors, not skip-list tools)
- Records M2.7 multi-factor reward into `reward_shaping` system
- Components: tool_fitness, execution_quality, outcome_quality
- Wraps in try/except for graceful degradation when M2.7 unavailable

### Performance (M2.7)

- M2.7 reasoning: ~300-500 reasoning tokens per call
- Total tokens per scoring call: ~400-600
- Latency: 10-12 seconds for scoring through wrapper (includes reasoning)
- Cost: covered by MiniMax subscription
- Key limit: max plan key has ~3-4 day TTL, then expires

## OpenClaw-RL Integration Pattern

Research from OpenClaw-RL (Princeton, March 2026) maps directly to this architecture:
- **Next-state signals are universal learning sources** — tool outputs, errors, user corrections all encode evaluative + directive info
- **Async PRM judge** — Phi-3 classifies in post_tool_call while Llama 8B scores trajectories between turns, zero coordination overhead
- **Hindsight-Guided On-Policy Distillation (OPD)** — extract textual hints from next state, construct enhanced teacher context, richer than scalar reward alone

The 3-tier local inference (Phi-3/Llama-8B/Nomic-Embed) IS a mini Process Reward Model system.
