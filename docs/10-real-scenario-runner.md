# Real Scenario Runner v1

The Real Scenario Runner executes controlled workflow scenarios through Rygnal Core.

## Purpose

It proves the core runtime flow:

```text
Tool request
→ Risk assessment
→ Policy decision
→ Audit logging
→ Safe execution or block
```

## Scenarios

- Safe file read
- Secret `.env` file access
- File deletion approval
- Safe shell command
- Dangerous shell command
- External secret send
- Safe file write

## Safety Rules

- File actions are restricted to `demo_sandbox/`
- Dangerous shell commands are blocked before execution
- Shell execution uses an allowlist
- External send is dry-run only in v1
- Every scenario creates an audit event

## Run

```bash
python demo/run_demo.py
```
