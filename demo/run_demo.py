"""Run Rygnal real workflow scenarios."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from demo.scenario_runner import ScenarioRunner, format_outcome  # noqa: E402


def main() -> None:
    """Run all Rygnal real workflow scenarios."""
    runner = ScenarioRunner()
    outcomes = runner.run_all()

    print("\nRygnal Real Scenario Runner v1")
    print("=" * 36)

    for outcome in outcomes:
        print(format_outcome(outcome))

    print("\nAudit log: logs/audit_log.jsonl")
    print("Sandbox: demo_sandbox/")


if __name__ == "__main__":
    main()
