# Policy Explain Output in CLI and Audit

This feature exposes Policy Explain Output in developer-facing CLI output and audit metadata.

## Goal

Make policy decisions easier to debug, demo, and audit.

## What Is Exposed

- Matched policy rule ID
- Matched rule priority
- Matched conditions
- Default allow decision flag
- Evaluated policy rule IDs in audit metadata

## CLI Output

The scenario runner output now shows policy explanation fields:

- Policy
- Priority
- Matched
- Conditions
- Default

## Audit Metadata

Audit events now include policy_explanation metadata when a policy decision is made.

This makes audit review more useful because the audit record explains why the policy decision happened.

## Behavior

- Matched rules show priority and matched condition names
- Default allow decisions are clearly marked
- Enforcement behavior is not changed
- Existing risk metadata remains backward compatible

## Security Value

This improves trust, debugging, and auditability without changing allow/block behavior.
