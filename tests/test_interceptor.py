from rygnal.audit_logger import AuditLogger
from rygnal.interceptor import RygnalInterceptor
from rygnal.models import Decision, ExecutionStatus, ToolRequest
from rygnal.policy_engine import load_default_policy_engine
from rygnal.risk_engine import RiskEngine
from rygnal.tool_executor import ToolExecutor


def build_test_interceptor(tmp_path):
    executor = ToolExecutor()
    logger = AuditLogger(tmp_path / "audit_log.jsonl")

    return RygnalInterceptor(
        policy_engine=load_default_policy_engine(),
        audit_logger=logger,
        tool_executor=executor,
        risk_engine=RiskEngine(),
    )


def test_interceptor_executes_allowed_tool(tmp_path):
    interceptor = build_test_interceptor(tmp_path)

    def safe_read(request: ToolRequest) -> dict[str, str]:
        return {"target": request.target or "", "content": "safe"}

    interceptor.tool_executor.register("file_read", safe_read)

    result = interceptor.intercept(
        ToolRequest(tool_name="file_read", action="read_file", target="README.md")
    )

    assert result.policy_decision.decision == Decision.ALLOW
    assert result.execution.status == ExecutionStatus.EXECUTED
    assert result.execution.executed is True
    assert result.execution.output == {"target": "README.md", "content": "safe"}
    assert result.risk_assessment["risk_score"] < 30
    assert result.risk_assessment["risk_level"] == "low"
    assert result.audit_event.metadata["risk_level"] == "low"


def test_interceptor_blocks_risky_tool_before_execution(tmp_path):
    interceptor = build_test_interceptor(tmp_path)
    called = {"value": False}

    def unsafe_read(request: ToolRequest) -> dict[str, str]:
        called["value"] = True
        return {"target": request.target or ""}

    interceptor.tool_executor.register("file_read", unsafe_read)

    result = interceptor.intercept(
        ToolRequest(tool_name="file_read", action="read_file", target=".env")
    )

    assert result.policy_decision.decision == Decision.BLOCK
    assert result.execution.status == ExecutionStatus.SKIPPED
    assert result.execution.executed is False
    assert called["value"] is False
    assert result.risk_assessment["risk_level"] == "critical"
    assert result.audit_event.metadata["risk_score"] >= 85


def test_interceptor_requires_approval_without_execution(tmp_path):
    interceptor = build_test_interceptor(tmp_path)
    called = {"value": False}

    def delete_file(request: ToolRequest) -> dict[str, str]:
        called["value"] = True
        return {"deleted": request.target or ""}

    interceptor.tool_executor.register("file_delete", delete_file)

    result = interceptor.intercept(
        ToolRequest(tool_name="file_delete", action="delete_file", target="customer_data.csv")
    )

    assert result.policy_decision.decision == Decision.REQUIRE_APPROVAL
    assert result.execution.status == ExecutionStatus.SKIPPED
    assert result.execution.executed is False
    assert called["value"] is False
    assert result.risk_assessment["risk_score"] >= 60
    assert result.audit_event.metadata["risk_level"] in {"high", "critical"}


def test_interceptor_simulates_without_execution(tmp_path):
    interceptor = build_test_interceptor(tmp_path)
    called = {"value": False}

    def external_send(request: ToolRequest) -> dict[str, str]:
        called["value"] = True
        return {"sent": "true"}

    interceptor.tool_executor.register("external_api_send", external_send)

    result = interceptor.intercept(
        ToolRequest(tool_name="external_api_send", action="send_data", input={"payload": "demo"})
    )

    assert result.policy_decision.decision == Decision.SIMULATE
    assert result.execution.status == ExecutionStatus.SIMULATED
    assert result.execution.executed is False
    assert called["value"] is False
    assert result.risk_assessment["risk_score"] >= 60
    assert result.audit_event.metadata["risk_level"] in {"high", "critical"}


def test_interceptor_writes_audit_event(tmp_path):
    interceptor = build_test_interceptor(tmp_path)

    result = interceptor.intercept(
        ToolRequest(tool_name="file_read", action="read_file", target=".env")
    )

    events = interceptor.audit_logger.read_events()

    assert len(events) == 1
    assert events[0].event_id == result.audit_event.event_id
    assert events[0].decision == Decision.BLOCK
    assert events[0].event_hash
    assert events[0].metadata["risk_score"] == result.risk_assessment["risk_score"]
    assert events[0].metadata["risk_level"] == result.risk_assessment["risk_level"]
    assert interceptor.audit_logger.verify_integrity() is True


def test_unmatched_unregistered_tool_is_blocked_by_default_policy(tmp_path):
    interceptor = build_test_interceptor(tmp_path)

    result = interceptor.intercept(
        ToolRequest(tool_name="unknown_safe_tool", action="noop", target="demo")
    )

    assert result.policy_decision.decision == Decision.BLOCK
    assert result.policy_decision.policy_id is None
    assert result.execution.status == ExecutionStatus.SKIPPED
    assert result.execution.executed is False
