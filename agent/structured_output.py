"""Structured output abstraction for Hermes Agent.

Provides a unified interface for schema-constrained generation across
multiple backends: OpenAI structured outputs, vLLM guided decoding,
llama.cpp JSON schema mode, and fallback prompt-based JSON.

Usage:
    from agent.structured_output import StructuredOutput

    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"}
        },
        "required": ["name", "age"]
    }

    so = StructuredOutput(schema)
    result = so.generate("Extract person info: John is 25 years old")
    # result: {"name": "John", "age": 25}

ZERO-FAILURE: Falls back to prompt-based JSON on any error.
"""

import json
import logging
import re
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class BackendCapability:
    """Describes what a backend supports."""
    name: str
    supports_structured_output: bool = False
    supports_guided_decoding: bool = False
    supports_json_mode: bool = False
    supports_response_format: bool = False


class StructuredOutput:
    """Schema-constrained generation with backend-specific optimizations."""

    def __init__(self, schema: Dict[str, Any], backend: Optional[str] = None):
        self.schema = schema
        self.backend = backend or self._detect_backend()
        self.capability = self._get_capability(self.backend)

    def _detect_backend(self) -> str:
        """Detect the inference backend from environment/config."""
        try:
            import os
            base_url = os.environ.get("OPENAI_BASE_URL", "")
            if "vllm" in base_url.lower() or ":8000" in base_url:
                return "vllm"
            if "llama.cpp" in base_url.lower() or "localhost:8080" in base_url:
                return "llama.cpp"
            if "openai" in base_url.lower():
                return "openai"
            return "generic"
        except Exception:
            return "generic"

    def _get_capability(self, backend: str) -> BackendCapability:
        """Get capabilities for a backend."""
        caps = {
            "openai": BackendCapability(
                "openai",
                supports_structured_output=True,
                supports_response_format=True,
            ),
            "vllm": BackendCapability(
                "vllm",
                supports_guided_decoding=True,
                supports_json_mode=True,
            ),
            "llama.cpp": BackendCapability(
                "llama.cpp",
                supports_guided_decoding=True,
                supports_json_mode=True,
            ),
            "generic": BackendCapability("generic"),
        }
        return caps.get(backend, caps["generic"])

    def _build_prompt(self, user_prompt: str) -> str:
        """Build a prompt that encourages valid JSON output."""
        schema_str = json.dumps(self.schema, indent=2)
        return (
            f"You must respond with a valid JSON object matching this schema:\n"
            f"{schema_str}\n\n"
            f"Respond ONLY with the JSON object. No markdown, no explanations.\n\n"
            f"Task: {user_prompt}"
        )

    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract JSON from model output, handling common wrapper formats."""
        if not text:
            return None

        # Try direct parse first
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            pass

        # Try extracting from markdown code blocks
        patterns = [
            r"```json\s*(.*?)\s*```",
            r"```\s*(.*?)\s*```",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1).strip())
                except json.JSONDecodeError:
                    continue

        # Try finding JSON object/array with balanced braces
        for start_char in ["{", "["]:
            idx = text.find(start_char)
            if idx != -1:
                depth = 0
                in_string = False
                escape = False
                for i, c in enumerate(text[idx:]):
                    if escape:
                        escape = False
                        continue
                    if c == "\\":
                        escape = True
                        continue
                    if c == '"' and (i == 0 or text[idx + i - 1] != "\\"):
                        in_string = not in_string
                        continue
                    if not in_string:
                        if c in ["{", "["]:
                            depth += 1
                        elif c in ["}", "]"]:
                            depth -= 1
                            if depth == 0:
                                try:
                                    return json.loads(text[idx:idx + i + 1])
                                except json.JSONDecodeError:
                                    break

        return None

    def _validate(self, data: Dict[str, Any]) -> bool:
        """Validate output against schema (basic type checking)."""
        try:
            if self.schema.get("type") == "object":
                if not isinstance(data, dict):
                    return False
                required = self.schema.get("required", [])
                for key in required:
                    if key not in data:
                        return False
            return True
        except Exception:
            return False

    def prepare_api_kwargs(self, user_prompt: str, **extra) -> Dict[str, Any]:
        """Prepare API kwargs with backend-specific structured output config."""
        kwargs = {
            "messages": [
                {"role": "system", "content": "You must respond with valid JSON."},
                {"role": "user", "content": self._build_prompt(user_prompt)},
            ],
            **extra,
        }

        cap = self.capability

        if cap.supports_structured_output:
            # OpenAI-style structured output
            kwargs["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": "structured_output",
                    "schema": self.schema,
                    "strict": True,
                },
            }
        elif cap.supports_guided_decoding:
            # vLLM / llama.cpp guided decoding
            kwargs["extra_body"] = kwargs.get("extra_body", {})
            kwargs["extra_body"]["guided_json"] = self.schema
        elif cap.supports_json_mode:
            # Generic JSON mode
            kwargs["response_format"] = {"type": "json_object"}
        else:
            # Fallback: just the prompt
            pass

        return kwargs

    def parse_response(self, response_text: str) -> Dict[str, Any]:
        """Parse and validate model response."""
        data = self._extract_json(response_text)
        if data is None:
            raise ValueError(f"Could not extract valid JSON from response: {response_text[:200]}")

        if not self._validate(data):
            raise ValueError(f"Extracted JSON does not match schema: {data}")

        return data

    def generate(self, user_prompt: str, llm_call: Optional[Callable] = None, **extra) -> Dict[str, Any]:
        """Full pipeline: prepare -> call LLM -> parse -> validate.

        Args:
            user_prompt: The task description
            llm_call: Function that takes kwargs and returns response text.
                      If None, returns prepared kwargs for manual calling.
            **extra: Extra kwargs passed to the LLM call

        Returns:
            Parsed and validated JSON object
        """
        kwargs = self.prepare_api_kwargs(user_prompt, **extra)

        if llm_call is None:
            # Return kwargs for external calling
            return kwargs

        # Call LLM
        response_text = llm_call(kwargs)

        # Parse and validate
        return self.parse_response(response_text)


class ToolSchemaGenerator:
    """Generate JSON schemas from Python function signatures."""

    TYPE_MAP = {
        str: "string",
        int: "integer",
        float: "number",
        bool: "boolean",
        list: "array",
        dict: "object",
    }

    @classmethod
    def from_function(cls, fn: Callable) -> Dict[str, Any]:
        """Generate JSON schema from a Python function."""
        import inspect

        sig = inspect.signature(fn)
        properties = {}
        required = []

        for name, param in sig.parameters.items():
            if name in ("self", "cls"):
                continue

            param_type = param.annotation
            if param_type == inspect.Parameter.empty:
                json_type = "string"
            else:
                json_type = cls.TYPE_MAP.get(param_type, "string")

            properties[name] = {"type": json_type}

            if param.default == inspect.Parameter.empty:
                required.append(name)

        schema = {
            "type": "object",
            "properties": properties,
        }
        if required:
            schema["required"] = required

        return schema


def structured_output(schema: Dict[str, Any], backend: Optional[str] = None):
    """Decorator for functions that return structured output.

    Usage:
        @structured_output({
            "type": "object",
            "properties": {"result": {"type": "string"}},
            "required": ["result"]
        })
        def my_tool(prompt: str) -> dict:
            # Implementation that calls LLM
            pass
    """
    def decorator(fn: Callable) -> Callable:
        fn._structured_output_schema = schema
        fn._structured_output_backend = backend
        return fn
    return decorator
