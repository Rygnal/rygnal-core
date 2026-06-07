"""Optional live OpenAI demo protected by Rygnal.

This module only calls OpenAI when OPENAI_API_KEY is available or a client is injected.
It is not used by CI as a real network dependency.
"""

from __future__ import annotations

import json
import os
from typing import Any

from examples.openai_tool_calling_adapter import build_demo_rygnal, handle_openai_tool_call

DEFAULT_MODEL = "gpt-4.1-mini"
DEFAULT_PROMPT = "Use the file_read tool to read README.md."


def run_live_openai_demo(
    *,
    client: Any | None = None,
    model: str | None = None,
    prompt: str = DEFAULT_PROMPT,
    audit_log_path: str = "logs/live_openai_audit_log.jsonl",
) -> dict[str, Any]:
    """Run an optional live OpenAI tool-calling demo through Rygnal."""
    if client is None and not os.getenv("OPENAI_API_KEY"):
        return {
            "skipped": True,
            "reason": "OPENAI_API_KEY is not set.",
        }

    client = client or _build_openai_client()
    model = model or os.getenv("OPENAI_MODEL", DEFAULT_MODEL)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "You are a demo agent. Use tools only when useful.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        tools=[_file_read_tool_schema()],
        tool_choice="auto",
    )

    tool_call = _first_tool_call(response)

    if tool_call is None:
        return {
            "skipped": False,
            "tool_called": False,
            "message": _message_content(response),
        }

    rygnal = build_demo_rygnal(audit_log_path=audit_log_path)
    protected_result = handle_openai_tool_call(tool_call, rygnal)

    return {
        "skipped": False,
        "tool_called": True,
        "model": model,
        "result": protected_result,
    }


def _build_openai_client() -> Any:
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError(
            "OpenAI SDK is not installed. Install with: pip install -e '.[live-openai]'"
        ) from exc

    return OpenAI()


def _file_read_tool_schema() -> dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": "file_read",
            "description": "Read a safe local demo file through Rygnal.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["read_file"],
                    },
                    "target": {
                        "type": "string",
                    },
                },
                "required": ["action", "target"],
                "additionalProperties": False,
            },
        },
    }


def _first_tool_call(response: Any) -> dict[str, Any] | None:
    choices = _get(response, "choices", [])
    if not choices:
        return None

    message = _get(choices[0], "message", None)
    if message is None:
        return None

    tool_calls = _get(message, "tool_calls", None)
    if not tool_calls:
        return None

    return _normalize_tool_call(tool_calls[0])


def _message_content(response: Any) -> str | None:
    choices = _get(response, "choices", [])
    if not choices:
        return None

    message = _get(choices[0], "message", None)
    if message is None:
        return None

    return _get(message, "content", None)


def _normalize_tool_call(tool_call: Any) -> dict[str, Any]:
    function = _get(tool_call, "function", {})
    return {
        "id": _get(tool_call, "id", None),
        "type": _get(tool_call, "type", "function"),
        "function": {
            "name": _get(function, "name", ""),
            "arguments": _get(function, "arguments", "{}"),
        },
    }


def _get(value: Any, key: str, default: Any = None) -> Any:
    if isinstance(value, dict):
        return value.get(key, default)

    return getattr(value, key, default)


def main() -> None:
    """Run the optional live demo from the command line."""
    print(json.dumps(run_live_openai_demo(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
