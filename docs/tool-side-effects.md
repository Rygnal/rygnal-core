# Tool Side Effects and Rollback Model

Rygnal controls AI-agent tool actions before execution. Some tool actions are reversible, but some are irreversible.

## Goal

Document how Rygnal treats tool actions that may create permanent or hard-to-rollback side effects.

## Why This Matters

AI agents can request actions such as deleting files, sending data externally, running shell commands, or modifying databases.

Some of these actions cannot be safely undone after execution.

## Side-Effect Categories

### Low Side Effect

- Reading safe documentation
- Listing files inside a sandbox
- Running safe read-only commands

### Medium Side Effect

- Writing files inside a sandbox
- Reading customer or business data
- Running commands with limited local impact

### High Side Effect

- Deleting files
- Modifying databases
- Sending data to external services
- Running shell commands that change system state

### Irreversible Side Effect

- Exfiltrating secrets
- Sending private data externally
- Deleting production data
- Triggering third-party APIs
- Running destructive shell commands

## Current Rygnal Behavior

- Safe actions may be allowed
- Dangerous actions may be blocked
- External data sends may be simulated
- File deletion requires approval
- Shell commands are allowlisted
- Audit events are always recorded

## Rollback Reality

Rygnal should not claim that every action can be rolled back.

For irreversible actions, the correct control is prevention before execution, not rollback after execution.

## Recommended Policy

- Read-only actions can be allowed with audit logging
- Write actions should be sandboxed or require policy review
- Delete actions should require approval
- External sends should be simulated or require approval
- Production-impacting actions should be denied by default

## Future Improvements

- Side-effect classification per tool
- Policy rules based on side-effect level
- Approval requirement for high side-effect actions
- Dry-run support for risky tools
- Rollback hooks where possible
- Stronger audit records for irreversible actions

## Current Limitation

Rygnal Core does not yet provide a universal rollback system.

The current safety model focuses on pre-execution control, simulation, approval, and audit logging.
