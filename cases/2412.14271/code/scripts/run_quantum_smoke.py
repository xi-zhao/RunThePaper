#!/usr/bin/env python3
"""Minimal QuTiP run proving that the isolated dependency path is clean."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.dicke import trajectory_density


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    with Path(args.config).open(encoding="utf-8") as handle:
        p = json.load(handle)["parameters"]
    result = trajectory_density(
        p["N"], p["M"], p["lambda"], omega_c=p["omega_c"], omega_a=p["omega_a"],
        kappa1=p["kappa1"], kappa2=p["kappa2"], trajectories=p["trajectories"],
        final_time=p["final_time"], seed=p["seed"],
    )
    output = Path("outputs/checks/quantum_isolation_smoke.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        json.dump({"trace_error": result["trace_error"], "passed": result["trace_error"] < 1e-10}, handle, indent=2)
        handle.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
