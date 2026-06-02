from demo.scenario_runner import ScenarioRunner
from rygnal.approval import ApprovalWorkflow
from rygnal.cli_approval import CLIApprovalResolver
from rygnal.models import ApprovalRequest, ApprovalStatus, ExecutionStatus


def make_request() -> ApprovalRequest:
    return ApprovalRequest(
        requested_by="demo_user",
        agent_id="demo_agent",
        environment="local",
        tool_name="file_delete",
        action="delete_file",
        target="customer_data.csv",
        policy_id="approval-file-delete",
        reason="File deletion requires human approval.",
        risk_assessment={"risk_score": 100, "risk_level": "critical"},
    )


def test_cli_approval_resolver_approves_yes_response():
    output: list[str] = []
    resolver = CLIApprovalResolver(
        approver="manish",
        timeout_seconds=None,
        input_func=lambda prompt: "yes",
        output_func=output.append,
    )

    decision = resolver(make_request())

    assert decision.status == ApprovalStatus.APPROVED
    assert decision.approved is True
    assert decision.decided_by == "manish"
    assert decision.reason == "Approved from CLI."
    assert any("Rygnal Approval Required" in line for line in output)


def test_cli_approval_resolver_rejects_no_response():
    resolver = CLIApprovalResolver(
        approver="reviewer",
        timeout_seconds=None,
        input_func=lambda prompt: "no",
        output_func=lambda message: None,
    )

    decision = resolver(make_request())

    assert decision.status == ApprovalStatus.REJECTED
    assert decision.approved is False
    assert decision.decided_by == "reviewer"
    assert decision.reason == "Rejected from CLI."


def test_cli_approval_resolver_rejects_empty_response():
    resolver = CLIApprovalResolver(
        timeout_seconds=None,
        input_func=lambda prompt: "",
        output_func=lambda message: None,
    )

    decision = resolver(make_request())

    assert decision.status == ApprovalStatus.REJECTED
    assert decision.approved is False


def test_scenario_runner_executes_approval_required_action_when_cli_approved(tmp_path):
    resolver = CLIApprovalResolver(
        approver="test_reviewer",
        timeout_seconds=None,
        input_func=lambda prompt: "y",
        output_func=lambda message: None,
    )

    runner = ScenarioRunner(
        sandbox_path=tmp_path / "sandbox",
        audit_log_path=tmp_path / "audit_log.jsonl",
        approval_workflow=ApprovalWorkflow(resolver=resolver),
    )

    outcomes = runner.run_all()
    outcome = next(item for item in outcomes if item.scenario.name == "file-delete-approval")

    assert outcome.result.approval_decision is not None
    assert outcome.result.approval_decision.status == ApprovalStatus.APPROVED
    assert outcome.result.execution.status == ExecutionStatus.EXECUTED
    assert outcome.result.execution.executed is True
    assert not (tmp_path / "sandbox" / "customer_data.csv").exists()


def test_scenario_runner_rejects_approval_required_action_by_default(tmp_path):
    runner = ScenarioRunner(
        sandbox_path=tmp_path / "sandbox",
        audit_log_path=tmp_path / "audit_log.jsonl",
    )

    outcomes = runner.run_all()
    outcome = next(item for item in outcomes if item.scenario.name == "file-delete-approval")

    assert outcome.result.approval_decision is not None
    assert outcome.result.approval_decision.status == ApprovalStatus.REJECTED
    assert outcome.result.execution.status == ExecutionStatus.SKIPPED
    assert outcome.result.execution.executed is False
    assert (tmp_path / "sandbox" / "customer_data.csv").exists()
