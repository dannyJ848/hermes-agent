# Qwen3.6 Thinking Mode Control

## Discovery Date: May 14, 2026

Qwen3.6 has native thinking support via special tokens in the vocabulary:
- `<think>` — token ID 248068
- `</think>` — token ID 248069

## Chat Template Control

The thinking behavior is controlled via `chat_template_kwargs` passed to the tokenizer:

```python
from transformers import AutoTokenizer

tok = AutoTokenizer.from_pretrained('/data/models/Qwen3.6-27B-Uncensored', trust_remote_code=True)

# Enable thinking (default)
prompt = tok.apply_chat_template(
    messages,
    tokenize=False,
    add_generation_prompt=True,
    enable_thinking=True  # Produces: "<|im_start|>assistant\n<think>\n"
)

# Disable thinking
prompt = tok.apply_chat_template(
    messages,
    tokenize=False,
    add_generation_prompt=True,
    enable_thinking=False  # Produces: "<|im_start|>assistant\n<think>\n\n</think>\n\n"
)
```

## vLLM API Usage

```bash
# Enable thinking (default)
curl http://localhost:8000/v1/chat/completions \
  -d '{"model":"merged-lora","messages":[{"role":"user","content":"What is 2+2?"}],"chat_template_kwargs":{"enable_thinking":true}}'

# Disable thinking
curl http://localhost:8000/v1/chat/completions \
  -d '{"model":"merged-lora","messages":[{"role":"user","content":"What is 2+2?"}],"chat_template_kwargs":{"enable_thinking":false}}'
```

## Reasoning Parser Behavior

| Configuration | Content Field | Reasoning Field | Notes |
|--------------|---------------|-----------------|-------|
| No `--reasoning-parser` | Contains thinking + answer | null | Raw model output |
| `--reasoning-parser qwen3` | null or empty | Contains thinking | Content may be null |

**Recommendation for Hermes:** Omit `--reasoning-parser` — Hermes expects content in the standard `content` field.

## Speed Impact

| Mode | Speed | Quality |
|------|-------|---------|
| No thinking | ~15-40 tok/s | Direct answers |
| With thinking | ~4-8 tok/s | Reasoning + answer |

Thinking mode is 5-10x slower because the model generates reasoning tokens before the answer.

## Hermes Config

```yaml
model:
  default: merged-lora
  provider: custom
  chat_template_kwargs:
    enable_thinking: true  # or false
```

## Instruct Mode Parameters (from Qwen3.6 README)

For non-thinking (instruct) mode, use these generation parameters:
- `temperature=0.7`
- `top_p=0.80`
- `top_k=20`
- `presence_penalty=1.5`
- `repetition_penalty=1.0`

For thinking mode:
- `temperature=1.0`
- `top_p=0.95`
- `top_k=20`
- `presence_penalty=0.0`
- `repetition_penalty=1.0`
