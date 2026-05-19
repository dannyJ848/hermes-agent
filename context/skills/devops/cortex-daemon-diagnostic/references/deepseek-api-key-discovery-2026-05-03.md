# DeepSeek API Key Discovery Pattern — May 3, 2026

## Problem
The `llm_judge.py` script needs `DEEPSEEK_API_KEY` for flywheel evals, but the environment variable is not set even though the key exists in `~/.hermes/.env`.

## Discovery Path
1. Check `~/.hermes/.env` for the key:
   ```bash
   grep DEEPSEEK_API_KEY ~/.hermes/.env
   # DEEPSEEK_API_KEY=sk-7ab7950...
   ```
2. Verify the key works:
   ```bash
   export DEEPSEEK_API_KEY=$(grep DEEPSEEK_API_KEY ~/.hermes/.env | cut -d= -f2)
   curl -H "Authorization: Bearer $DEEPSEEK_API_KEY" https://api.deepseek.com/v1/models
   # Returns: deepseek-v4-pro, deepseek-v4-flash
   ```
3. Export the key before starting any daemon or script that needs it:
   ```bash
   export DEEPSEEK_API_KEY=$(grep DEEPSEEK_API_KEY ~/.hermes/.env | cut -d= -f2)
   ```

## Key Lessons
1. **API keys live in `~/.hermes/.env`**: This is the canonical location for Hermes agent credentials. Always check here first before asking the user for credentials.
2. **Export before daemon start**: Background processes (scheduler daemon, cortex daemon) don't inherit the shell's environment. Export the key explicitly before starting them.
3. **DeepSeek v4-pro is the model**: Use `deepseek-v4-pro` for flywheel evals. It's slower (~15s per call) but high quality. For bulk evals, use `use_llm_every=50` to only call DeepSeek for 2% of pairs.
4. **Timeout on bulk evals**: 3+ pair eval sweeps timeout (>120s) because each DeepSeek call takes ~15s sequentially. The workaround is `use_llm_every=50` in `cortex_daemon.py` line 48.
5. **Credential discovery order**:
   - First: `~/.hermes/.env`
   - Second: shell environment (`echo $DEEPSEEK_API_KEY`)
   - Third: ask user (only if above fail)
