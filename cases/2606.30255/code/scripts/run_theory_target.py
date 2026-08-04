#!/usr/bin/env python3
"""Run exactly one guarded paper-exact theory target."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import platform
import sys
import time
from pathlib import Path
from typing import Any


WORKSPACE = Path(__file__).resolve().parents[1]
SRC = WORKSPACE / "src"
sys.path.insert(0, str(SRC))

# Keep Matplotlib's cache outside the repository and set it before import.
os.environ.setdefault(
    "MPLCONFIGDIR",
    str(Path(os.environ.get("TMPDIR", "/tmp")) / "pragent-2606.30255-matplotlib"),
)
os.environ.setdefault(
    "XDG_CACHE_HOME",
    str(Path(os.environ.get("TMPDIR", "/tmp")) / "pragent-2606.30255-cache"),
)

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from wigner_model import (  # noqa: E402
    ANGLE_STEP_DEG,
    ASYMMETRIC_LIMIT,
    PAPER_ID,
    SYMMETRIC_LIMIT,
    TARGET_SPECS,
    TargetSpec,
    born_probability_analytic,
    density_diagnostics,
    evaluate_target,
    singlet_fidelity,
)


FORMULA_DEPENDENCIES = [f"EQC{index:03d}" for index in range(1, 7)]
TOLERANCE = 1e-12


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_csv(path: Path, data: dict[str, np.ndarray]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "angle_deg",
        "p_abprime",
        "p_bcprime",
        "p_acprime",
        "wigner",
        "violation_limit",
    ]
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        for index in range(len(data["angle_deg"])):
            writer.writerow({key: f"{float(data[key][index]):.15g}" for key in fieldnames})


def _render_figure(path: Path, spec: TargetSpec, data: dict[str, np.ndarray]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["STIXGeneral", "DejaVu Serif"],
            "mathtext.fontset": "stix",
            "axes.linewidth": 0.9,
            "font.size": 12,
            "axes.labelsize": 17,
            "xtick.labelsize": 11,
            "ytick.labelsize": 11,
            "legend.fontsize": 10,
        }
    )
    figure, axis = plt.subplots(figsize=(12.0, 6.1), dpi=150)
    angle = data["angle_deg"]

    axis.axhspan(spec.y_range[0], 0.0, color="#ff6b6b", alpha=0.32, zorder=0)
    wigner_line = axis.plot(
        angle,
        data["wigner"],
        color="#0000ff",
        linewidth=1.35,
        label="Calculated Wigner Value",
        zorder=4,
    )[0]
    limit_line = axis.plot(
        angle,
        data["violation_limit"],
        color="#ff0000",
        linewidth=1.15,
        linestyle=":",
        label=f"Theoretical Violation Limit at {spec.violation_limit:.3f}",
        zorder=3,
    )[0]
    p_ab_line = axis.plot(
        angle,
        data["p_abprime"],
        color="#d9822b",
        linewidth=1.0,
        label=r"Modelled $P_{++}^{\hat a\hat b^\prime}$",
        zorder=2,
    )[0]
    p_bc_line = axis.plot(
        angle,
        data["p_bcprime"],
        color="#94b83d",
        linewidth=1.0,
        label=r"Modelled $P_{++}^{\hat b\hat c^\prime}$",
        zorder=2,
    )[0]
    p_ac_line = axis.plot(
        angle,
        data["p_acprime"],
        color="#d66ad2",
        linewidth=1.0,
        label=r"Modelled $P_{++}^{\hat a\hat c^\prime}$",
        zorder=2,
    )[0]

    axis.set_xlim(0.0, 360.0)
    axis.set_ylim(*spec.y_range)
    axis.set_xticks(np.arange(0.0, 361.0, 20.0))
    axis.set_xlabel(spec.x_label)
    axis.set_ylabel("Wigner Value (1)")
    axis.grid(True, color="#a8a8a8", linewidth=0.65)
    axis.set_axisbelow(True)
    axis.legend(
        handles=[wigner_line, limit_line, p_ab_line, p_bc_line, p_ac_line],
        loc="upper center",
        bbox_to_anchor=(0.5, -0.15),
        ncol=3,
        frameon=True,
        columnspacing=1.6,
        handlelength=2.4,
    )
    figure.subplots_adjust(left=0.09, right=0.985, top=0.965, bottom=0.29)
    figure.savefig(path, dpi=150, facecolor="white")
    plt.close(figure)


def _check(
    check_id: str,
    condition: bool,
    *,
    observed: Any,
    threshold: Any,
    claim: str,
    essential: bool = True,
    tier: str = "numeric",
) -> dict[str, Any]:
    return {
        "check_id": check_id,
        "status": "passed" if condition else "failed",
        "essential": essential,
        "tier": tier,
        "observed": observed,
        "threshold": threshold,
        "claim": claim,
    }


def _scientific_checks(
    spec: TargetSpec,
    generated: dict[str, np.ndarray],
    analytic: dict[str, np.ndarray],
) -> tuple[list[dict[str, Any]], dict[str, Any], list[str]]:
    diagnostics = density_diagnostics(spec.w, spec.v, spec.xi_rad)
    probability_columns = ["p_abprime", "p_bcprime", "p_acprime"]
    matrix_scalar_error = max(
        float(np.max(np.abs(generated[column] - analytic[column])))
        for column in probability_columns + ["wigner"]
    )
    probability_values = np.concatenate([generated[column] for column in probability_columns])
    wigner_identity_error = float(
        np.max(
            np.abs(
                generated["wigner"]
                - (
                    generated["p_abprime"]
                    + generated["p_bcprime"]
                    - generated["p_acprime"]
                )
            )
        )
    )
    half_period_samples = int(round(180.0 / ANGLE_STEP_DEG))
    periodicity_error = max(
        float(
            np.max(
                np.abs(
                    generated[column][:-half_period_samples]
                    - generated[column][half_period_samples:]
                )
            )
        )
        for column in probability_columns + ["wigner"]
    )
    minimum_index = int(np.argmin(generated["wigner"]))
    maximum_index = int(np.argmax(generated["wigner"]))
    fidelity = singlet_fidelity(spec.w, spec.v)
    fidelity_difference = abs(fidelity - spec.reported_fidelity)

    checks = [
        _check(
            "density_trace",
            diagnostics["trace_error"] <= TOLERANCE,
            observed=diagnostics["trace_error"],
            threshold=TOLERANCE,
            claim="The empirical density matrix has unit trace.",
            tier="analytic",
        ),
        _check(
            "density_hermiticity",
            diagnostics["hermiticity_error"] <= TOLERANCE,
            observed=diagnostics["hermiticity_error"],
            threshold=TOLERANCE,
            claim="The empirical density matrix is Hermitian.",
            tier="analytic",
        ),
        _check(
            "density_positive_semidefinite",
            diagnostics["minimum_eigenvalue"] >= -TOLERANCE,
            observed=diagnostics["minimum_eigenvalue"],
            threshold=f">={-TOLERANCE}",
            claim="The empirical density matrix is positive semidefinite.",
            tier="analytic",
        ),
        _check(
            "matrix_scalar_born_identity",
            matrix_scalar_error <= TOLERANCE,
            observed=matrix_scalar_error,
            threshold=TOLERANCE,
            claim="Explicit matrix Born traces agree with an independent scalar contraction at every angle.",
            tier="analytic",
        ),
        _check(
            "probability_bounds",
            float(np.min(probability_values)) >= -TOLERANCE
            and float(np.max(probability_values)) <= 1.0 + TOLERANCE,
            observed={
                "minimum": float(np.min(probability_values)),
                "maximum": float(np.max(probability_values)),
            },
            threshold="[0, 1]",
            claim="All three joint probabilities remain physical.",
        ),
        _check(
            "wigner_component_identity",
            wigner_identity_error <= TOLERANCE,
            observed=wigner_identity_error,
            threshold=TOLERANCE,
            claim="The Wigner series is exactly the declared signed sum of the three component probabilities.",
            tier="analytic",
        ),
        _check(
            "polarization_periodicity",
            periodicity_error <= TOLERANCE,
            observed=periodicity_error,
            threshold=TOLERANCE,
            claim="All generated theory curves are 180-degree periodic.",
            tier="analytic",
        ),
        _check(
            "full_theory_series_coverage",
            set(generated)
            == {
                "angle_deg",
                "p_abprime",
                "p_bcprime",
                "p_acprime",
                "wigner",
                "violation_limit",
            },
            observed=sorted(generated),
            threshold="angle plus W, three P++ components, and ideal limit",
            claim="Every visible theory curve in the frozen mixed panel is generated, with no experimental series.",
        ),
        _check(
            "reported_fidelity_rounding_consistency",
            fidelity_difference <= 0.006,
            observed={
                "from_reported_w_v": fidelity,
                "paper_reported": spec.reported_fidelity,
                "absolute_difference": fidelity_difference,
            },
            threshold=0.006,
            claim="Fidelity computed from two-decimal paper parameters is consistent with the paper value within rounding sensitivity.",
            essential=False,
        ),
    ]

    if spec.target_id == "T-FIG003":
        angle_30_index = int(round(30.0 / ANGLE_STEP_DEG))
        expected_noisy_minimum = spec.v * SYMMETRIC_LIMIT + (1.0 - spec.v) / 4.0
        checks.append(
            _check(
                "fig003_noisy_symmetric_value",
                abs(float(generated["wigner"][angle_30_index]) - expected_noisy_minimum)
                <= TOLERANCE,
                observed=float(generated["wigner"][angle_30_index]),
                threshold=expected_noisy_minimum,
                claim="At phi=30 degrees the paper's w=1/2 noisy state gives the analytically predicted W.",
                tier="analytic",
            )
        )
    elif spec.target_id == "T-FIG004":
        checks.append(
            _check(
                "fig004_violation_for_full_rotation",
                float(np.max(generated["wigner"])) < 0.0,
                observed=float(np.max(generated["wigner"])),
                threshold="<0",
                claim="The model Wigner value remains negative throughout the common absolute-angle rotation.",
            )
        )
    else:
        checks.extend(
            [
                _check(
                    "fig005_contains_violation_and_classical_regions",
                    float(np.min(generated["wigner"])) < 0.0
                    and float(np.max(generated["wigner"])) > 0.0,
                    observed={
                        "minimum": float(np.min(generated["wigner"])),
                        "maximum": float(np.max(generated["wigner"])),
                    },
                    threshold="minimum<0 and maximum>0",
                    claim="The asymmetric scan contains both violation and non-violation angular regions.",
                ),
                _check(
                    "fig005_ideal_asymmetric_limit",
                    abs(ASYMMETRIC_LIMIT - (1.0 - np.sqrt(3.0)) / 4.0)
                    <= TOLERANCE,
                    observed=ASYMMETRIC_LIMIT,
                    threshold=(1.0 - np.sqrt(3.0)) / 4.0,
                    claim="The red asymmetric reference line equals the independently derived analytic extremum.",
                    tier="analytic",
                ),
            ]
        )

    metrics = {
        **diagnostics,
        "matrix_scalar_max_abs_error": matrix_scalar_error,
        "wigner_identity_max_abs_error": wigner_identity_error,
        "periodicity_max_abs_error": periodicity_error,
        "probability_minimum": float(np.min(probability_values)),
        "probability_maximum": float(np.max(probability_values)),
        "wigner_minimum": float(generated["wigner"][minimum_index]),
        "wigner_minimum_angle_deg": float(generated["angle_deg"][minimum_index]),
        "wigner_maximum": float(generated["wigner"][maximum_index]),
        "wigner_maximum_angle_deg": float(generated["angle_deg"][maximum_index]),
        "wigner_mean_over_unique_period": float(
            np.mean(generated["wigner"][:half_period_samples])
        ),
        "singlet_fidelity_from_reported_parameters": fidelity,
        "paper_reported_fidelity": spec.reported_fidelity,
        "fidelity_absolute_difference": fidelity_difference,
    }
    warnings: list[str] = []
    if fidelity_difference > 5e-4:
        warnings.append(
            "The fidelity recomputed from the paper's rounded w and v differs from "
            f"the printed value by {fidelity_difference:.6g}; the target uses the "
            "explicitly reported curve parameters and records this rounding-sensitive discrepancy."
        )
    return checks, metrics, warnings


def run_target(target_id: str) -> dict[str, Any]:
    guarded_target = os.environ.get("PRAGENT_GUARDED_TARGET_ID")
    guarded_stage = os.environ.get("PRAGENT_GUARDED_STAGE")
    if guarded_target != target_id:
        raise RuntimeError(
            "This runner requires PRAGENT_GUARDED_TARGET_ID to equal the explicit --target."
        )
    if guarded_stage != "final_reproduction":
        raise RuntimeError("This frozen Trial only publishes paper-exact final_reproduction runs.")

    spec = TARGET_SPECS[target_id]
    output_data = WORKSPACE / "outputs" / "data" / f"{spec.slug}.csv"
    output_figure = WORKSPACE / "outputs" / "figures" / f"{spec.slug}.png"
    output_check = WORKSPACE / "outputs" / "checks" / f"{spec.slug}_scientific.json"

    total_start = time.perf_counter()
    numerical_start = time.perf_counter()
    generated = evaluate_target(spec)
    analytic = evaluate_target(spec, probability_fn=born_probability_analytic)
    numerical_seconds = time.perf_counter() - numerical_start

    checks, metrics, warnings = _scientific_checks(spec, generated, analytic)
    _write_csv(output_data, generated)
    rendering_start = time.perf_counter()
    _render_figure(output_figure, spec, generated)
    rendering_seconds = time.perf_counter() - rendering_start

    failed_checks = [check["check_id"] for check in checks if check["status"] == "failed"]
    status = "passed" if not failed_checks else "failed"
    total_seconds_before_check_write = time.perf_counter() - total_start
    payload: dict[str, Any] = {
        "schema_version": 1,
        "check": "target_scientific_evidence",
        "paper_id": PAPER_ID,
        "target_id": target_id,
        "figure_id": spec.figure_id,
        "status": status,
        "artifact_stage": "final_reproduction",
        "parameter_match": "paper_exact",
        "generated_data_provenance": "independent_numerics",
        "analytic_reference_provenance": "analytic_reference",
        "formula_dependencies": FORMULA_DEPENDENCIES,
        "input_contract": {
            "w": spec.w,
            "v": spec.v,
            "xi_rad": spec.xi_rad,
            "scan_kind": spec.scan_kind,
            "spacing_deg": spec.spacing_deg,
            "alice_origin_deg": spec.alice_origin_deg,
            "bob_origin_deg": spec.bob_origin_deg,
            "angle_start_deg": 0.0,
            "angle_stop_deg": 360.0,
            "angle_step_deg": ANGLE_STEP_DEG,
            "experimental_data_used": False,
            "source_pixels_used": False,
        },
        "output_contract": {
            "visible_generated_series": [
                "wigner",
                "p_abprime",
                "p_bcprime",
                "p_acprime",
                "violation_limit",
            ],
            "experimental_series_generated": [],
            "data_path": str(output_data.relative_to(WORKSPACE)),
            "figure_path": str(output_figure.relative_to(WORKSPACE)),
        },
        "checks": checks,
        "physics_assertions": [
            {
                "assertion_id": check["check_id"],
                "tier": check["tier"],
                "essential": check["essential"],
                "status": check["status"],
                "evidence": f"outputs/checks/{spec.slug}_scientific.json#{check['check_id']}",
                "claim": check["claim"],
            }
            for check in checks
        ],
        "metrics": metrics,
        "warnings": warnings,
        "failed_checks": failed_checks,
        "timing": {
            "clock": "time.perf_counter",
            "numerical_seconds": numerical_seconds,
            "rendering_seconds": rendering_seconds,
            "total_seconds_before_check_write": total_seconds_before_check_write,
        },
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "numpy": np.__version__,
            "matplotlib": matplotlib.__version__,
        },
        "input_fingerprints": {
            "EQUATION_CARDS.json": _sha256(WORKSPACE / "EQUATION_CARDS.json"),
            "DERIVATION.md": _sha256(WORKSPACE / "DERIVATION.md"),
            "physics_reproduction_project.json": _sha256(
                WORKSPACE / "physics_reproduction_project.json"
            ),
            "src/wigner_model.py": _sha256(WORKSPACE / "src" / "wigner_model.py"),
            "scripts/run_theory_target.py": _sha256(
                WORKSPACE / "scripts" / "run_theory_target.py"
            ),
        },
    }
    output_check.parent.mkdir(parents=True, exist_ok=True)
    output_check.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    payload["artifacts"] = {
        "data": str(output_data),
        "figure": str(output_figure),
        "check": str(output_check),
    }
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", required=True, choices=sorted(TARGET_SPECS))
    args = parser.parse_args()
    try:
        result = run_target(args.target)
    except (RuntimeError, ValueError) as exc:
        print(json.dumps({"status": "failed", "target_id": args.target, "error": str(exc)}))
        return 2
    print(
        json.dumps(
            {
                "status": result["status"],
                "target_id": result["target_id"],
                "metrics": result["metrics"],
                "timing": result["timing"],
                "artifacts": result["artifacts"],
                "warnings": result["warnings"],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
