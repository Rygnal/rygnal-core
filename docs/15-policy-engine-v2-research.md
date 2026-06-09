# Policy Engine v2: YAML vs OPA/Rego Research

## Status

Historical archive note. This research document is retained for historical context and is superseded by `docs/23-policy-engine-v2-research.md` as the current policy v2 direction.

Current direction: build improved YAML Policy Engine v2 first, keep OPA/Rego as a future optional backend.

**Author:** Rygnal Engineering  
**Date:** June 2026  
**Status:** Research Complete

---

## Executive Summary

This document evaluates whether Rygnal should keep its custom YAML policy engine or migrate to a policy-as-code framework like OPA/Rego for Phase 2.

**Recommendation:** **Adopt a hybrid approach** starting in Phase 2:
1. Keep YAML for simple, rule-based policies (MVP-grade)
2. Introduce OPA/Rego support for complex enterprise policies
3. Provide tooling to help teams migrate gradually
4. Ensure backwards compatibility throughout the transition

---

## Current State: YAML Policy Engine (Phase 1 / MVP)

### Architecture

```
PolicyRule (YAML) → PolicyEngine.from_file() → Evaluate Sequential Rules → First Match Wins
```

### Capabilities

The current YAML policy engine supports:

- **Exact Matching:**
  - `tool_name` exact match (e.g., `file_read`, `shell_command`)
  - `action` exact match (e.g., `execute`, `read_file`)
  - `environment` exact match (e.g., `local`, `production`)

- **String Pattern Matching:**
  - `target_contains` substring match (e.g., `.env` in target path)
  - `input_contains` substring match (e.g., `rm -rf` in input)

- **Decision Output:**
  - `decision`: `ALLOW`, `BLOCK`, `REQUIRE_APPROVAL`, `SIMULATE`
  - `severity`: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`
  - `reason`: human-readable text
  - `id`: unique policy rule identifier

### Example YAML Policy

```yaml
rules:
  - id: block-env-read
    tool_name: file_read
    target_contains: ".env"
    decision: block
    severity: critical
    reason: "Reading environment secret files is not allowed."

  - id: approval-file-delete
    tool_name: file_delete
    decision: require_approval
    severity: high
    reason: "File deletion requires human approval."
```

### Advantages of Current YAML Approach

| Advantage | Benefit |
|-----------|---------|
| **Simple & Readable** | Non-technical stakeholders can understand policies |
| **Easy to Implement** | MVP could be built in 1-2 weeks |
| **Deterministic** | Rule order is explicit; first match wins |
| **Fast Evaluation** | Linear scan through rules; O(n) complexity is acceptable for MVP |
| **Version Controlled** | Policies integrate naturally with git workflows |
| **Low Dependencies** | Uses only PyYAML; minimal supply chain risk |
| **Easy Testing** | Unit tests are straightforward |
| **IDE Support** | YAML editing is widely supported |

### Limitations of Current YAML Approach

#### 1. **No Complex Logic**

❌ Cannot express conditional logic:

```yaml
# What we want: "Approve ONLY if risk_score < 50 AND user_role = admin"
# Current YAML: No support for OR/AND/NOT logic

# Workaround: Create many rules (combinatorial explosion)
- id: low-risk-admin-approve
  tool_name: file_delete
  # But how do we check risk_score and user_role? We can't.
  decision: require_approval
```

#### 2. **No Access to Rich Context**

Current policy rules can only access:

- `tool_name`
- `action`
- `environment`
- `target`
- `input`

**Cannot access:**

- `user_id` / user role (admin, operator, read-only)
- `agent_id` / agent type (autonomous, human-supervised)
- `risk_score` from the risk engine
- `risk_signals` (what specific patterns triggered high risk)
- `metadata` (custom fields for enterprise needs)
- `data_classification` (is this PII, public, internal?)
- `approval_chain` (how many approvals needed)

#### 3. **No Complex Pattern Matching**

❌ Limited string matching:

```yaml
# Current: substring search only
- target_contains: ".env"

