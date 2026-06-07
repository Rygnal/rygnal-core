from pathlib import Path


def test_optional_live_openai_demo_doc_exists():
    assert Path("docs/39-optional-live-openai-demo.md").exists()


def test_optional_live_openai_demo_doc_mentions_safety_rules():
    content = Path("docs/39-optional-live-openai-demo.md").read_text()

    required_terms = [
        "CI must not require a live OpenAI API call",
        "OPENAI_API_KEY",
        "Tool calls must still pass through Rygnal",
        "Audit logs must still be generated",
    ]

    for term in required_terms:
        assert term in content


def test_optional_live_openai_demo_doc_mentions_run_command():
    content = Path("docs/39-optional-live-openai-demo.md").read_text()

    required_terms = [
        'pip install -e ".[live-openai]"',
        "python -m examples.live_openai_demo",
        "OPENAI_MODEL",
    ]

    for term in required_terms:
        assert term in content
