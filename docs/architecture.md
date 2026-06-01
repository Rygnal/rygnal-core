# Rygnal Core Architecture

## System Overview

Rygnal Core is built around a single, critical control point: the **Interceptor**. Every AI agent tool request flows through this interceptor, which coordinates risk assessment, policy evaluation, approval workflows, and audit logging.

```
┌─────────────────────────────────────────────────────────────────┐
│                      AI Agent Runtime                           │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           │ Tool Request
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Rygnal Interceptor                            │
│  ┌─────────────────────────────────────────────────────────────┤
│  │ 1. Risk Assessment       ───► [Risk Engine]                 │
│  │ 2. Policy Matching       ───► [Policy Engine]               │
│  │ 3. Approval Check        ───► [Approval Workflow]           │
│  │ 4. Audit Logging         ───► [Audit Logger]                │
│  │ 5. Decision Execution    ───► [Tool Executor]               │
│  └─────────────────────────────────────────────────────────────┤
└─────────────────────┬──────────────────────────────────────────┘
                      │
         ┌────────────┼────────────┐
         │            │            │
    ALLOW / BLOCK / SIMULATE / REQUIRE_APPROVAL
         │            │            │
         └────────────┼────────────┘
                      │
                      ▼
        ┌─────────────────────────┐
        │  Tool Execution Result  │
        │  + Audit Log Entry      │
        └─────────────────────────┘
```

## Core Components

### 1. Interceptor
**File:** `src/rygnal/interceptor.py`

The central orchestrator that:
- Receives tool requests from AI agents
- Coordinates risk assessment, policy evaluation, and approval workflows
- Makes the final decision (ALLOW / BLOCK / SIMULATE / REQUIRE_APPROVAL)
- Logs every decision to the audit log
- Executes or skips tool execution based on runtime mode and decision

**Key Methods:**
- `intercept(request)` - Main entry point for tool requests
- `handle(request)` - Alias for intercept

**Runtime Modes:**
- `OBSERVE` - Never execute, just log decisions (audit-only mode)
- `SIMULATE` - Simulate tool execution, never actually run tools
- `ENFORCE` - Respect policy decisions, execute or block accordingly

### 2. Policy Engine
**File:** `src/rygnal/policy_engine.py`

Evaluates tool requests against a set of rules defined in YAML.

**Decision Types:**
- `ALLOW` - Tool is permitted to execute
- `BLOCK` - Tool execution is forbidden
- `SIMULATE` - Tool execution should be simulated (no actual execution)
- `REQUIRE_APPROVAL` - Tool requires human approval before execution

**Matching Logic:**
Rules are evaluated in order. The first matching rule determines the decision. If no rule matches, the default decision is `ALLOW`.

**Matching Criteria:**
- `tool_name` - Exact match on tool name (e.g., `file_read`, `shell_command`)
- `action` - Exact match on action (e.g., `read`, `write`, `delete`)
- `environment` - Exact match on environment (e.g., `local`, `staging`, `production`)
- `target_contains` - Substring match on target path/identifier
- `input_contains` - Substring match on serialized input

**Policy File Format (YAML):**
```yaml
rules:
  - id: block-env-read
    tool_name: file_read
    target_contains: ".env"
    decision: block
    severity: high
    reason: "Reading environment secret files is not allowed."
    
  - id: approval-file-delete
    tool_name: file_delete
    decision: require_approval
    severity: high
    reason: "File deletion requires human approval."
```

### 3. Risk Engine
**File:** `src/rygnal/risk_engine.py`

Scores tool requests for inherent risk based on:
- **Tool Type Risk** - Some tools are inherently riskier (shell commands > file operations > read operations)
- **Action Risk** - Some actions are riskier (delete > write > read)
- **Target Risk** - Some targets are riskier (system files > user files)
- **Input Risk** - Dangerous patterns in input (shell injection, path traversal)

**Risk Scores:**
- `CRITICAL` (90-100) - Extremely dangerous operations
- `HIGH` (70-89) - Dangerous operations
- `MEDIUM` (40-69) - Potentially risky operations
- `LOW` (1-39) - Generally safe operations
- `SAFE` (0) - Safe operations

**Output:** `RiskAssessment` object with:
- Overall risk score
- Per-category breakdown (tool, action, target, input)
- Explanation and remediation suggestions

### 4. Audit Logger
**File:** `src/rygnal/audit_logger.py`

Records every decision with full context for:
- Compliance auditing
- Forensic analysis
- Incident investigation
- Policy effectiveness evaluation

**Logged Information:**
- Request details (tool, action, target, input, environment)
- Risk assessment (score, breakdown)
- Policy matched (rule ID, reason, severity)
- Decision (ALLOW / BLOCK / SIMULATE / REQUIRE_APPROVAL)
- Approval details (if applicable)
- Execution status and result
- Timestamp and request ID
- Runtime mode

**Audit Log Format:** JSON lines (one entry per line)

**Storage:** File-based (default), extensible to databases

### 5. Tool Executor
**File:** `src/rygnal/tool_executor.py`

Safely executes tools based on:
- Policy decision
- Approval decision (if applicable)
- Runtime mode

**Capabilities:**
- Executes allowed tool requests
- Returns results or errors
- Integrates with various tool adapters (file operations, shell commands, API calls, etc.)

