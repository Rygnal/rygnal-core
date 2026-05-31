from pathlib import Path

import pytest

from rygnal.models import Decision, ToolRequest
from rygnal.policy_engine import PolicyEngine, load_default_policy_engine


def test_policy_engine_loads_default_policy():
    engine = load_default_policy_engine()

    assert engine.rules
    assert len(engine.rules) >= 4


def test_blocks_env_file_read():
    engine = load_default_policy_engine()

    request = ToolRequest(
        tool_name="file_read",
        action="read_file",
        target=".env",
    )

    result = engine.evaluate(request)

    assert result.decision == Decision.BLOCK
    assert result.allowed is False
    assert result.policy_id == "block-env-read"


def test_blocks_dangerous_shell_command():
    engine = load_default_policy_engine()

    request = ToolRequest(
        tool_name="shell_command",
        action="execute",
        input="rm -rf /important-folder",
    )

    result = engine.evaluate(request)

    assert result.decision == Decision.BLOCK
    assert result.allowed is False
    assert result.policy_id == "block-dangerous-shell"


def test_file_delete_requires_approval():
    engine = load_default_policy_engine()

    request = ToolRequest(
        tool_name="file_delete",
        action="delete_file",
        target="customer_data.csv",
    )

    result = engine.evaluate(request)

    assert result.decision == Decision.REQUIRE_APPROVAL
    assert result.allowed is False
    assert result.policy_id == "approval-file-delete"


def test_external_api_send_is_simulated():
    engine = load_default_policy_engine()

    request = ToolRequest(
        tool_name="external_api_send",
        action="send_data",
        input={"url": "https://example.com", "payload": "demo"},
    )

    result = engine.evaluate(request)

    assert result.decision == Decision.SIMULATE
    assert result.allowed is True
    assert result.policy_id == "simulate-external-api-send"


def test_safe_file_read_is_allowed_by_default():
    engine = load_default_policy_engine()

    request = ToolRequest(
        tool_name="file_read",
        action="read_file",
        target="README.md",
    )

    result = engine.evaluate(request)

    assert result.decision == Decision.ALLOW
    assert result.allowed is True
    assert result.policy_id is None


def test_invalid_policy_file_raises_error(tmp_path: Path):
    bad_policy = tmp_path / "bad_policy.yaml"
    bad_policy.write_text("rules: invalid")

    with pytest.raises(ValueError):
        PolicyEngine.from_file(bad_policy)
