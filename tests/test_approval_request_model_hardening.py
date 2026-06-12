import pytest
from pydantic import ValidationError

from rygnal.approval import ApprovalWorkflow
from rygnal.models import ApprovalRequest, Decision, PolicyDecision, Severity, ToolRequest


def test_approval_request_rejects_missing_required_context() -> None:
    with pytest.raises(ValidationError):
        ApprovalRequest(
            requested_by="",
            agent_id="demo_agent",
            environment="local",
            tool_name="file_delete",
            reason="Requires human approval.",
        )

    with pytest.raises(ValidationError):
        ApprovalRequest(
            requested_by="demo_user",
            agent_id="",
            environment="local",
            tool_name="file_delete",
            reason="Requires human approval.",
        )

    with pytest.raises(ValidationError):
        ApprovalRequest(
            requested_by="demo_user",
            agent_id="demo_agent",
            environment="",
            tool_name="file_delete",
            reason="Requires human approval.",
        )


def test_approval_workflow_redacts_sensitive_metadata_from_request() -> None:
    captured: dict[str, ApprovalRequest] = {}

    def capture_request(approval_request: ApprovalRequest):
        captured["approval_request"] = approval_request
        from rygnal.approval import reject_by_default

        return reject_by_default(approval_request)

    workflow = ApprovalWorkflow(resolver=capture_request)

    request = ToolRequest(
        tool_name="file_delete",
        action="delete_file",
        target="customer-data.csv",
        metadata={
            "trace_id": "trace_safe",
            "token": "secret-token-value",
            "api_key": "secret-api-key",
            "nested": {
                "password": "secret-password",
                "safe": "visible",
            },
        },
    )
    policy_decision = PolicyDecision(
        decision=Decision.REQUIRE_APPROVAL,
        allowed=False,
        severity=Severity.HIGH,
        reason="Deleting files requires approval.",
        policy_id="require-delete-approval",
    )

    workflow.request_approval(request, policy_decision)

    approval_request = captured["approval_request"]

    assert approval_request.trace_id == "trace_safe"
    assert approval_request.metadata["token"] == "[REDACTED]"
    assert approval_request.metadata["api_key"] == "[REDACTED]"
    assert approval_request.metadata["nested"]["password"] == "[REDACTED]"
    assert approval_request.metadata["nested"]["safe"] == "visible"


def test_approval_workflow_redacts_sensitive_risk_metadata() -> None:
    captured: dict[str, ApprovalRequest] = {}

    def capture_request(approval_request: ApprovalRequest):
        captured["approval_request"] = approval_request
        from rygnal.approval import reject_by_default

        return reject_by_default(approval_request)

    workflow = ApprovalWorkflow(resolver=capture_request)

    request = ToolRequest(
        tool_name="file_delete",
        action="delete_file",
        target="customer-data.csv",
    )
    policy_decision = PolicyDecision(
        decision=Decision.REQUIRE_APPROVAL,
        allowed=False,
        severity=Severity.HIGH,
        reason="Deleting files requires approval.",
        policy_id="require-delete-approval",
    )

    workflow.request_approval(
        request,
        policy_decision,
        risk_assessment={
            "risk_level": "high",
            "evidence": {
                "authorization": "Bearer secret-token-value",
                "safe": "visible",
            },
        },
    )

    approval_request = captured["approval_request"]

    assert approval_request.risk_assessment["risk_level"] == "high"
    assert approval_request.risk_assessment["evidence"]["authorization"] == "[REDACTED]"
    assert approval_request.risk_assessment["evidence"]["safe"] == "visible"
