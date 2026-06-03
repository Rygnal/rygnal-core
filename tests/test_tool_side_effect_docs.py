from pathlib import Path


def test_tool_side_effect_doc_exists():
    assert Path("docs/tool-side-effects.md").exists()


def test_tool_side_effect_doc_documents_irreversible_actions():
    content = Path("docs/tool-side-effects.md").read_text()

    assert "Irreversible Side Effect" in content
    assert "prevention before execution" in content
    assert "does not yet provide a universal rollback system" in content


def test_tool_side_effect_doc_mentions_core_controls():
    content = Path("docs/tool-side-effects.md").read_text()

    required_terms = [
        "blocked",
        "simulated",
        "approval",
        "audit logging",
        "denied by default",
    ]

    for term in required_terms:
        assert term in content
