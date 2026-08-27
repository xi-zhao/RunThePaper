#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import sys


WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from supplement_hatano_nelson import run_supplement_case  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run reduced-scale supplement numerics for Fig. S1/S2.")
    parser.add_argument(
        "--config",
        type=Path,
        default=WORKSPACE / "config" / "supplement_feature_run.json",
    )
    parser.add_argument(
        "--science-only",
        action="store_true",
        help="Generate numerical data and checks without invoking the rendering stack.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    result = run_supplement_case(WORKSPACE, config, render_figures=not args.science_only)
    # The historical supplement runner writes below outputs/supplement_feature.
    # Copy the same generated artifacts into the Harness canonical output roots
    # so the isolated-run contract can hash and attest them without changing the
    # legacy public paths in existing case evidence.
    canonical_outputs = {
        "supplement_feature/data/supplement_offdiag_grid.csv": "data/supplement_offdiag_grid.csv",
        "supplement_feature/data/supplement_offdiag_profiles.csv": "data/supplement_offdiag_profiles.csv",
        "supplement_feature/data/supplement_quasiperiodic_grid.csv": "data/supplement_quasiperiodic_grid.csv",
        "supplement_feature/data/supplement_quasiperiodic_profiles.csv": "data/supplement_quasiperiodic_profiles.csv",
        "supplement_feature/checks/supplement_feature_checks.json": "checks/supplement_feature_checks.json",
    }
    if not args.science_only:
        canonical_outputs.update(
            {
                "supplement_feature/figures/figs1_reproduction.png": "figures/figs1_reproduction.png",
                "supplement_feature/figures/figs2_reproduction.png": "figures/figs2_reproduction.png",
            }
        )
    for source, destination in canonical_outputs.items():
        destination_path = WORKSPACE / "outputs" / destination
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(WORKSPACE / "outputs" / source, destination_path)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
