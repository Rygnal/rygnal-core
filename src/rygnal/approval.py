"""Approval workflow for Rygnal.

Approval Workflow v1 handles actions that require human approval before execution.
"""

from collections.abc import Callable, Mapping
from typing import Any

from rygnal.models import (
    ApprovalDecision,
    ApprovalRequest,
    ApprovalStatus,
    PolicyDecision,
    ToolRequest,
    new_trace_id,
    utc_now_iso,
)
from rygnal.security import redact_sensitive_value

ApprovalResolver = Callable[[ApprovalRequest], ApprovalDecision]

DENIED_APPROVER_ROLES = frozenset({"viewer"})


class ApprovalWorkflow:
    """Create approval requests and resolve approve/reject decisions."""

    def __init__(
        self,
        resolver: ApprovalResolver | None = None,
        reviewer_roles: Mapping[str, str] | None = None,
    ) -> None:
        self.resolver = resolver or reject_by_default
        self.reviewer_roles = dict(reviewer_roles or {})

    def request_approval(
        self,
        request: ToolRequest,
        policy_decision: PolicyDecision,
        risk_assessment: dict[str, Any] | None = None,
    ) -> tuple[ApprovalRequest, ApprovalDecision]:
        """Create an approval request and return the approval decision."""
        approval_request = ApprovalRequest(
            trace_id=str(request.metadata.get("trace_id") or new_trace_id()),
            requested_by=request.user_id,
            agent_id=request.agent_id,
            environment=request.environment,
            tool_name=request.tool_name,
            action=request.action,
            target=request.target,
            policy_id=policy_decision.policy_id,
            reason=policy_decision.reason,
            risk_assessment=_redacted_mapping(risk_assessment),
            metadata=_redacted_mapping(request.metadata),
        )

        approval_decision = self.resolver(approval_request)

        if approval_decision.approval_id != approval_request.approval_id:
            raise ValueError("Approval decision ID does not match approval request ID.")

        approval_decision = _enforce_self_approval_guard(
            approval_request,
            approval_decision,
        )
        approval_decision = _enforce_reviewer_role_guard(
            approval_decision,
            self.reviewer_roles,
        )

        return approval_request, approval_decision


def reject_by_default(approval_request: ApprovalRequest) -> ApprovalDecision:
    """Safe default resolver when no human approval system is configured."""
    return ApprovalDecision(
        approval_id=approval_request.approval_id,
        status=ApprovalStatus.REJECTED,
        approved=False,
        decided_by="system",
        decided_at=utc_now_iso(),
        reason="Approval workflow is not configured. Request rejected by default.",
    )


def approve_for_testing(
    approval_request: ApprovalRequest,
    decided_by: str = "test_reviewer",
    reason: str = "Approved for controlled test execution.",
) -> ApprovalDecision:
    """Approve an action for deterministic tests or controlled local workflows."""
    return ApprovalDecision(
        approval_id=approval_request.approval_id,
        status=ApprovalStatus.APPROVED,
        approved=True,
        decided_by=decided_by,
        decided_at=utc_now_iso(),
        reason=reason,
    )


def reject_for_testing(
    approval_request: ApprovalRequest,
    decided_by: str = "test_reviewer",
    reason: str = "Rejected for controlled test execution.",
) -> ApprovalDecision:
    """Reject an action for deterministic tests or controlled local workflows."""
    return ApprovalDecision(
        approval_id=approval_request.approval_id,
        status=ApprovalStatus.REJECTED,
        approved=False,
        decided_by=decided_by,
        decided_at=utc_now_iso(),
        reason=reason,
    )


def _enforce_self_approval_guard(
    approval_request: ApprovalRequest,
    approval_decision: ApprovalDecision,
) -> ApprovalDecision:
    """Reject approvals where the requester approves their own action."""
    if not approval_decision.approved:
        return approval_decision

    if approval_decision.decided_by != approval_request.requested_by:
        return approval_decision

    return ApprovalDecision(
        approval_id=approval_request.approval_id,
        status=ApprovalStatus.REJECTED,
        approved=False,
        decided_by="system",
        decided_at=utc_now_iso(),
        reason=("Self-approval rejected: requester cannot approve their own approval request."),
        metadata={
            **approval_decision.metadata,
            "guard": "self-approval",
            "attempted_decided_by": approval_decision.decided_by,
        },
    )


def _enforce_reviewer_role_guard(
    approval_decision: ApprovalDecision,
    reviewer_roles: Mapping[str, str],
) -> ApprovalDecision:
    """Reject approvals from roles that are not allowed to approve."""
    if not approval_decision.approved:
        return approval_decision

    if approval_decision.decided_by is None:
        return approval_decision

    reviewer_role = reviewer_roles.get(approval_decision.decided_by)

    if reviewer_role is None:
        return approval_decision

    normalized_role = reviewer_role.strip().lower()

    if normalized_role not in DENIED_APPROVER_ROLES:
        return approval_decision

    return ApprovalDecision(
        approval_id=approval_decision.approval_id,
        status=ApprovalStatus.REJECTED,
        approved=False,
        decided_by="system",
        decided_at=utc_now_iso(),
        reason=(
            f"Viewer-role approval rejected: reviewer role '{reviewer_role}' "
            "cannot approve protected actions."
        ),
        metadata={
            **approval_decision.metadata,
            "guard": "viewer-role",
            "attempted_decided_by": approval_decision.decided_by,
            "reviewer_role": reviewer_role,
        },
    )


def _redacted_mapping(value: dict[str, Any] | None) -> dict[str, Any]:
    """Return a safely redacted metadata mapping for approval context."""
    redacted_value = redact_sensitive_value(value or {})

    if not isinstance(redacted_value, dict):
        return {}

    return redacted_value
