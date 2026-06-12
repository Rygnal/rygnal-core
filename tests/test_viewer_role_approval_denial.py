from pathlib import Path

from rygnal import Rygnal
from rygnal.approval import ApprovalWorkflow
from rygnal.models import (
    ApprovalDecision,
    ApprovalStatus,
    ExecutionStatus,
    ToolRequest,
    utc_now_iso,
)


def test_viewer_role_cannot_approve_risky_action(tmp_path: Path) -> None:
    audit_log_path = tmp_path / "audit.jsonl"

    def viewer_approving_resolver(approval_request):
        return ApprovalDecision(
            approval_id=approval_request.approval_id,
            status=ApprovalStatus.APPROVED,
            approved=True,
            decided_by="readonly_reviewer",
            decided_at=utc_now_iso(),
            reason="Viewer attempted to approve a protected action.",
        )

    rygnal = Rygnal(
        audit_log_path=audit_log_path,
        approval_workflow=ApprovalWorkflow(
            resolver=viewer_approving_resolver,
            reviewer_roles={"readonly_reviewer": "viewer"},
        ),
    )

    executed = {"value": False}

    def dangerous_delete(_request):
        executed["value"] = True
        return {"deleted": True}

    rygnal.register_tool("file_delete", dangerous_delete)

    result = rygnal.intercept(
        ToolRequest(
            tool_name="file_delete",
            action="delete_file",
            target="customer-data.csv",
            user_id="demo_user",
            agent_id="demo_agent",
            environment="local",
        )
    )

    assert result.approval_decision is not None
    assert result.approval_decision.status == ApprovalStatus.REJECTED
    assert result.approval_decision.approved is False
    assert result.approval_decision.decided_by == "system"
    assert "viewer" in result.approval_decision.reason.lower()
    assert "cannot approve" in result.approval_decision.reason.lower()

    assert result.execution.status == ExecutionStatus.SKIPPED
    assert result.execution.executed is False
    assert executed["value"] is False

    audit_log = audit_log_path.read_text()
    assert "viewer-role" in audit_log.lower()
    assert "readonly_reviewer" in audit_log
    assert "rejected" in audit_log.lower()
