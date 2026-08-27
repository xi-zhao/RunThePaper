#!/usr/bin/env python3
"""Close the Fig. 3(a) direct C_y integration gate.

The published cylinder phase diagram draws its red boundary from the analytic
non-Bloch band-touching condition. This script independently verifies the
panel's claim with two computations that never use that formula as input:

1. the non-Bloch Chern number C_y, integrated with biorthogonal
   Fukui-Hatsugai-Suzuki links on a (gamma, m) grid — validating that C_y=1
   left of the strip, C_y=0 right of it, and the jump falls inside the strip;
2. a dense closed-form min|E| search at each strip midpoint — validating that
   the strip between the boundaries is genuinely gapless.

Inside the gapless strip the sorted-band FHS integer is not a claim of the
panel and is recorded but not judged.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nonhermitian_chern import (  # noqa: E402
    cylinder_non_bloch_gap_boundaries,
    non_bloch_bulk_min_abs_energy,
    non_bloch_chern_number,
)

GAP_THRESHOLD = 0.02
STRIP_GAPLESS_TOLERANCE = 0.05


def main() -> int:
    # Validate exactly the published Fig. 3(a) claim domain
    # (m in [1.29, 2.71], gamma in [0, 0.5]); outside it the model has an
    # additional kx=pi band-touching boundary that the panel does not claim.
    gamma_values = np.linspace(0.025, 0.5, 20)
    m_values = np.linspace(1.3, 2.7, 57)
    m_step = float(m_values[1] - m_values[0])

    rows: list[dict[str, object]] = []
    gamma_checks: list[dict[str, object]] = []

    for gamma in gamma_values:
        lower, upper = cylinder_non_bloch_gap_boundaries(float(gamma))
        chern_by_m: list[tuple[float, int | None]] = []
        for m in m_values:
            chern = non_bloch_chern_number(float(gamma), float(m), gap_threshold=GAP_THRESHOLD)
            chern_by_m.append((float(m), chern))
            rows.append(
                {
                    "gamma": float(gamma),
                    "m": float(m),
                    "chern": "" if chern is None else int(chern),
                    "in_strip": bool(lower - m_step <= m <= upper + m_step),
                    "analytic_lower": lower,
                    "analytic_upper": upper,
                }
            )
        strip_mid = 0.5 * (lower + upper)
        strip_min_abs_E = non_bloch_bulk_min_abs_energy(float(gamma), strip_mid)
        gamma_checks.append(
            check_gamma_slice(float(gamma), chern_by_m, lower, upper, m_step, strip_mid, strip_min_abs_E)
        )

    star_chern = non_bloch_chern_number(0.2, 1.717, gap_threshold=GAP_THRESHOLD)

    data_path = ROOT / "outputs/data/fig3a_direct_cy_integration.csv"
    checks_path = ROOT / "outputs/checks/fig3a_direct_cy_integration.json"
    data_path.parent.mkdir(parents=True, exist_ok=True)
    checks_path.parent.mkdir(parents=True, exist_ok=True)
    with data_path.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["gamma", "m", "chern", "in_strip", "analytic_lower", "analytic_upper"],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)

    failed_slices = [check for check in gamma_checks if not check["passed"]]
    gate_flags = {
        "star_point_chern_one": star_chern == 1,
        "all_gamma_slices_pass": not failed_slices,
    }

    checks = {
        "target_id": "T002",
        "gate": "direct_cy_integration_gate",
        "status": "passed" if all(gate_flags.values()) else "failed",
        "method": "biorthogonal_fukui_hatsugai_suzuki_on_non_bloch_torus",
        "band_selection": "lower_real_part_band",
        "gapless_probe": "closed_form_min_abs_E_dense_search_at_strip_midpoint",
        "grid": {
            "gamma_points": len(gamma_values),
            "m_points": len(m_values),
            "gamma_range": [float(gamma_values[0]), float(gamma_values[-1])],
            "m_range": [float(m_values[0]), float(m_values[-1])],
            "kx_points": 41,
            "ky_points": 41,
            "m_step": m_step,
        },
        "tolerances": {
            "fhs_gap_threshold": GAP_THRESHOLD,
            "strip_gapless_min_abs_E": STRIP_GAPLESS_TOLERANCE,
            "region_slack_m_steps": 1,
        },
        "star_point": {"m": 1.717, "gamma": 0.2, "chern": star_chern},
        "gate_flags": gate_flags,
        "failed_slices": failed_slices,
        "gamma_checks": gamma_checks,
        "data_path": "outputs/data/fig3a_direct_cy_integration.csv",
        "notes": [
            "C_y is integrated directly with biorthogonal FHS links; the analytic band-touching boundary is validated, not used as the classification source.",
            "The claim validated per gamma slice: C_y=1 everywhere left of the strip, C_y=0 everywhere right of it, a single jump inside the strip, and independently confirmed gaplessness at the strip midpoint.",
            "Inside the strip the sorted-band FHS integer is recorded in the CSV but is not part of the panel's claim.",
        ],
    }
    checks_path.write_text(json.dumps(checks, indent=2) + "\n")
    print(json.dumps({k: checks[k] for k in ["status", "gate_flags", "star_point"]}, indent=2))
    if failed_slices:
        print(json.dumps({"failed_slices": failed_slices[:4]}, indent=2))
    return 0 if checks["status"] == "passed" else 1


def check_gamma_slice(
    gamma: float,
    chern_by_m: list[tuple[float, int | None]],
    lower: float,
    upper: float,
    m_step: float,
    strip_mid: float,
    strip_min_abs_E: float,
) -> dict[str, object]:
    left = [(m, c) for m, c in chern_by_m if m < lower - m_step]
    right = [(m, c) for m, c in chern_by_m if m > upper + m_step]
    left_pure = all(c == 1 for _, c in left)
    right_pure = all(c == 0 for _, c in right)

    # The C_y jump: last m with C=1 and first m with C=0 must both fall
    # inside the strip (with one grid step of slack), and be adjacent in the
    # non-None sequence (single jump).
    last_one = max((m for m, c in chern_by_m if c == 1), default=None)
    first_zero = min((m for m, c in chern_by_m if c == 0), default=None)
    jump_inside_strip = (
        last_one is not None
        and first_zero is not None
        and last_one < first_zero
        and lower - m_step <= 0.5 * (last_one + first_zero) <= upper + m_step
    )
    integer_sequence = [c for _, c in chern_by_m if c is not None]
    single_jump = all(
        not (a == 0 and b == 1) for a, b in zip(integer_sequence, integer_sequence[1:])
    )
    strip_gapless = strip_min_abs_E < STRIP_GAPLESS_TOLERANCE

    passed = bool(left_pure and right_pure and jump_inside_strip and single_jump and strip_gapless)
    return {
        "gamma": gamma,
        "analytic_lower": lower,
        "analytic_upper": upper,
        "left_pure_chern_one": bool(left_pure),
        "right_pure_chern_zero": bool(right_pure),
        "last_chern_one_m": last_one,
        "first_chern_zero_m": first_zero,
        "jump_inside_strip": bool(jump_inside_strip),
        "single_jump": bool(single_jump),
        "strip_midpoint_m": strip_mid,
        "strip_midpoint_min_abs_E": strip_min_abs_E,
        "strip_gapless": bool(strip_gapless),
        "passed": passed,
    }


if __name__ == "__main__":
    raise SystemExit(main())
