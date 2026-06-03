import json
from pathlib import Path

from examples.openai_tool_calling_adapter import (
    build_demo_rygnal,
    handle_openai_tool_call,
)


def test_openai_style_tool_call_allows_safe_file_read(tmp_path):
    audit_log_path = tmp_path / "audit_log.jsonl"
    rygnal = build_demo_rygnal(str(audit_log_path))

    tool_call = {
        "id": "call_safe_read",
        "type": "function",
        "function": {
            "name": "file_read",
            "arguments": json.dumps(
                {
                    "action": "read_file",
                    "target": "README.md",
                }
            ),
        },
    }

    result = handle_openai_tool_call(tool_call, rygnal)

    assert result["tool_call_id"] == "call_safe_read"
    assert result["allowed"] is True
    assert result["executed"] is True
    assert result["decision"] == "allow"
    assert result["execution_status"] == "executed"
    assert result["risk_level"] == "low"
    assert result["audit_event_id"]
    assert result["output"]["target"] == "README.md"
    assert Path(audit_log_path).exists()


def test_openai_style_tool_call_blocks_secret_file_read(tmp_path):
    audit_log_path = tmp_path / "audit_log.jsonl"
    rygnal = build_demo_rygnal(str(audit_log_path))

    tool_call = {
        "id": "call_secret_read",
        "type": "function",
        "function": {
            "name": "file_read",
            "arguments": json.dumps(
                {
                    "action": "read_file",
                    "target": ".env",
                }
            ),
        },
    }

    result = handle_openai_tool_call(tool_call, rygnal)

    assert result["tool_call_id"] == "call_secret_read"
    assert result["allowed"] is False
    assert result["executed"] is False
    assert result["decision"] == "block"
    assert result["execution_status"] == "skipped"
    assert result["risk_level"] == "critical"
    assert result["audit_event_id"]
    assert result["output"] is None
    assert Path(audit_log_path).exists()


def test_openai_style_tool_call_handles_invalid_json_arguments(tmp_path):
    audit_log_path = tmp_path / "audit_log.jsonl"
    rygnal = build_demo_rygnal(str(audit_log_path))

    tool_call = {
        "id": "call_invalid_json",
        "type": "function",
        "function": {
            "name": "file_read",
            "arguments": "not-json",
        },
    }

    result = handle_openai_tool_call(tool_call, rygnal)

    assert result["tool_call_id"] == "call_invalid_json"
    assert result["audit_event_id"]
    assert Path(audit_log_path).exists()