# What enterprises need:
# - Regular expressions: /^\..*credentials/
# - Wildcard patterns: /var/secrets/*
# - Negation: NOT /var/public/*
# - Multiple patterns in one rule
```

#### 4. **No Policy Inheritance or Composition**

❌ Each rule is independent:

```yaml
# Desired: Policy inheritance/composition
# base-security-policy.yaml
#   ├─ file-access-policy.yaml
#   └─ network-policy.yaml

# Current: All rules in one file (doesn't scale)
```

#### 5. **No Stateful Policies**

❌ Cannot track state across requests:

```yaml
# Desired: "Block shell commands if 3+ dangerous commands detected in last 5 min"
# Current: No state tracking; each request evaluated independently
```

#### 6. **No Risk Score Integration**

❌ Policies cannot use risk engine output:

```yaml
# Desired:
# - id: risk-based-approval
#   decision: require_approval
#   if: risk_score > 75

# Current: PolicyRule has no risk score condition
```

#### 7. **No User/Agent Identity-Based Decisions**

❌ Cannot differentiate by user or agent:

```yaml
# Desired:
# - Allow file_read for admin users in production
# - Require approval for other users

# Current: No support for user_role or agent capabilities
```

---

## OPA/Rego as Alternative

### What is OPA/Rego?

**Open Policy Agent (OPA)** is a general-purpose policy engine that uses the **Rego** language to express policies as code.

**Rego** is a logic-based language (similar to Prolog/Datalog) designed for policy decisions.

### Example Rego Policy

```rego
package rygnal

# Allow file_read on non-sensitive files
allow {
    input.tool_name == "file_read"
    not sensitive_file(input.target)
    input.risk_score < 50
}

# Require approval for file deletion
require_approval {
    input.tool_name == "file_delete"
    not is_admin(input.user_id)
}

# Block dangerous shell commands
deny {
    input.tool_name == "shell_command"
    dangerous_pattern(input.input)
}

# Helper: check if file is sensitive
sensitive_file(target) {
    sensitive_names := [".env", "secrets", "credentials", "key", "token"]
    contains_any := [name | name := sensitive_names[_]; contains(target, name)]
    count(contains_any) > 0
}

# Helper: check if user is admin
is_admin(user_id) {
    data.admins[user_id]
}

# Helper: check for dangerous patterns
dangerous_pattern(input_str) {
    patterns := ["rm -rf", "sudo", "chmod 777", ":(){ :|:"]
    any_match := [p | p := patterns[_]; contains(input_str, p)]
    count(any_match) > 0
}
```

### Advantages of OPA/Rego

| Advantage | Benefit |
|-----------|---------|
| **Full Logic Programming** | Express any policy using boolean logic |
| **Rich Context Access** | Pass entire request object + user/role/risk data |
| **Complex Conditions** | AND, OR, NOT, regex, loops, aggregations |
| **Modularity** | Policies can import/compose other policies |
| **Reusable Helpers** | Define functions and data transformations |
| **Dynamic Data** | External data (user roles, risk scores) integrates easily |
| **Testing Framework** | OPA has built-in testing (opa test) |
| **Production Adoption** | Used by companies like Google, Styra, and many enterprises |
| **Stateful Policies** | Can evaluate against time-series data (risk history) |
| **IDE/Lint Support** | Good tooling ecosystem (VS Code, linters) |
| **Performance** | Compiled; faster than Python string matching for complex queries |
| **Audit Trail** | Can explain why a policy decision was made |

### Disadvantages of OPA/Rego

| Disadvantage | Impact |
|--------------|--------|
| **Steep Learning Curve** | Rego is logic-based; not familiar to most developers |
| **New Dependency** | Requires OPA runtime (Go binary or Python wrapper) |
| **Performance Overhead** | Extra latency for policy evaluation (ms-scale, acceptable) |
| **Overkill for MVP** | Introduces complexity for simple policies |
| **Debugging Difficulty** | Logic-based debugging is non-intuitive |
| **Documentation Burden** | Teams need Rego training |
| **Migration Effort** | Moving from YAML to Rego requires rewriting policies |

### OPA/Rego Architecture in Rygnal

```
ToolRequest + RiskAssessment + UserContext
           ↓
      OPA Rego Engine
           ↓
   Policy Decision (Allow/Block/Approve/Simulate)
