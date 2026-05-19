# DeepSeek API Key Missing — May 3, 2026

## Incident
Flywheel eval cycles were hanging "running" for 30+ minutes. 12 eval cycles stuck since 13:52. Root cause: DeepSeek API key not set in environment.

## Discovery
- `DEEPSEEK_API_KEY` was present in `~/.hermes/.env` but NOT loaded into environment
- `llm_judge.py` loads from `.env` file, but daemon processes didn't inherit it
- API calls returned 401, causing infinite retries/timeouts

## Fix
```bash
# Check if key exists in .env
cat ~/.hermes/.env | grep DEEPSEEK_API_KEY

# Export it before starting any daemon
export DEEPSEEK_API_KEY=$(grep DEEPSEEK_API_KEY ~/.hermes/.env | cut -d= -f2)

# Verify API works
curl -s https://api.deepseek.com/v1/models -H "Authorization: Bearer $DEEPSEEK_API_KEY"
```

## Prevention
- Always check `env | grep DEEPSEEK_API_KEY` before starting flywheel or LLM judge
- Add key export to daemon startup scripts
- Consider adding `.env` loading to daemon init

## Files
- `~/.hermes/.env` — API keys stored here
- `~/subconscious/llm_judge.py` — loads key from env or `.env` file
- `~/hermes-agent/config.yaml` — references `api_key_env: DEEPSEEK_API_KEY`
