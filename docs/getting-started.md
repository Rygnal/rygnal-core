# Getting Started with Rygnal Core v0.1

Learn how to set up Rygnal locally, run the demo, and integrate it with your own code.

## 15-Minute Quick Start

### Prerequisites
- **Python 3.11+** (use `python --version` to check)
- **Git** (use `git --version` to check)

### Step 1: Clone the Repository (30 seconds)
```bash
git clone https://github.com/Rygnal/rygnal-core.git
cd rygnal-core
```

### Step 2: Install Dependencies (30 seconds)
```bash
python -m pip install -r requirements-dev.txt
```

### Step 3: Run the Demo (30 seconds)
```bash
python -m demo.run_demo
```

**Expected output:**
You'll see 5 demo scenarios, each showing:
- A risky AI agent action
- Rygnal's risk assessment
- Policy decision (block/allow/simulate)
- Result (blocked/allowed/simulated)
- Audit log entry

### Step 4: Review the Output
```
✅ Scenario 1: Agent tries to read .env file
   Risk Score: HIGH (78/100)
   Policy Decision: BLOCK
   Reason: Reading environment secret files is not allowed.
   Result: BLOCKED ✓

✅ Scenario 2: Agent tries to delete important file
   ...
```

**Congratulations!** Rygnal is working. You've just seen the core value: catching risky actions before execution.

---

## Docker Quick Start (2 minutes)

### Prerequisites
- **Docker** (use `docker --version` to check)
- **Docker Compose** (use `docker compose --version` to check)

### Run Demo in Docker
```bash
docker compose build
docker compose run --rm rygnal python -m demo.run_demo
```

**or run tests:**
```bash
docker compose run --rm rygnal pytest -q
```

**or run everything:**
```bash
docker compose run --rm rygnal make validate
```

---

## Local Development Setup

### Step 1: Install Python 3.11+

**macOS (using Homebrew):**
```bash
brew install python@3.11
```

**Ubuntu/Debian:**
```bash
sudo apt-get install python3.11 python3.11-venv python3.11-dev
```