```

---

## Phase 1 vs Phase 2+ Requirements

### Phase 1 (MVP) - Current

- ✅ Block sensitive files (e.g., `.env`)
- ✅ Block dangerous shell commands
- ✅ Require approval for file deletion
- ✅ Simulate external API calls
- ✅ Deterministic, fast policy evaluation
- ✅ Simple policies, easy to understand

**YAML is sufficient.**

### Phase 2+ (Enterprise) - Emerging Requirements

- ❌ Allow based on `user_role` (admin vs operator)
- ❌ Different policies for different `agent_types` (autonomous vs supervised)
- ❌ **Risk score integration** ("approve only if risk < 50")
- ❌ Complex approval workflows ("2 admins + 1 manager")
- ❌ Time-based policies ("deny this action after hours")
- ❌ Data classification policies ("block if accessing PII")
- ❌ Policy composition ("inherit from base-security.rego")
- ❌ Regular expressions for pattern matching
- ❌ Audit compliance rules ("log all deletions")

**YAML becomes problematic. OPA/Rego becomes attractive.**

---

## Research Analysis: When YAML Breaks Down

### Example 1: Risk-Based Approval

**Requirement:** "Approve shell commands only if risk_score < 40 and user is admin"

**YAML Attempt:**

```yaml
# ❌ Not possible - no risk_score field, no user role access
- id: risk-based-approval
  tool_name: shell_command
  decision: require_approval
  # No way to check risk_score < 40 or user role
```

**Rego Solution:**

```rego
approve_command {
    input.tool_name == "shell_command"
    input.risk_score < 40
    is_admin(input.user_id)
}
```

### Example 2: Policy Composition

**Requirement:** Base security policy + environment-specific overrides

**YAML Attempt:**

```yaml
# ❌ All rules in one file; no inheritance/composition
# Can't override rules from base policy
rules:
  - id: base-env-blocking
    # ...
  - id: prod-specific-override
    # ...
```

**Rego Solution:**

```rego
# policies/base.rego
package rygnal.base
default_allow { input.risk_score < 30 }

# policies/prod.rego
package rygnal.prod
import data.rygnal.base
override_prod_approval { /* ... */ }
```

### Example 3: Complex Conditions

**Requirement:** "Block database modifications unless (user is DBA and in maintenance window) or (has PagerDuty incident)"

**YAML Attempt:**

```yaml
# ❌ No way to express boolean logic
- id: db-modify-restriction
  tool_name: database_execute
  # Cannot check: (is_dba AND in_maintenance) OR has_incident
```

**Rego Solution:**

```rego
allow_database_modify {
    is_dba(input.user_id)
    in_maintenance_window(input.timestamp)
}

allow_database_modify {
    has_pagerduty_incident(input.agent_id)
}

deny_database_modify {
    input.tool_name == "database_execute"
    not allow_database_modify
}
```

---

## Alternative: Custom DSL

**Hypothesis:** Could Rygnal create its own domain-specific language (DSL) instead of adopting OPA/Rego?

### Prototype DSL Concept

```
// Simpler than Rego, tailored to Rygnal
rule "block-env-read" {
    when tool == "file_read" AND target contains ".env"
    then BLOCK with severity CRITICAL
}

rule "risk-based-approval" {
    when tool == "shell_command" AND risk_score > 75
    then REQUIRE_APPROVAL
}

rule "admin-bypass" {
    when user_role == "admin" AND risk_score < 50
    then ALLOW
}
```

### Custom DSL Evaluation

| Aspect | Rating | Notes |
|--------|--------|-------|
| Learning Curve | ⭐⭐⭐⭐⭐ | Easiest for Rygnal users |
| Expressiveness | ⭐⭐⭐ | Limited to what we implement |
| Migration Effort | ⭐⭐⭐⭐ | Natural progression from YAML |
| Maintenance | ⭐⭐ | Rygnal must maintain entire language + tooling |
| Community | ⭐ | No ecosystem; only Rygnal support |
| Performance | ⭐⭐⭐⭐⭐ | Can optimize for Rygnal use cases |
| Composability | ⭐⭐ | Must implement ourselves |
| External Data | ⭐⭐⭐ | Must build integration layer |

**Verdict:** Not recommended. OPA/Rego is already built; better to leverage battle-tested solution.

---

## Recommended Phase 2 Direction: Hybrid Approach

### Architecture: Dual-Engine Support

```
ToolRequest + Context (user, risk, etc.)
              ↓
        Policy Engine Router
         ↙              ↘
    YAML Rules      OPA/Rego Policies
    (simple)        (complex)
         ↘              ↙
         Policy Decision
         (Allow/Block/Approve/Simulate)
