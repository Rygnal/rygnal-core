from pathlib import Path

import pytest
import yaml

from rygnal.models import Decision, ToolRequest
from rygnal.policy_engine import (
    DEFAULT_POLICY_PATH,
    PolicyEngine,
    PolicyLoadError,
    load_default_policy_engine,
)


def test_policy_engine_constructor_defaults_to_block() -> None:
    engine = PolicyEngine()

    result = engine.evaluate(ToolRequest(tool_name="unknown_tool"))

    assert engine.default_decision == Decision.BLOCK
    assert result.decision == Decision.BLOCK
    assert result.allowed is False


def test_default_policy_yaml_is_fail_closed() -> None:
    policy = yaml.safe_load(DEFAULT_POLICY_PATH.read_text())

    assert policy["default_decision"] == Decision.BLOCK.value


def test_default_policy_loader_rejects_default_allow(monkeypatch, tmp_path: Path) -> None:
    unsafe_policy = tmp_path / "unsafe_default_policy.yaml"
    unsafe_policy.write_text(
        """
policy_version: policy.v2
default_decision: allow
rules: []
"""
    )

    import rygnal.policy_engine as policy_engine_module

    monkeypatch.setattr(policy_engine_module, "DEFAULT_POLICY_PATH", unsafe_policy)

    with pytest.raises(PolicyLoadError, match="default_policy.yaml must be fail-closed"):
        load_default_policy_engine()


def test_default_policy_no_match_blocks() -> None:
    engine = load_default_policy_engine()

    result = engine.evaluate(ToolRequest(tool_name="unknown_tool", action="noop"))

    assert engine.default_decision == Decision.BLOCK
    assert result.decision == Decision.BLOCK
    assert result.allowed is False
    assert result.policy_id is None
    assert result.explanation is not None
    assert result.explanation.default_decision is True


def test_default_policy_allows_readme_only_by_explicit_rule() -> None:
    engine = load_default_policy_engine()

    result = engine.evaluate(
        ToolRequest(tool_name="file_read", action="read_file", target="README.md")
    )

    assert engine.default_decision == Decision.BLOCK
    assert result.decision == Decision.ALLOW
    assert result.allowed is True
    assert result.policy_id == "allow-readme-read"
    assert result.explanation is not None
    assert result.explanation.default_decision is False
    assert "target_matches" in result.explanation.matched_conditions
    assert "target_not_matches" in result.explanation.matched_conditions


def test_default_policy_blocks_sensitive_file_read_patterns() -> None:
    engine = load_default_policy_engine()

    for target in ("/etc/passwd", "secrets/api.txt", "private.pem", ".ssh/id_rsa"):
        result = engine.evaluate(
            ToolRequest(tool_name="file_read", action="read_file", target=target)
        )

        assert result.decision == Decision.BLOCK
        assert result.allowed is False
        assert result.policy_id == "block-sensitive-path-read"
