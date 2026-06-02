"""Run Rygnal real workflow scenarios."""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from demo.cli_output import render_run_report  # noqa: E402
from demo.scenario_runner import ScenarioRunner  # noqa: E402
from rygnal.cli_approval import build_cli_approval_workflow  # noqa: E402


def main() -> None:
    """Run all Rygnal real workflow scenarios."""
    args = parse_args()
    approval_workflow = None

    if args.approval_mode == "cli":
        approval_workflow = build_cli_approval_workflow(
            approver=args.approver,
            timeout_seconds=args.approval_timeout,
        )

    runner = ScenarioRunner(approval_workflow=approval_workflow)
    outcomes = runner.run_all()
    print(render_run_report(outcomes))


def parse_args() -> argparse.Namespace:
    """Parse demo arguments."""
    parser = argparse.ArgumentParser(
        description="Run Rygnal real workflow scenarios.",
    )
    parser.add_argument(
        "--approval-mode",
        choices=["default", "cli"],
        default="default",
        help="Use default safe rejection or interactive CLI approval.",
    )
    parser.add_argument(
        "--approver",
        default="cli_user",
        help="Identity recorded for CLI approval decisions.",
    )
    parser.add_argument(
        "--approval-timeout",
        type=int,
        default=30,
        help="Seconds before CLI approval rejects by default.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    main()
