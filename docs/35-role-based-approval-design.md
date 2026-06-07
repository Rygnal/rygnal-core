# Role-Based Approval Design

## Goal

Design who is allowed to approve risky AI-agent actions in Rygnal.

This is design-only. It does not implement runtime RBAC, approval APIs, or storage.

## Final Decisions

| Area | Decision |
|---|---|
| Secret access | Default block in default_policy.yaml, not hardcoded in engine |
| Roles file | policies/roles.yaml |
| Access model | RBAC first, ABAC later |
| MVP roles | viewer, developer, security_reviewer, admin, owner |
| Self approval | Hard invariant: requester cannot approve own request |
| Environment | Role permissions include environment from day one |
| Reviewer role | Store reviewer role at decision time |
| Multi approval | Single approval now, model for multi-approval later |

## File Layout

policies/default_policy.yaml is loaded by PolicyEngine.

policies/roles.yaml should be loaded by a future ApprovalAuthorizationEngine.

Policy rules decide what should happen to an agent action.

Role rules decide who can approve an action that already requires approval.

## roles.yaml Direction

Future RolePermission shape:

- role: str
- allowed_severities: list[str]
- allowed_actions: list[str] | None
- environments: list[str] | None

Environment semantics:

- environments: null means all environments
- environments: [local] means local only
- environments: [] is invalid and should fail validation

## Enforcement Order

Approval authorization should always run in this order:

1. Self-approval guard
2. Pending-state check
3. Role permission check
4. Audit write

Self-approval runs first because it is a trust-boundary violation.

## Hard Invariants

These rules must not be configurable:

- requester must not approve their own request
- only pending requests can be approved or rejected
- rejected requests must never execute
- every approval decision must be audited

## Audit Requirements

Every approval decision audit record should include:

- approval_id
- trace_id
- tool_name
- action
- target
- environment
- severity
- requested_by
- reviewer_id
- reviewer_role
- decided_at
- decision
- reason
- policy_id

reviewer_role must be stored at decision time because roles can change later.

## Not Building Yet

Do not build these in this issue:

- runtime ApprovalAuthorizationEngine
- roles.yaml loader
- approval API endpoints
- dashboard UI
- ABAC
- persistent approval storage
- multi-reviewer enforcement
- production auth

## Next Implementation Issues

Recommended next issues after this design:

1. Add Approval RBAC Models
2. Add policies/roles.yaml
3. Add ApprovalAuthorizationEngine
4. Add approval API endpoints
5. Add approval audit hardening
