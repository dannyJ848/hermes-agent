# Axolotl Dataset Format Conversion (May 13, 2026)

## Problem
Axolotl's `chat_template` dataset type requires `messages` field with `role`/`content` structure:
```json
{"messages": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}
```

Raw datasets often come in `input`/`output` format:
```json
{"input": "...", "output": "..."}
```

Using `type: chat_template` with `input`/`output` format produces:
```
ValueError: Messages is null. Please check `field_messages`.
```

## Conversion Script

For datasets with 2M+ examples, use streaming conversion to avoid memory issues:

```python
import json
from pathlib import Path

def convert_to_messages(input_file, output_file):
    with open(input_file) as f:
        lines = f.readlines()
    
    with open(output_file, 'w') as f:
        for line in lines:
            data = json.loads(line)
            messages = [
                {'role': 'user', 'content': data['input']},
                {'role': 'assistant', 'content': data['output']}
            ]
            f.write(json.dumps({'messages': messages}) + '\n')
    
    print(f'Converted {len(lines)} examples to {output_file}')

# Usage
base = Path('/data/SpecForge/custom_dflash/datasets')
convert_to_messages(base / 'tier1-reasoning.jsonl', base / 'tier1-reasoning-chat.jsonl')
```

## Config Update

```yaml
datasets:
  - path: /data/SpecForge/custom_dflash/datasets/tier1-reasoning-chat.jsonl
    type: chat_template
  - path: /data/SpecForge/custom_dflash/datasets/tier2-reasoning-chat.jsonl
    type: chat_template
  - path: /data/SpecForge/custom_dflash/datasets/tier3-health-chat.jsonl
    type: chat_template
```

## Deprecated Config Keys

Remove `max_packed_sequence_len` — deprecated in newer axolotl versions:
```
DeprecationWarning: `max_packed_sequence_len` is no longer supported
```

## Axolotl Telemetry Bug

Axolotl 0.16.1 has a missing `whitelist.yaml` bug. Fix:
```bash
echo 'organizations: []' > ~/train-venv/lib/python3.12/site-packages/axolotl/telemetry/whitelist.yaml
```

Error without fix:
```
FileNotFoundError: [Errno 2] No such file or directory: '.../axolotl/telemetry/whitelist.yaml'
```
Or:
```
TypeError: 'NoneType' object is not subscriptable
```