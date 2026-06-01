# Security Hardening v1

Security Hardening v1 strengthens Rygnal Core before v0.1 release.

## Improvements

- Centralized security helper module
- Stronger path traversal protection
- Secret detection helpers
- Secret redaction helpers
- Shell command allowlist validation
- Shell metacharacter blocking
- HTTPS-only outbound URL validation
- HTTP host allowlist validation
- Local/private network destination blocking
- Audit metadata redaction

## Safety Rules

- Tool adapters must never access files outside the sandbox
- Shell commands must use an allowlist
- Shell metacharacters are rejected
- External sends are dry-run only in v1
- Secret-looking payloads are blocked or redacted
- Audit logs must not store raw secrets

## Validation

Run:

```bash
ruff format src tests demo
ruff check src tests demo
pytest -q
bandit -r src demo -c pyproject.toml
pip-audit -r requirements-dev.txt
python -m demo.run_demo
```
