#!/usr/bin/env python3
"""Recompute the paper's decisive Wigner-negativity witness values."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np


CODE_ROOT = Path(__file__).resolve().parents[1]
CASE_ROOT = CODE_ROOT.parent
sys.path.insert(0, str(CODE_ROOT))

from src.wigner_gme import (  # noqa: E402
    SOURCE_PRINTED_GME_BOUND,
    STATE_DERIVED_GME_BOUND,
    W_STATE_GME_THRESHOLD,
    characteristic_witness_spectrum,
    illustrative_slice_metrics,
    illustrative_state_norm,
    smoothed_origin_exact,
    unique_pairwise_differences,
    w_state_critical_radius,
    w_state_disk_volume,
)


def main() -> int:
    overview = illustrative_slice_metrics(
        radial_order=800,
        angular_order=3072,
        radial_cutoff=4.0,
    )
    eigenvalues = characteristic_witness_spectrum()
    disk_volume = float(w_state_disk_volume(0.7))
    critical_radius = w_state_critical_radius()
    witness = -float(eigenvalues[0])

    checks = {
        "state_normalized": bool(np.isclose(illustrative_state_norm(), 1.0)),
        "state_derived_bound_crossed": bool(
            float(overview["negativity_volume"]) > STATE_DERIVED_GME_BOUND
        ),
        "source_printed_bound_crossed": bool(
            float(overview["negativity_volume"]) > SOURCE_PRINTED_GME_BOUND
        ),
        "disk_threshold_crossed": bool(disk_volume > W_STATE_GME_THRESHOLD),
        "one_negative_characteristic_eigenvalue": bool(np.sum(eigenvalues < 0.0) == 1),
        "nineteen_unique_differences": len(unique_pairwise_differences()) == 19,
    }
    payload = {
        "status": "passed" if all(
            value
            for key, value in checks.items()
            if key != "source_printed_bound_crossed"
        ) and not checks["source_printed_bound_crossed"] else "failed",
        "overview": {
            "negativity_volume": float(overview["negativity_volume"]),
            "state_derived_gme_bound": STATE_DERIVED_GME_BOUND,
            "source_printed_gme_bound": SOURCE_PRINTED_GME_BOUND,
            "state_derived_margin": float(overview["corrected_margin"]),
            "source_printed_margin": float(overview["printed_margin"]),
            "smoothed_origin": smoothed_origin_exact(),
        },
        "w_state": {
            "critical_radius": critical_radius,
            "disk_volume_at_0_7": disk_volume,
            "gme_threshold": W_STATE_GME_THRESHOLD,
            "certification_margin": disk_volume - W_STATE_GME_THRESHOLD,
            "characteristic_witness": witness,
            "eigenvalues": [float(value) for value in eigenvalues],
            "unique_difference_count": len(unique_pairwise_differences()),
            "independent_measurement_count": 10,
        },
        "checks": checks,
        "source_inconsistency": {
            "state_derived_numerator": 52,
            "source_printed_numerator": 56,
            "consequence": (
                "The numerical volume clears the threshold derived from the "
                "printed state but not the separately printed threshold."
            ),
        },
    }

    output = CASE_ROOT / "outputs" / "checks" / "public_reproduction_check.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0 if payload["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
