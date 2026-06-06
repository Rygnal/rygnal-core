from pathlib import Path


def test_rygnal_cli_doc_exists():
    assert Path("docs/26-rygnal-cli-v1.md").exists()


def test_rygnal_cli_doc_mentions_core_commands():
    content = Path("docs/26-rygnal-cli-v1.md").read_text()

    required_terms = [
        "rygnal --help",
        "rygnal version",
        "rygnal demo run",
        "rygnal policy validate",
    ]

    for term in required_terms:
        assert term in content