```

### Migration Strategy

#### Phase 1 (Current): YAML Only
- Keep all existing YAML policies
- Tests pass with YAML engine
- Zero breaking changes

#### Phase 2a (Early): Add OPA/Rego Support
- New PolicyEngine v2 can accept both YAML and Rego policies
- Default: evaluate YAML rules first
- If policy file is `.rego`: evaluate with OPA
- Backwards compatible: all existing YAML policies work unchanged

#### Phase 2b (Mid): Co-existence Mode
- Teams can author new policies in Rego
- Teams keep old YAML policies
- PolicyEngine routes to correct engine based on file extension
- Gradual migration; no forced rewrites

#### Phase 2c (Late): Optional Migration Helpers
- Provide YAML→Rego converter for common patterns
- Documentation with side-by-side examples
- CLI tool: `rygnal policy convert --from yaml --to rego`

#### Phase 3+ (Future): Sunset YAML (Optional)
- If all policies migrated to Rego, deprecate YAML support
- Keep conversion tool for archives
- Not mandatory; some teams may stay with YAML

### Implementation Roadmap

```
Phase 1 (Now)     Phase 2a (Q3)    Phase 2b (Q4)     Phase 3 (Q1+)
├─ YAML Only      ├─ Add OPA       ├─ Both Work      ├─ OPA Primary
├─ Simple rules   │  wrapper       │  side-by-side   │  YAML optional
└─ MVP complete   │                │                 └─ Migration
                  ├─ Policy Router │                    tools ready
                  │  by extension  │
                  └─ Compat tests  │
