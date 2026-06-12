from pathlib import Path

from rygnal.audit_logger import AuditLogger
from rygnal.interceptor import RygnalInterceptor
from rygnal.models import Decision, ExecutionStatus, RuntimeMode, ToolRequest
from rygnal.policy_engine import load_default_policy_engine
from rygnal.risk_engine import RiskEngine
from rygnal.tool_executor import ToolExecutor


def build_interceptor(tmp_path: Path) -> RygnalInterceptor:
    executor = ToolExecutor()
    executor.register(
        "file_read",
        lambda request: {"target": request.target, "content": "safe"},
    )

    return RygnalInterceptor(
        policy_engine=load_default_policy_engine(RuntimeMode.PRODUCTION_SAFE),
        audit_logger=AuditLogger(tmp_path / "audit_log.jsonl"),
        tool_executor=executor,
        risk_engine=RiskEngine(),
        runtime_mode=RuntimeMode.PRODUCTION_SAFE,
    )


def test_load_default_policy_engine_uses_production_safe_policy() -> None:
    engine = load_default_policy_engine(RuntimeMode.PRODUCTION_SAFE)

    assert engine.default_decision == Decision.REQUIRE_APPROVAL


def test_production_safe_policy_blocks_critical_risk(tmp_path: Path) -> None:
    interceptor = build_interceptor(tmp_path)

    result = interceptor.intercept(
        ToolRequest(tool_name="file_read", action="read_file", target=".env")
    )

    assert result.risk_assessment["risk_level"] == "critical"
    assert result.policy_decision.decision == Decision.BLOCK
    assert result.policy_decision.policy_id == "block-critical-risk"
    assert result.execution.status == ExecutionStatus.SKIPPED


def test_production_safe_policy_requires_approval_for_unmatched_safe_read(tmp_path: Path) -> None:
    interceptor = build_interceptor(tmp_path)

    result = interceptor.intercept(
        ToolRequest(tool_name="file_read", action="read_file", target="README.md")
    )

    assert result.policy_decision.decision == Decision.REQUIRE_APPROVAL
    assert result.policy_decision.policy_id is None
    assert result.policy_decision.explanation is not None
    assert result.policy_decision.explanation.default_decision is True
    assert result.execution.status == ExecutionStatus.SKIPPED


def test_existing_default_policy_remains_local_dev_compatible() -> None:
    engine = load_default_policy_engine()

    result = engine.evaluate(
        ToolRequest(tool_name="file_read", action="read_file", target="README.md")
    )

    assert result.decision == Decision.ALLOW
    assert result.allowed is True
