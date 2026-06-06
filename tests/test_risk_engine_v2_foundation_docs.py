from pathlib import Path


def test_risk_engine_v2_foundation_doc_exists():
    assert Path("docs/28-risk-engine-v2-foundation.md").exists()


def test_risk_engine_v2_foundation_doc_mentions_core_components():
    content = Path("docs/28-risk-engine-v2-foundation.md").read_text()

    required_terms = [
        "RiskContext",
        "RiskSignalCategory",
        "RiskScoringProfile",
        "RiskSignalRegistry",
        "confidence",
        "explanation",
    ]

    for term in required_terms:
        assert term in content


def test_risk_engine_v2_foundation_doc_states_not_included_yet():
    content = Path("docs/28-risk-engine-v2-foundation.md").read_text()

    assert "Chain-risk detection" in content
    assert "Policy-risk bridge" in content
    assert "Rust implementation" in content
