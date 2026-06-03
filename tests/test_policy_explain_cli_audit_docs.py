from pathlib import Path


def test_policy_explain_cli_audit_doc_exists():
    assert Path("docs/25-policy-explain-cli-audit.md").exists()


def test_policy_explain_cli_audit_doc_mentions_cli_and_audit_fields():
    content = Path("docs/25-policy-explain-cli-audit.md").read_text()

    required_terms = [
        "Priority",
        "Matched",
        "Conditions",
        "Default",
        "policy_explanation",
        "audit metadata",
    ]

    for term in required_terms:
        assert term in content