**Windows (using Python.org):**
Download and install from [python.org](https://www.python.org/downloads/)

### Step 2: Create Virtual Environment (Optional but Recommended)
```bash
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 3: Clone Repository
```bash
git clone https://github.com/Rygnal/rygnal-core.git
cd rygnal-core
```

### Step 4: Install Dependencies
```bash
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
```

### Step 5: Verify Installation
```bash
# Run tests
pytest -q

# Format and lint code
ruff format src tests demo
ruff check src tests demo

# Run security checks
bandit -r src demo -c pyproject.toml
pip-audit -r requirements-dev.txt

# Run the demo
python -m demo.run_demo
```

All commands should pass without errors.

---

## Using Rygnal in Your Code

### Basic Usage

```python
from rygnal.interceptor import RygnalInterceptor
from rygnal.policy_engine import load_default_policy_engine
from rygnal.audit_logger import AuditLogger
from rygnal.tool_executor import ToolExecutor
from rygnal.models import ToolRequest, RuntimeMode

# 1. Initialize components
policy_engine = load_default_policy_engine()
audit_logger = AuditLogger(log_dir="./logs")
tool_executor = ToolExecutor()

# 2. Create interceptor
interceptor = RygnalInterceptor(
    policy_engine=policy_engine,
    audit_logger=audit_logger,
    tool_executor=tool_executor,
    runtime_mode=RuntimeMode.ENFORCE
)

# 3. Create a tool request
request = ToolRequest(
    tool_name="file_read",
    action="read",
    target="/home/user/config.txt",
    input={},
    environment="local"
)

# 4. Intercept the request
result = interceptor.intercept(request)

# 5. Check the result
print(f"Decision: {result.decision}")
print(f"Executed: {result.executed}")
print(f"Output: {result.output}")
print(f"Audit ID: {result.audit_id}")
```

### Runtime Modes

**OBSERVE Mode** - Audit only, never execute:
```python
interceptor = RygnalInterceptor(
    policy_engine=policy_engine,
    audit_logger=audit_logger,
    tool_executor=tool_executor,
    runtime_mode=RuntimeMode.OBSERVE  # Never execute tools
)
```

**SIMULATE Mode** - Test policies without real execution:
```python
interceptor = RygnalInterceptor(
    policy_engine=policy_engine,
    audit_logger=audit_logger,
    tool_executor=tool_executor,
    runtime_mode=RuntimeMode.SIMULATE  # Simulate execution
)
```

**ENFORCE Mode** - Respect policy decisions (default):
```python
interceptor = RygnalInterceptor(
    policy_engine=policy_engine,
    audit_logger=audit_logger,
    tool_executor=tool_executor,
    runtime_mode=RuntimeMode.ENFORCE  # Enforce policies
)
```

### Custom Policies

Create a custom policy file `my_policy.yaml`:
```yaml
rules:
  # Block any file deletion
  - id: block-all-deletes
    tool_name: file_delete
    decision: block
    severity: high
    reason: "All file deletions are blocked in this environment."

  # Require approval for shell commands
  - id: approve-shell
    tool_name: shell_command
    decision: require_approval
    severity: high
    reason: "Shell commands require human approval."

  # Allow file reads
  - id: allow-reads
    tool_name: file_read
    decision: allow
    severity: low
    reason: "File reads are allowed."
```

Load and use your custom policy:
```python
from rygnal.policy_engine import PolicyEngine
from pathlib import Path

policy_engine = PolicyEngine(rules_file=Path("my_policy.yaml"))

interceptor = RygnalInterceptor(
    policy_engine=policy_engine,
    audit_logger=audit_logger,
    tool_executor=tool_executor,
    runtime_mode=RuntimeMode.ENFORCE
)
```

### Handling Different Decisions

```python
from rygnal.models import Decision

result = interceptor.intercept(request)

if result.decision == Decision.ALLOW:
    print("Tool execution allowed")
    if result.executed:
        print(f"Output: {result.output}")

elif result.decision == Decision.BLOCK:
    print("Tool execution blocked")
    print(f"Reason: {result.metadata.get('reason')}")

elif result.decision == Decision.SIMULATE:
    print("Tool execution simulated (not actually run)")

elif result.decision == Decision.REQUIRE_APPROVAL:
    print("Tool execution requires human approval")
    if result.metadata.get("approval_id"):
        print(f"Approval ID: {result.metadata['approval_id']}")
```

### Accessing Audit Logs

Audit logs are stored in JSON lines format:
```bash
# View audit logs
cat logs/audit.log | head

# Pretty print logs
python -m json.tool logs/audit.log
```

Each audit entry contains:
- Request details (tool, action, target, input)
- Risk assessment (score, breakdown)
- Policy decision (rule matched, reason)
- Execution status
- Timestamp

---

## Customization Examples

### Example 1: Custom Tool Type

Implement a custom tool adapter:
```python
from rygnal.tool_executor import ToolExecutor, ToolExecutionResult
from rygnal.models import ToolRequest, ExecutionStatus

class CustomToolExecutor(ToolExecutor):
    def execute(self, request: ToolRequest) -> ToolExecutionResult:
        if request.tool_name == "custom_tool":
            # Your custom logic here
            return ToolExecutionResult(
                status=ExecutionStatus.ALLOWED,
                executed=True,
                output="Custom tool executed successfully"
            )
        return super().execute(request)

# Use with interceptor
tool_executor = CustomToolExecutor()
interceptor = RygnalInterceptor(
    policy_engine=policy_engine,
    audit_logger=audit_logger,
    tool_executor=tool_executor
)
```

### Example 2: Custom Approval Workflow

```python
from rygnal.approval import ApprovalWorkflow
from rygnal.models import ApprovalDecision, ApprovalStatus

class CustomApprovalWorkflow(ApprovalWorkflow):
    def request_approval(self, request, policy_decision, risk_assessment):
        # Your custom approval logic here
        # For example, check user permissions, send email, etc.
        
        approval_request, approval_decision = super().request_approval(
            request, policy_decision, risk_assessment
        )
        
        # Custom logic
        print(f"Approval requested: {approval_request.approval_id}")
        
        return approval_request, approval_decision

# Use with interceptor
approval_workflow = CustomApprovalWorkflow()
interceptor = RygnalInterceptor(
    policy_engine=policy_engine,
    audit_logger=audit_logger,
    tool_executor=tool_executor,
    approval_workflow=approval_workflow
)
```

### Example 3: Custom Risk Engine

```python
from rygnal.risk_engine import RiskEngine
from rygnal.models import ToolRequest

class CustomRiskEngine(RiskEngine):
    def assess(self, request: ToolRequest):
        # Your custom risk scoring logic here
        assessment = super().assess(request)
        
        # Add custom scoring
        if request.tool_name == "sensitive_tool":
            assessment.risk_score = 95  # Very high risk
        
        return assessment

# Use with interceptor
risk_engine = CustomRiskEngine()
interceptor = RygnalInterceptor(
    policy_engine=policy_engine,
    audit_logger=audit_logger,
    tool_executor=tool_executor,
    risk_engine=risk_engine
)
```

---

## Troubleshooting

### Issue: Python 3.11+ not found
```
Error: Python 3.11 is required
```
**Solution:** 
- Check your Python version: `python --version`
- Install Python 3.11+ from [python.org](https://www.python.org/downloads/)
- Use python3.11 explicitly: `python3.11 -m demo.run_demo`

### Issue: Module not found
```
ModuleNotFoundError: No module named 'rygnal'
```
**Solution:**
- Install dependencies: `pip install -r requirements-dev.txt`
- Verify you're in the correct directory: `cd rygnal-core`

### Issue: Demo doesn't run
```
Permission denied: python -m demo.run_demo
```
**Solution:**
- Try with explicit Python path: `python -m demo.run_demo`
- On Windows, try: `python.exe -m demo.run_demo`

### Issue: Docker build fails
```
Error response from daemon: build failed
```
**Solution:**
- Update Docker: `docker --version` should be 20.10+
- Clear Docker cache: `docker compose build --no-cache`

---

## What to Try Next

### 1. Run the Demo Again
```bash
python -m demo.run_demo
```
Review the output to understand how Rygnal evaluates risk and makes decisions.

### 2. Read the Architecture
See [architecture.md](architecture.md) to understand how Rygnal Core works.

### 3. Explore the Code
```bash
ls -la src/rygnal/  # Core components
ls -la demo/        # Demo scenarios
ls -la policies/    # Policy definitions
```

### 4. Modify the Default Policy
Edit `policies/default_policy.yaml` and re-run the demo to see how policy changes affect decisions.

### 5. Look at the Tests
```bash
pytest -v  # Run all tests with output
pytest tests/test_policy_engine.py -v  # Run specific test file
```

### 6. Integrate with Your Code
Use the examples above to integrate Rygnal into your AI agent or tool system.

### 7. Join the Community
- Open issues on GitHub
- Contribute improvements
- Share feedback

---

## Running All Validation Commands

Before committing code, run the full validation suite:

```bash
# Format code
ruff format src tests demo

# Lint code
ruff check src tests demo

# Run tests
pytest -q

# Security audit
bandit -r src demo -c pyproject.toml

# Dependency audit
pip-audit -r requirements-dev.txt

# Run the demo
python -m demo.run_demo

# Or all at once (using Makefile)
make validate
```

All should pass with exit code 0.

---

## Environment Variables

Optional configuration:

```bash
export RYGNAL_LOG_DIR="./logs"           # Audit log directory
export RYGNAL_POLICY_FILE="./policies/default_policy.yaml"  # Policy file
export RYGNAL_MODE="ENFORCE"             # Runtime mode
```

## Next Steps

- ✅ **Demo works?** Check [Architecture](architecture.md)
- ✅ **Want to understand limitations?** See [Known Limitations](known-limitations.md)
- ✅ **Want to know what's planned?** See [v0.1 Scope](v0.1-scope.md)
- ✅ **Need help?** Check [README.md](../README.md) for more info

**Happy securing! 🔐**
