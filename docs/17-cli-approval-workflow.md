# CLI Approval Workflow v1

CLI Approval Workflow v1 adds a real local human-in-the-loop approval path for approval-required actions.

## Goal

When policy returns require_approval, Rygnal can ask a human in the terminal before executing the action.

## Default Safety

By default, approval-required actions are rejected if no approval resolver is configured.

This keeps Rygnal safe in non-interactive demos and CI.

## Run Default Demo

python -m demo.run_demo

Default mode rejects approval-required actions automatically.

## Run Interactive CLI Approval Demo

python -m demo.run_demo --approval-mode cli --approver manish

When the file deletion scenario runs, Rygnal asks:

Approve this action? [y/N]:

## Approval Behavior

- y, yes, approve, approved means approve
- anything else means reject
- timeout or interruption rejects by default

## Audit Metadata

Approval decisions are stored in audit metadata:

- approval ID
- status
- approved/rejected
- decided by
- decided at
- reason

## Security Notes

CLI approval is local-first and v1-level.

It is not yet:

- approval UI
- approval API
- approval queue
- team approval
- role-based approval
