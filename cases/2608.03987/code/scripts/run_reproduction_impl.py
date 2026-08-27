from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


WORKSPACE = Path(__file__).resolve().parents[1]
CASE_ROOT = WORKSPACE.parent
sys.path.insert(0, str(WORKSPACE / "src"))

from benchmark_release import ARCHIVE_FILENAME  # noqa: E402
from realified_figures import run_reproduction  # noqa: E402


def _default_archive() -> Path:
    internal = CASE_ROOT / "raw" / "benchmarks" / ARCHIVE_FILENAME
    public = CASE_ROOT / "inputs" / ARCHIVE_FILENAME
    return internal if internal.is_file() else public


def _default_output_root() -> Path:
    if (WORKSPACE / "metadata").is_dir():
        return WORKSPACE / "outputs"
    return CASE_ROOT / "outputs"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Reproduce Figures 8 and 9 of arXiv:2608.03987."
    )
    parser.add_argument(
        "--archive",
        type=Path,
        default=_default_archive(),
        help="Immutable Zenodo data-release ZIP.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=_default_output_root(),
        help="Directory containing data/, figures/, and checks/.",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Validate and write tidy data/checks without rendering figures.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = run_reproduction(
        args.archive,
        args.output_root,
        render=not args.validate_only,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
