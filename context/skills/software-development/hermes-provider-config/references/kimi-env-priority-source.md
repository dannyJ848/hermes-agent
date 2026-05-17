# Source Code: Why ~/.hermes/.env Beats Shell Environment

## The Code

From `agent/credential_pool.py`, lines ~1409-1415:

```python
def _get_env_prefer_dotenv(key: str) -> str:
    """Prefer ~/.hermes/.env over os.environ.

    The user's config file is the authoritative source for Hermes credentials.
    Stale env vars from parent processes (Codex CLI, test scripts, etc.)
    should not override deliberate changes to the .env file.
    """
    env_file = load_env()
    val = env_file.get(key) or os.environ.get(key) or ""
    return val.strip()
```

## What This Means

1. `~/.hermes/.env` is checked FIRST
2. If the key exists in `.env` (even if empty), it wins
3. Shell environment variables are ONLY used as fallback
4. This is intentional design — prevents stale parent-process env vars from overriding user config

## Practical Impact

| Scenario | Result |
|----------|--------|
| `KIMI_API_KEY` in `.env`, `MOONSHOT_API_KEY` in shell | Uses `.env` value |
| Both `KIMI_API_KEY` and `MOONSHOT_API_KEY` in `.env` | Uses `KIMI_API_KEY` (first match) |
| `MOONSHOT_API_KEY` in shell, nothing in `.env` | Uses shell value |
| Old key in `.env`, new key in shell | Uses OLD key from `.env` |

## The Fix Pattern

When updating API keys, update BOTH locations:

```bash
# 1. Update .env (authoritative source)
echo "KIMI_API_KEY=sk-kimi-NEWKEY" >> ~/.hermes/.env

# 2. Update shell profile (for non-Hermes tools)
echo 'export MOONSHOT_API_KEY="sk-kimi-NEWKEY"' >> ~/.zshrc

# 3. Clear auth cache (removes exhausted status)
rm ~/.hermes/auth.json

# 4. Reload shell env
source ~/.zshrc
```

## Provider Registry

From `hermes_cli/auth.py`, the Kimi provider config:

```python
"kimi-coding": ProviderConfig(
    id="kimi-coding",
    name="Kimi / Moonshot",
    auth_type="api_key",
    inference_base_url="https://api.moonshot.ai/v1",
    api_key_env_vars=("KIMI_API_KEY", "KIMI_CODING_API_KEY"),
    base_url_env_var="KIMI_BASE_URL",
),
```

Note: `api_key_env_vars` lists `KIMI_API_KEY` first, then `KIMI_CODING_API_KEY`. The credential pool seeds from these env vars using `_get_env_prefer_dotenv()`.

## Key Routing

From `hermes_cli/auth.py`, lines ~472-490:

```python
KIMI_CODE_BASE_URL = "https://api.kimi.com/coding"

def _resolve_kimi_base_url(api_key: str, default_url: str, env_override: str) -> str:
    if env_override:
        return env_override
    if not api_key:
        return default_url
    if api_key.startswith("sk-kimi-"):
        return KIMI_CODE_BASE_URL
    return default_url
```

Keys starting with `sk-kimi-` → `https://api.kimi.com/coding`
Legacy keys → `https://api.moonshot.ai/v1`
