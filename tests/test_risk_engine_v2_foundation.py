from rygnal.models import ToolRequest
from rygnal.risk_engine import (
    RiskContext,
    RiskEngine,
    RiskLevel,
    RiskScoringProfile,
    RiskSignalCategory,
    RiskSignalRegistry,
)


def test_risk_context_normalizes_tool_request():
    request = ToolRequest(
        tool_name="Shell_Command",
        action="execute",
        target="Customer_Data.csv",
        input={"command": "echo hello"},
        environment="production",
        metadata={"source": "test"},
    )

    context = RiskContext.from_request(request)

    assert context.tool_name == "Shell_Command"
    assert context.tool_name_normalized == "shell_command"
    assert context.target_text == "customer_data.csv"
    assert "echo hello" in context.input_text
    assert context.metadata == {"source": "test"}


def test_default_signal_registry_detects_structured_signals():
    context = RiskContext.from_request(
        ToolRequest(tool_name="file_delete", action="delete_file", target="customer_data.csv")
    )

    signals = RiskSignalRegistry.default().detect(context)

    assert any(signal.code == "file-delete" for signal in signals)
    assert any(signal.code == "sensitive-business-data" for signal in signals)
    assert all(signal.category for signal in signals)
    assert all(signal.reason for signal in signals)


def test_risk_assessment_includes_v2_explanation_and_confidence():
    assessment = RiskEngine().assess(
        ToolRequest(tool_name="shell_command", action="execute", input="rm -rf /tmp/demo")
    )

    assert assessment.risk_level == RiskLevel.CRITICAL
    assert assessment.confidence > 0
    assert "Risk score" in assessment.explanation
    assert "dangerous-shell-pattern" in assessment.explanation
    assert any(signal.category == RiskSignalCategory.COMMAND for signal in assessment.signals)


def test_risk_scoring_profile_can_be_configured():
    engine = RiskEngine(scoring_profile=RiskScoringProfile(critical_threshold=70))

    assessment = engine.assess(
        ToolRequest(tool_name="file_delete", action="delete_file", target="demo.txt")
    )

    assert assessment.risk_score >= 70
    assert assessment.risk_level == RiskLevel.CRITICAL


def test_production_environment_adds_environment_signal():
    assessment = RiskEngine().assess(
        ToolRequest(
            tool_name="file_read",
            action="read_file",
            target="README.md",
            environment="production",
        )
    )

    assert any(signal.code == "production-environment" for signal in assessment.signals)
    assert any(signal.category == RiskSignalCategory.ENVIRONMENT for signal in assessment.signals)
