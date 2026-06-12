import json

from demo.scenario_runner import ScenarioRunner


def test_audit_metadata_includes_policy_explanation_for_matched_rule(tmp_path):
    audit_log_path = tmp_path / "audit_log.jsonl"

    runner = ScenarioRunner(
        sandbox_path=tmp_path / "sandbox",
        audit_log_path=audit_log_path,
    )

    outcomes = runner.run_all()
    outcome = next(item for item in outcomes if item.scenario.name == "secret-file-access")

    saved_events = [json.loads(line) for line in audit_log_path.read_text().splitlines()]
    saved_event = next(
        event for event in saved_events if event["event_id"] == outcome.result.audit_event.event_id
    )

    explanation = saved_event["metadata"]["policy_explanation"]

    assert explanation["policy_version"] == "policy.v2"
    assert explanation["matched"] is True
    assert explanation["matched_rule_id"] == "block-env-read"
    assert explanation["matched_rule_priority"] == 10
    assert "tool_name" in explanation["matched_conditions"]
    assert "target_contains" in explanation["matched_conditions"]
    assert explanation["default_decision"] is False


def test_audit_metadata_includes_policy_explanation_for_explicit_safe_read_allow(tmp_path):
    audit_log_path = tmp_path / "audit_log.jsonl"

    runner = ScenarioRunner(
        sandbox_path=tmp_path / "sandbox",
        audit_log_path=audit_log_path,
    )

    outcomes = runner.run_all()
    outcome = next(item for item in outcomes if item.scenario.name == "safe-file-read")

    saved_events = [json.loads(line) for line in audit_log_path.read_text().splitlines()]
    saved_event = next(
        event for event in saved_events if event["event_id"] == outcome.result.audit_event.event_id
    )

    explanation = saved_event["metadata"]["policy_explanation"]

    assert explanation["policy_version"] == "policy.v2"
    assert explanation["matched"] is True
    assert explanation["matched_rule_id"] == "allow-readme-read"
    assert explanation["matched_rule_priority"] == 50
    assert "target_matches" in explanation["matched_conditions"]
    assert "target_not_matches" in explanation["matched_conditions"]
    assert explanation["default_decision"] is False