```

---

## What Should Never Be Configurable (Hard Constraints)

These decisions must **always be made by Rygnal**, regardless of policy language:

1. **Audit Logging** - Every decision must be logged. No policy can disable audit trails.

2. **Core Decisions** - `ALLOW`, `BLOCK`, `REQUIRE_APPROVAL`, `SIMULATE` are fixed. No policy can invent new decisions.

3. **Integrity Chain** - Event hashing and tamper detection must always run. No policy can skip this.

4. **Safe Defaults** - If a request doesn't match any policy, the default is `ALLOW` (but can be overridden per deployment).

5. **Risk Assessment** - Risk engine output is informational. Policies can *consider* risk but cannot disable risk scoring.

6. **Tool Execution Prevention** - If policy decides `BLOCK`, the tool must never execute. No exceptions.

---

## Key Questions Addressed

### Q1: How far can current YAML policy go?

**A:** YAML works for MVP and simple rule sets (40-50 rules). Beyond ~100 rules or when needing conditional logic, it becomes unmaintainable.

### Q2: What policy examples become hard in YAML?

**A:** 
- Risk score-based decisions
- User role / agent type differentiation
- Complex boolean logic
- Temporal policies (time-based rules)
- Policy composition/inheritance
- Stateful policies

### Q3: Should Rygnal adopt OPA/Rego later?

**A:** **Yes, in Phase 2.** OPA/Rego is battle-tested, widely adopted, and solves hard problems. Better to adopt proven tool than reinvent.

### Q4: Should Rygnal create its own simple policy DSL?

**A:** **No.** The burden of maintaining a language exceeds the benefit. OPA/Rego already exists and is more powerful.

### Q5: How would migration work?

**A:** Gradual, opt-in. New policies in Rego; old YAML policies continue working. No forced migration.

### Q6: What should be configurable?

**A:** 
- Tool name/action matching ✅
- Risk thresholds ✅
- User/agent attributes ✅
- Approval workflows ✅
- Severity levels ✅
- Policy composition ✅
- Temporal rules ✅

### Q7: What should never be configurable for safety?

**A:**
- Audit logging ❌ (always on)
- Core decisions ❌ (fixed set)
- Execution prevention ❌ (if blocked, never runs)
- Tamper detection ❌ (always on)

---

## Proof of Concept Plan (Optional)

If Phase 2 commits to OPA/Rego, create a small PoC:

### PoC Scope (1-2 weeks)

1. **Add OPA Python wrapper**
   - Use `python-opa-wasm` or embed OPA binary
   - Minimal dependency

2. **Extend PolicyRule to support Rego source**
   ```python
   class PolicyRule(BaseModel):
       # Current fields...
       rego_source: str | None = None  # New: inline Rego code
   ```

3. **Create PolicyEngine v2**
   ```python
   class PolicyEngineV2(PolicyEngine):
       def evaluate(self, request: ToolRequest) -> PolicyDecision:
           # Detect: YAML rules vs Rego source
           # Route to correct engine
           # Return PolicyDecision
   ```

4. **Test suite**
   - Replicate 10 YAML tests in Rego
   - Verify both engines produce same results
   - Performance benchmarks

5. **Documentation**
   - Hello-World Rego policy
   - Migration guide
   - Best practices

### PoC Success Criteria

- ✅ OPA/Rego policies produce same results as YAML equivalents
- ✅ Backwards compatible (all YAML tests pass)
- ✅ <50ms evaluation latency (acceptable for security decision)
- ✅ Code coverage >80%

---

## Conclusion

**For Phase 1 (MVP):** YAML policies are sufficient, simple, and effective.

**For Phase 2+ (Enterprise):** Adopt OPA/Rego alongside YAML, allowing gradual migration.

**Migration Path:** Keep both systems running in parallel; teams choose policy language; provide conversion tooling.

**Safety:** Hard constraints (audit, execution prevention, integrity) remain non-configurable regardless of policy language.

---

## References

- [Open Policy Agent (OPA) Documentation](https://www.openpolicyagent.org/docs/)
- [Rego Language Guide](https://www.openpolicyagent.org/docs/latest/policy-language/)
- [OPA Use Cases](https://www.openpolicyagent.org/docs/latest/examples/)
- [Python OPA Wrapper: python-opa-wasm](https://github.com/pycqa/python-opa-wasm)
- [Policy as Code (Styra Blog)](https://www.styra.com/blog/what-is-policy-as-code/)

---

## Appendix A: Comparison Matrix

| Feature | YAML v1 | OPA/Rego | Custom DSL |
|---------|---------|----------|-----------|
| **Readability** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Learning Curve** | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ |
| **Logic Support** | ⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Scalability** | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Maintenance Burden** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐ |
| **Community Support** | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐ |
| **MVP Fit** | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ |
| **Enterprise Fit** | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |

---

## Appendix B: Hard Examples

### Example: Time-Based Policies

```rego
# "Allow shell commands during business hours, require approval after hours"
allow_shell {
    input.tool_name == "shell_command"
    is_business_hours(input.timestamp)
    not dangerous_command(input.input)
}

is_business_hours(timestamp) {
    hour := to_number(substr(timestamp, 11, 2))
    day := dayofweek(timestamp)
    hour >= 8
    hour < 18
    day >= 1  # Monday
    day < 6   # Friday
}
```

### Example: Risk-Score Aggregation

```rego
# "Block if multiple risky actions in succession"
require_approval_risk_spike {
    input.tool_name == "file_delete"
    recent_actions := data.recent_actions[input.agent_id]
    high_risk_count := count([a | a := recent_actions[_]; a.risk_score > 70])
    high_risk_count >= 3
}
```

### Example: Data Classification

```rego
# "Block access to PII unless user is compliance officer"
deny_pii_access {
    is_pii(input.target)
    not has_role(input.user_id, "compliance_officer")
    input.tool_name == "file_read"
}

is_pii(target) {
    pii_patterns := [
        "customer_data",
        "ssn",
        "credit_card",
        "health_records"
    ]
    any_contains := [p | p := pii_patterns[_]; contains(target, p)]
    count(any_contains) > 0
}
```

These examples **cannot be easily expressed in YAML** but are **trivial in Rego**.

