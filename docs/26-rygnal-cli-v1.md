# Rygnal CLI v1

Rygnal CLI v1 adds a real developer-facing command interface for Rygnal Core.

## Goal

Make Rygnal usable through a proper CLI instead of relying only on python -m demo.run_demo.

## Commands

### Help

```bash
rygnal --help
```

### Version

```bash
rygnal version
```

### Run Demo Scenarios

```bash
rygnal demo run
```

### Run Demo With CLI Approval

```bash
rygnal demo run --approval-mode cli --approver manish
```

### Validate Policy File

```bash
rygnal policy validate policies/default_policy.yaml
```

## Current Scope

- Provides a real CLI entry point
- Runs the existing real scenario runner
- Validates Rygnal policy YAML files
- Shows package version
- Keeps existing demo behavior working

## Future Work

- Add JSON output mode
- Add audit log inspection commands
- Add policy explain commands
- Add config file support
