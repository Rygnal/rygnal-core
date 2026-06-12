from pathlib import Path

from rygnal.models import Decision, ToolRequest
from rygnal.policy_engine import PolicyEngine, load_default_policy_engine


def write_policy(tmp_path: Path, default_decision: str) -> Path:
    policy_file = tmp_path / "policy.yaml"
    policy_file.write_text(
        f"""
policy_version: policy.v2
default_decision: {default_decision}
rules: []
""".strip()
    )
    return policy_file


def test_default_decision_allow_is_configurable(tmp_path: Path) -> None:
    engine = PolicyEngine.from_file(write_policy(tmp_path, "allow"))

    result = engine.evaluate(ToolRequest(tool_name="unknown_tool"))

    assert result.decision == Decision.ALLOW
    assert result.allowed is True
    assert result.explanation is not None
    assert result.explanation.default_decision is True


def test_default_decision_block_is_configurable(tmp_path: Path) -> None:
    engine = PolicyEngine.from_file(write_policy(tmp_path, "block"))

    result = engine.evaluate(ToolRequest(tool_name="unknown_tool"))

    assert result.decision == Decision.BLOCK
    assert result.allowed is False
    assert result.explanation is not None
    assert result.explanation.default_decision is True


def test_default_decision_require_approval_is_configurable(tmp_path: Path) -> None:
    engine = PolicyEngine.from_file(write_policy(tmp_path, "require_approval"))

    result = engine.evaluate(ToolRequest(tool_name="unknown_tool"))

    assert result.decision == Decision.REQUIRE_APPROVAL
    assert result.allowed is False
    assert result.explanation is not None
    assert result.explanation.default_decision is True


def test_default_policy_blocks_unmatched_requests() -> None:
    engine = load_default_policy_engine()

    result = engine.evaluate(ToolRequest(tool_name="unknown_tool"))

    assert engine.default_decision == Decision.BLOCK
    assert result.decision == Decision.BLOCK
    assert result.allowed is False
    assert result.explanation is not None
    assert result.explanation.default_decision is True