**Tool Adapters:**
- `file_read` - Read file contents
- `file_write` - Write to files
- `file_delete` - Delete files
- `shell_command` - Execute shell commands
- `external_api_send` - Send data to external APIs

### 6. Approval Workflow
**File:** `src/rygnal/approval.py`

Routes high-risk requests for human approval.

**Current Implementation (v0.1):**
- Basic deterministic approval (currently accepts all approval requests)
- Approval ID generation
- Tracks approval status

**Planned for v1+:**
- Web UI for approval dashboard
- Email/Slack notifications
- Timed approval requests (auto-deny if no response)
- Role-based approval chains
- API for programmatic approval

### 7. Models
**File:** `src/rygnal/models.py`

Defines core data structures:
- `ToolRequest` - Incoming tool request from agent
- `PolicyDecision` - Decision from policy engine
- `RiskAssessment` - Risk score and breakdown
- `ApprovalRequest` / `ApprovalDecision` - Approval workflow
- `ToolExecutionResult` - Result of tool execution
- `InterceptorResult` - Final result returned to agent
- `ExecutionStatus` - Status of execution (ALLOWED, BLOCKED, SIMULATED, SKIPPED, ERROR)
- `Decision` - Decision type enum
- `RuntimeMode` - Runtime mode enum
- `Severity` - Severity level enum

### 8. Security Utilities
**File:** `src/rygnal/security.py`

Cryptographic security features:
- Audit log cryptographic signing
- Request validation and sanitization
- Secure hashing and encoding

## Data Flow

### Request Processing Pipeline

```
1. ToolRequest arrives
   │
   ├─► Risk Engine
   │   └─► Risk Assessment + Metadata
   │
   ├─► Policy Engine
   │   └─► Policy Decision (ALLOW/BLOCK/SIMULATE/REQUIRE_APPROVAL)
   │
   ├─► Approval Workflow (if REQUIRE_APPROVAL)
   │   └─► Approval Decision
   │
   ├─► Audit Logger
   │   └─► Audit Log Entry
   │
   ├─► Tool Executor (based on runtime mode + decision)
   │   └─► Execution Result
   │
   └─► Return InterceptorResult to agent
       (decision, result, audit_id, status)
```

### Decision Matrix

| Runtime Mode | ALLOW Decision | BLOCK Decision | SIMULATE Decision | REQUIRE_APPROVAL Decision |
|---|---|---|---|---|
| **OBSERVE** | Log, Skip | Log, Skip | Log, Skip | Log, Skip |
| **SIMULATE** | Log, Simulate | Log, Skip | Log, Simulate | Log, Skip |
| **ENFORCE** | Log, Execute | Log, Skip | Log, Simulate | Log, Execute (if approved) |

## Extension Points

Rygnal is designed to be extended:

### Custom Tool Adapters
Implement the tool executor interface to support new tool types.

### Custom Policy Rules
Add new matching criteria to the policy engine for domain-specific rules.

### Custom Risk Scorers
Extend the risk engine to implement custom risk scoring logic.

### Custom Audit Loggers
Implement alternative audit log backends (database, SIEM, cloud logging).

## Configuration

### Environment Variables
- `RYGNAL_MODE` - Runtime mode (OBSERVE, SIMULATE, ENFORCE)
- `RYGNAL_POLICY_FILE` - Path to policy YAML file
- `RYGNAL_LOG_DIR` - Directory for audit logs
- `RYGNAL_APPROVAL_TIMEOUT` - Approval request timeout (seconds)

### Policy Configuration
Edit `policies/default_policy.yaml` to customize policies.

## Security Considerations

1. **Audit Log Integrity** - Audit logs are cryptographically signed to prevent tampering
2. **Request Validation** - All incoming requests are validated before processing
3. **Tool Isolation** - Tool executors run in isolated contexts when possible
4. **Safe Defaults** - Missing configuration defaults to safe/deny-by-default behavior
5. **No Code Execution in Policies** - Policies are declarative YAML, no arbitrary code execution

## Performance Characteristics

- **Policy Matching** - O(n) where n is number of rules (typically < 100)
- **Risk Assessment** - O(1) with fixed set of checks
- **Audit Logging** - Async-friendly, non-blocking writes
- **Approval Workflow** - Async, doesn't block tool executor

## v0.1 Limitations

- **YAML Policies Only** - v0.1 uses simple YAML rules. OPA/Rego support planned for v1+
- **Deterministic Risk Scoring** - Fixed rule-based scoring, no ML/heuristics yet
- **Basic Approval Workflow** - No UI, email, or notification system
- **No Real-time Policy Updates** - Policies loaded on startup
- **No Policy Versioning** - Single active policy version
- **Local Audit Logs** - Single-node file storage, no distributed logging
- **No Policy Conflict Detection** - Overlapping rules can create unexpected results

## Future Enhancements (v1+)

- OPA/Rego policy engine support
- ML-based risk scoring
- Web dashboard for monitoring
- Policy management UI
- Real-time policy hot-reload
- Policy versioning and rollback
- Multi-node audit log aggregation
- SIEM integration
- Advanced approval workflows
- Real AI agent integration (LangChain, AutoGen, etc.)
