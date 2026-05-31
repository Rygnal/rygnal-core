from demo.scenario_runner import ScenarioRunner
from rygnal.models import Decision, ExecutionStatus


def test_real_scenario_runner_executes_all_workflows(tmp_path):
    runner = ScenarioRunner(
        sandbox_path=tmp_path / "sandbox",
        audit_log_path=tmp_path / "audit_log.jsonl",
    )

    outcomes = runner.run_all()

    assert len(outcomes) == 7

    scenario_names = {outcome.scenario.name for outcome in outcomes}
    assert "safe-file-read" in scenario_names
    assert "secret-file-access" in scenario_names
    assert "file-delete-approval" in scenario_names
    assert "safe-shell-command" in scenario_names
    assert "dangerous-shell-command" in scenario_names
    assert "external-secret-send" in scenario_names
    assert "safe-file-write" in scenario_names


def test_blocked_secret_file_access_never_executes(tmp_path):
    runner = ScenarioRunner(
        sandbox_path=tmp_path / "sandbox",
        audit_log_path=tmp_path / "audit_log.jsonl",
    )

    outcomes = runner.run_all()
    outcome = next(item for item in outcomes if item.scenario.name == "secret-file-access")

    assert outcome.result.policy_decision.decision == Decision.BLOCK
    assert outcome.result.execution.status == ExecutionStatus.SKIPPED
    assert outcome.result.execution.executed is False


def test_approval_required_file_delete_never_executes(tmp_path):
    runner = ScenarioRunner(
        sandbox_path=tmp_path / "sandbox",
        audit_log_path=tmp_path / "audit_log.jsonl",
    )

    outcomes = runner.run_all()
    outcome = next(item for item in outcomes if item.scenario.name == "file-delete-approval")

    customer_file = tmp_path / "sandbox" / "customer_data.csv"

    assert outcome.result.policy_decision.decision == Decision.REQUIRE_APPROVAL
    assert outcome.result.execution.status == ExecutionStatus.SKIPPED
    assert outcome.result.execution.executed is False
    assert customer_file.exists()


def test_dangerous_shell_command_never_executes(tmp_path):
    runner = ScenarioRunner(
        sandbox_path=tmp_path / "sandbox",
        audit_log_path=tmp_path / "audit_log.jsonl",
    )

    outcomes = runner.run_all()
    outcome = next(item for item in outcomes if item.scenario.name == "dangerous-shell-command")

    assert outcome.result.policy_decision.decision == Decision.BLOCK
    assert outcome.result.execution.status == ExecutionStatus.SKIPPED
    assert outcome.result.execution.executed is False


def test_safe_workflows_execute(tmp_path):
    runner = ScenarioRunner(
        sandbox_path=tmp_path / "sandbox",
        audit_log_path=tmp_path / "audit_log.jsonl",
    )

    outcomes = runner.run_all()

    safe_read = next(item for item in outcomes if item.scenario.name == "safe-file-read")
    safe_shell = next(item for item in outcomes if item.scenario.name == "safe-shell-command")
    safe_write = next(item for item in outcomes if item.scenario.name == "safe-file-write")

    assert safe_read.result.policy_decision.decision == Decision.ALLOW
    assert safe_read.result.execution.status == ExecutionStatus.EXECUTED

    assert safe_shell.result.policy_decision.decision == Decision.ALLOW
    assert safe_shell.result.execution.status == ExecutionStatus.EXECUTED

    assert safe_write.result.policy_decision.decision == Decision.ALLOW
    assert safe_write.result.execution.status == ExecutionStatus.EXECUTED


def test_external_secret_send_is_simulated_not_transmitted(tmp_path):
    runner = ScenarioRunner(
        sandbox_path=tmp_path / "sandbox",
        audit_log_path=tmp_path / "audit_log.jsonl",
    )

    outcomes = runner.run_all()
    outcome = next(item for item in outcomes if item.scenario.name == "external-secret-send")

    assert outcome.result.policy_decision.decision == Decision.SIMULATE
    assert outcome.result.execution.status == ExecutionStatus.SIMULATED
    assert outcome.result.execution.executed is False


def test_audit_log_created_for_every_scenario(tmp_path):
    audit_log_path = tmp_path / "audit_log.jsonl"
    runner = ScenarioRunner(
        sandbox_path=tmp_path / "sandbox",
        audit_log_path=audit_log_path,
    )

    outcomes = runner.run_all()
    lines = audit_log_path.read_text().splitlines()

    assert len(lines) == len(outcomes)
    assert runner.build_interceptor().audit_logger.verify_integrity() is True
