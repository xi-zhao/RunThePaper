from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


CODE_ROOT = Path(__file__).resolve().parents[1]
CASE_ROOT = CODE_ROOT.parent if CODE_ROOT.name == "code" else CODE_ROOT
sys.path.insert(0, str(CODE_ROOT / "src"))

from cavity_transport.experiments import RunContext, TARGET_RUNNERS, run_targets  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Reproduce numerical targets from arXiv:2608.05312."
    )
    parser.add_argument(
        "--profile",
        choices=("quick", "paper_subset"),
        default="quick",
        help="Quick smoke run or the declared paper-parameter subset.",
    )
    parser.add_argument(
        "--targets",
        default="checks,dynamics,detuning",
        help=(
            "Comma-separated targets. Available: "
            + ",".join(TARGET_RUNNERS)
            + ". Use 'all' for every implemented target."
        ),
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=CASE_ROOT / "outputs",
        help="Output directory containing data/, figures/, comparisons/, checks/.",
    )
    parser.add_argument(
        "--output-namespace",
        help="Optional namespace below each output kind, for non-canonical probes.",
    )
    parser.add_argument(
        "--no-reference-comparisons",
        action="store_true",
        help="Disable the separate render-diagnostics channel for source-blind runs.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    targets = (
        list(TARGET_RUNNERS)
        if args.targets.strip() == "all"
        else [value.strip() for value in args.targets.split(",") if value.strip()]
    )
    context = RunContext.create(
        CODE_ROOT,
        args.output_root,
        args.profile,
        output_namespace=args.output_namespace,
        allow_reference_comparisons=not args.no_reference_comparisons,
    )
    manifest = run_targets(context, targets)
    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
