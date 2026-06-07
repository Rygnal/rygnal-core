from pathlib import Path


def test_local_fastapi_service_doc_exists():
    assert Path("docs/33-local-fastapi-service.md").exists()


def test_local_fastapi_service_doc_mentions_endpoints_and_limits():
    content = Path("docs/33-local-fastapi-service.md").read_text()

    required_terms = [
        "GET /health",
        "POST /v1/evaluate",
        "does not execute tools",
        "authentication",
        "production SaaS API",
    ]

    for term in required_terms:
        assert term in content
