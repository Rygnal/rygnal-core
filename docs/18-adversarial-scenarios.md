# Adversarial Scenario Tests v1

Adversarial Scenario Tests v1 adds security-focused edge-case tests for realistic malicious or unexpected AI-agent behavior.

## Goal

Reduce false confidence by testing more than obvious safe and unsafe paths.

## Covered Scenarios

- Nested path traversal
- Absolute path escape attempts
- Secret-like backup file access attempts
- Nested secret payloads
- Secret values hidden inside lists
- Shell command chaining
- Shell pipe exfiltration attempts
- Unallowlisted shell commands
- Cloud metadata IP access
- Private/local network destination blocking
- Hidden secret payload exfiltration attempts

## Important Finding

This test suite exposed a real weakness: nested secret payloads were not blocked during file write operations.

The file write tool now checks the raw input payload before converting it to a string.

## Security Value

These tests make Rygnal safer by checking agent behavior that may try to bypass simple rules.

## Validation

Run pytest -q tests/test_adversarial_scenarios.py and pytest -q.
