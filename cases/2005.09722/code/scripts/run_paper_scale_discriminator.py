#!/usr/bin/env python3
"""Attest paper-scale code readiness without claiming paper-scale reproduction."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from backends import run_backend_benchmark  # noqa: E402
from paper_scale import load_campaign  # noqa: E402


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def run_discriminator(
    config_path: Path,
    acceptance_path: Path,
    output_root: Path,
) -> dict[str, object]:
    """Run full-size backend probes plus a reduced all-family canary.

    The benchmark exercises the published matrix sizes but only for the frozen
    short probe.  The campaign remains in smoke mode.  Consequently this
    result can exclude a basic implementation failure, but it cannot establish
    either paper-scale scientific agreement or an objective compute shortfall.
    """

    config = json.loads(config_path.read_text(encoding="utf-8"))
    resource_benchmark = run_backend_benchmark(
        config["backend_benchmark"], smoke=False
    )
    if resource_benchmark["status"] != "passed":
        raise RuntimeError("local paper-size backend benchmark failed")

    backend = str(resource_benchmark["selected_backend"])
    campaign = load_campaign(
        config_path,
        output_root=output_root,
        smoke=True,
        backend=backend,
    )
    smoke_benchmark = run_backend_benchmark(
        config["backend_benchmark"], smoke=True
    )
    _write_json(output_root / "checks" / "backend_benchmark.json", smoke_benchmark)
    _write_json(
        output_root / "checks" / "resource_benchmark.json", resource_benchmark
    )

    run = campaign.run_all(resume=True)
    aggregate = campaign.aggregate_all()
    acceptance = campaign.accept(acceptance_path)
    summary: dict[str, object] = {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "status": "passed" if acceptance["status"] == "machine_passed" else "failed",
        "execution_mode": "paper_size_backend_probe_plus_reduced_all_family_canary",
        "backend": backend,
        "paper_scale_campaign_executed": False,
        "scientific_coverage_promoted": False,
        "compute_shortfall_established": False,
        "resource_boundary": (
            "Published matrix sizes were probed locally, but the full 40,800-trajectory "
            "campaign and the declared A100 benchmark were not run. Code readiness is "
            "attested; paper-scale resource sufficiency remains unmeasured."
        ),
        "resource_benchmark": resource_benchmark,
        "canary_run": run,
        "canary_aggregate": aggregate,
        "canary_acceptance": acceptance,
    }
    _write_json(output_root / "checks" / "discriminating_canary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--acceptance", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()

    def resolve(path: Path) -> Path:
        return path if path.is_absolute() else WORKSPACE / path

    result = run_discriminator(
        resolve(args.config),
        resolve(args.acceptance),
        resolve(args.output_root),
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
