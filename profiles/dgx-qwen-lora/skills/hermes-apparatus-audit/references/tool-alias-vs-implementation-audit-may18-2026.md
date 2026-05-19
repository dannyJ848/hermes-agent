# Tool Alias vs Implementation Audit — May 18, 2026

## Finding
The CLI reports 27 tools (15 enabled + 12 disabled), but toolsets.py defines 76 aliases. The gap is 60 unimplemented aliases.

## Breakdown
- **Implemented and enabled**: 15 (browser, clarify, code_execution, cronjob, terminal, etc.)
- **Implemented but disabled**: 12 (web, moa, rl, discord, etc. — need API keys)
- **Implemented but gated**: 18 (kanban, ha_*, messaging, etc. — need config)
- **Aliases without implementation**: 60 (defined in toolsets.py but no tool function exists)
- **Internal helpers not exposed**: 15 (cleanup, notify, reset, etc.)

## How to Audit
```python
# Count actual tool functions
import ast, pathlib
tool_dir = pathlib.Path("~/.hermes/tools").expanduser()
actual_tools = []
for f in tool_dir.glob("*.py"):
    try:
        tree = ast.parse(f.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if "task_id" in [arg.arg for arg in node.args.args]:
                    actual_tools.append(node.name)
    except:
        pass
print(f"Actual tool functions: {len(actual_tools)}")

# Count aliases
toolsets = ast.parse(pathlib.Path("~/.hermes/toolsets.py").read_text())
aliases = []
for node in ast.walk(toolsets):
    if isinstance(node, ast.Dict) and hasattr(node, 'keys'):
        for key in node.keys:
            if isinstance(key, ast.Constant):
                aliases.append(key.value)
print(f"Tool aliases: {len(aliases)}")
print(f"Unimplemented: {len(set(aliases) - set(actual_tools))}")
```

## To Enable More Tools
Configure API keys in `~/.hermes/.env`:
- `OPENROUTER_API_KEY` → moa toolset (+1)
- `EXA_API_KEY`, `PARALLEL_API_KEY`, `TAVILY_API_KEY`, `FIRECRAWL_API_KEY` → web toolset (+2)
- `DISCORD_BOT_TOKEN` → discord toolset (+2)
- `TINKER_API_KEY`, `WANDB_API_KEY` → rl toolset (+10)
- `HASS_TOKEN` → homeassistant toolset (+4)
- Gateway running → messaging toolset (+1)
- Image gen provider → image_generate (+1)
- Video provider → video_analyze (+1)
- TTS provider → text_to_speech (+1)
