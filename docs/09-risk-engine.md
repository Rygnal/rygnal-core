# Risk Engine v1

Risk Engine v1 provides deterministic risk scoring for AI-agent tool requests.

## Purpose

The risk engine answers:

- How risky is this agent action?
- Why is it risky?
- Which signals contributed to the risk score?
- Is the action low, medium, high, or critical risk?

## Risk Score

Risk score range:

```text
0 to 100
```

A higher score means a more dangerous request.

## Risk Levels

- `low`: safe or routine actions with minimal risk.
- `medium`: non-critical operations with some sensitive data or business impact.
- `high`: risky actions such as file deletion, external data transfer, or database writes.
- `critical`: actions that likely expose secrets, run dangerous shell commands, or access environment secrets.

## Risk Signals

Risk Engine v1 generates explainable signals for:

- tool-level behavior, such as file deletion, shell execution, external API/data send, and database modification.
- target patterns, such as `.env`, secrets, credentials, private keys, or customer data.
- input patterns, such as API keys, tokens, passwords, `rm -rf`, `sudo`, `curl`, `wget`, and `chmod 777`.

Each signal includes:

- `code`: deterministic signal identifier.
- `severity`: risk level of the signal.
- `score`: numeric contribution to the final risk score.
- `reason`: human-readable explanation.

## Integration

The risk engine is designed to be integrated into the interceptor and audit pipeline later.
It is deterministic, typed, testable, and does not rely on LLM calls.

## Example

A safe `file_read` request on `README.md` returns low risk.
A request that targets `.env` or sends `api_key=` in input returns critical risk.
