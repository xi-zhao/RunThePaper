"""One data-first pipeline for every numerical panel in arXiv:2105.08076."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

from .audit import phase_label_checks, relevance_inequality_checks, wick_sign_checks
from .gaussian import EnsembleResult, simulate_ensemble
from .observables import chord_length
from .rendering import render_all
from .scaling import (
    fit_correlation_size,
    fit_effective_central_charge,
    fit_entropy_size,
    local_power_slope,
)
from .theory import dark_state_exponents

TARGET_IDS = [f"T{index:03d}" for index in range(1, 10)]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"refusing to write empty dataset: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _key(length: int, exponent: float, gamma: float) -> tuple[int, float, float]:
    return length, round(exponent, 12), round(gamma, 12)


def _physics_cases(parameters: dict[str, Any]) -> list[dict[str, Any]]:
    return [dict(item) for item in parameters["representative_cases"]]


def _half_rows(
    results: dict[tuple[int, float, float], EnsembleResult],
    cases: list[dict[str, Any]],
    sizes: list[int],
    value_key: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for case in cases:
        for length in sizes:
            result = results[_key(length, float(case["p"]), float(case["gamma"]))]
            half = result.half_chain()
            rows.append(
                {
                    "physics_phase": case["physics_phase"],
                    "caption_phase": case["caption_phase"],
                    "gamma": case["gamma"],
                    "p": case["p"],
                    "L": length,
                    value_key: half[value_key],
                    f"{value_key}_sem": half.get(f"{value_key}_sem", 0.0),
                    "parameter_status": "paper_subset_reconstructed_numerics",
                }
            )
    return rows


def _simulate_grid(
    parameters: dict[str, Any],
) -> dict[tuple[int, float, float], EnsembleResult]:
    dynamics = parameters["dynamics"]
    sizes = [int(value) for value in parameters["sizes"]]
    exponents = [float(value) for value in parameters["p_values"]]
    gammas = [float(value) for value in parameters["gamma_values"]]
    results: dict[tuple[int, float, float], EnsembleResult] = {}
    job_index = 0
    for gamma in gammas:
        for exponent in exponents:
            for length in sizes:
                seed = int(parameters["seed_base"]) + job_index * int(
                    parameters["seed_stride"]
                )
                results[_key(length, exponent, gamma)] = simulate_ensemble(
                    length=length,
                    exponent=exponent,
                    gamma=gamma,
                    dt=float(dynamics["dt"]),
                    burn_time=float(dynamics["burn_time"]),
                    sample_time=float(dynamics["sample_time"]),
                    sample_interval=float(dynamics["sample_interval"]),
                    trajectories=int(dynamics["trajectories"]),
                    seed_base=seed,
                    entropy_origins=int(dynamics["entropy_origins"]),
                )
                job_index += 1
    return results


def _write_ensemble_summary(
    path: Path,
    results: dict[tuple[int, float, float], EnsembleResult],
) -> None:
    rows: list[dict[str, Any]] = []
    for (length, exponent, gamma), result in sorted(results.items()):
        chords = chord_length(length, result.ell)
        for index, ell in enumerate(result.ell):
            rows.append(
                {
                    "L": length,
                    "p": exponent,
                    "gamma": gamma,
                    "ell": ell,
                    "chord_length": chords[index],
                    "entropy": result.entropy_mean[index],
                    "entropy_sem": result.entropy_sem[index],
                    "correlation_positive": result.correlation_positive_mean[index],
                    "correlation_positive_sem": result.correlation_positive_sem[index],
                    "correlation_connected": result.correlation_connected_mean[index],
                    "trajectories": result.trajectories,
                    "samples_per_trajectory": result.samples_per_trajectory,
                    "max_invariant_residual": result.max_invariant_residual,
                    "stationary_relative_drift": result.stationary_relative_drift,
                }
            )
    _write_csv(path, rows)


def _target_datasets(
    parameters: dict[str, Any],
    results: dict[tuple[int, float, float], EnsembleResult],
    data_dir: Path,
) -> dict[str, Any]:
    sizes = [int(value) for value in parameters["sizes"]]
    exponents = [float(value) for value in parameters["p_values"]]
    cases = _physics_cases(parameters)
    largest = max(sizes)

    # T001: reduced-scale phase map.
    rows_t001 = []
    for gamma in parameters["gamma_values"]:
        for exponent in exponents:
            result = results[_key(largest, exponent, float(gamma))]
            fit = fit_effective_central_charge(largest, result.ell, result.entropy_mean)
            rows_t001.append(
                {
                    "gamma": gamma,
                    "p": exponent,
                    "inverse_p": 1.0 / exponent,
                    "L": largest,
                    "c_eff": fit.parameters["c"],
                    "fit_relative_rms": fit.relative_rms,
                    "parameter_status": "reduced_scale",
                }
            )
    _write_csv(data_dir / "T001_phase_map.csv", rows_t001)

    # T002/T003: size-derived exponents and analytic dark-state line.
    rows_t002: list[dict[str, Any]] = []
    rows_t003: list[dict[str, Any]] = []
    for gamma in parameters["exponent_gamma_values"]:
        for exponent in exponents:
            series = [
                results[_key(length, exponent, float(gamma))].half_chain()
                for length in sizes
            ]
            entropy_values = np.asarray(
                [item["entropy"] for item in series], dtype=float
            )
            correlation_values = np.asarray(
                [item["correlation_positive"] for item in series], dtype=float
            )
            entropy_fit = fit_entropy_size(
                np.asarray(sizes, dtype=float), entropy_values
            )
            correlation_fit = fit_correlation_size(
                np.asarray(sizes, dtype=float), correlation_values
            )
            direct_b = local_power_slope(np.asarray(sizes, dtype=float), entropy_values)
            theory_a = ""
            theory_b = ""
            if 1.0 < exponent < 1.5:
                theory_a, theory_b = dark_state_exponents(exponent)
            rows_t002.append(
                {
                    "gamma": gamma,
                    "p": exponent,
                    "inverse_p": 1.0 / exponent,
                    "fitted_a": correlation_fit.parameters["a"],
                    "direct_a": correlation_fit.parameters["direct_a"],
                    "theory_a": theory_a,
                    "fit_relative_rms": correlation_fit.relative_rms,
                    "parameter_status": "reduced_scale",
                }
            )
            rows_t003.append(
                {
                    "gamma": gamma,
                    "p": exponent,
                    "inverse_p": 1.0 / exponent,
                    "fitted_b": entropy_fit.parameters["b"],
                    "direct_b": direct_b,
                    "theory_b": theory_b,
                    "fit_relative_rms": entropy_fit.relative_rms,
                    "parameter_status": "reduced_scale",
                }
            )
    _write_csv(data_dir / "T002_correlation_exponent.csv", rows_t002)
    _write_csv(data_dir / "T003_entropy_exponent.csv", rows_t003)

    # T004/T005: representative parameter pairs.  Physics/caption labels are
    # kept as separate columns because the source captions appear swapped.
    rows_t004 = _half_rows(results, cases, sizes, "entropy")
    rows_t005 = _half_rows(results, cases, sizes, "correlation_positive")
    _write_csv(data_dir / "T004_entropy_size.csv", rows_t004)
    _write_csv(data_dir / "T005_correlation_size.csv", rows_t005)

    # T006: c_eff versus p and size for both paper-highlighted gamma values.
    rows_t006: list[dict[str, Any]] = []
    for gamma in parameters["central_charge_gamma_values"]:
        for length in sizes:
            for exponent in exponents:
                result = results[_key(length, exponent, float(gamma))]
                fit = fit_effective_central_charge(
                    length, result.ell, result.entropy_mean
                )
                rows_t006.append(
                    {
                        "gamma": gamma,
                        "L": length,
                        "p": exponent,
                        "inverse_p": 1.0 / exponent,
                        "c_eff": fit.parameters["c"],
                        "fit_relative_rms": fit.relative_rms,
                        "parameter_status": "reduced_scale",
                    }
                )
    _write_csv(data_dir / "T006_effective_central_charge.csv", rows_t006)

    # T007: algebraic case profile and independently normalized analytic slopes.
    algebraic = next(item for item in cases if item["physics_phase"] == "algebraic")
    result = results[_key(largest, float(algebraic["p"]), float(algebraic["gamma"]))]
    a, b = dark_state_exponents(float(algebraic["p"]))
    ell = result.ell
    anchor = int(np.argmin(np.abs(ell - largest / 4)))
    theory_entropy = ell**b
    theory_entropy *= result.entropy_mean[anchor] / theory_entropy[anchor]
    theory_rescaled_correlation = ell ** (2.0 - a)
    observed_rescaled = 20.0 * ell**2 * result.correlation_positive_mean
    theory_rescaled_correlation *= (
        observed_rescaled[anchor] / theory_rescaled_correlation[anchor]
    )
    rows_t007 = [
        {
            "L": largest,
            "gamma": algebraic["gamma"],
            "p": algebraic["p"],
            "ell": ell[index],
            "entropy": result.entropy_mean[index],
            "correlation_positive": result.correlation_positive_mean[index],
            "theory_entropy": theory_entropy[index],
            "theory_rescaled_correlation": theory_rescaled_correlation[index],
            "theory_a": a,
            "theory_b": b,
            "parameter_status": "reduced_scale",
        }
        for index in range(ell.size)
    ]
    _write_csv(data_dir / "T007_algebraic_scaling.csv", rows_t007)

    # T008/T009: all subsystem curves for the three printed parameter pairs.
    rows_t008: list[dict[str, Any]] = []
    rows_t009: list[dict[str, Any]] = []
    for case in cases:
        for length in sizes:
            current = results[_key(length, float(case["p"]), float(case["gamma"]))]
            chords = chord_length(length, current.ell)
            for index, ell_value in enumerate(current.ell):
                common = {
                    "physics_phase": case["physics_phase"],
                    "caption_phase": case["caption_phase"],
                    "gamma": case["gamma"],
                    "p": case["p"],
                    "L": length,
                    "ell": ell_value,
                    "chord_length": chords[index],
                    "parameter_status": "paper_subset_reconstructed_numerics",
                }
                rows_t008.append(
                    {
                        **common,
                        "entropy": current.entropy_mean[index],
                        "entropy_sem": current.entropy_sem[index],
                    }
                )
                rows_t009.append(
                    {
                        **common,
                        "correlation_positive": current.correlation_positive_mean[
                            index
                        ],
                        "correlation_positive_sem": current.correlation_positive_sem[
                            index
                        ],
                    }
                )
    _write_csv(data_dir / "T008_subsystem_entropy.csv", rows_t008)
    _write_csv(data_dir / "T009_subsystem_correlation.csv", rows_t009)

    return {
        "rows": {
            "T001": rows_t001,
            "T002": rows_t002,
            "T003": rows_t003,
            "T004": rows_t004,
            "T005": rows_t005,
            "T006": rows_t006,
            "T007": rows_t007,
            "T008": rows_t008,
            "T009": rows_t009,
        }
    }


def _find(rows: list[dict[str, Any]], **conditions: Any) -> dict[str, Any]:
    for row in rows:
        if all(row[key] == value for key, value in conditions.items()):
            return row
    raise KeyError(conditions)


def _checks(
    config: dict[str, Any],
    results: dict[tuple[int, float, float], EnsembleResult],
    datasets: dict[str, Any],
) -> dict[str, Any]:
    parameters = config["parameters"]
    rows = datasets["rows"]
    sizes = [int(value) for value in parameters["sizes"]]
    largest = max(sizes)
    cases = {item["physics_phase"]: item for item in _physics_cases(parameters)}

    def half(phase: str, length: int) -> dict[str, float]:
        case = cases[phase]
        return results[
            _key(length, float(case["p"]), float(case["gamma"]))
        ].half_chain()

    algebraic_entropy = np.asarray(
        [half("algebraic", length)["entropy"] for length in sizes]
    )
    cft_entropy = np.asarray([half("CFT", length)["entropy"] for length in sizes])
    area_entropy = np.asarray([half("area_law", length)["entropy"] for length in sizes])
    algebraic_corr = np.asarray(
        [half("algebraic", length)["correlation_positive"] for length in sizes]
    )
    cft_corr = np.asarray(
        [half("CFT", length)["correlation_positive"] for length in sizes]
    )
    area_corr = np.asarray(
        [half("area_law", length)["correlation_positive"] for length in sizes]
    )
    length_array = np.asarray(sizes, dtype=float)
    corr_slopes = {
        "algebraic": -local_power_slope(length_array, algebraic_corr),
        "CFT": -local_power_slope(length_array, cft_corr),
        "area_law": -local_power_slope(length_array, area_corr),
    }
    entropy_slopes = {
        "algebraic": local_power_slope(length_array, algebraic_entropy),
        "CFT": local_power_slope(length_array, cft_entropy),
        "area_law": local_power_slope(length_array, area_entropy),
    }
    theory_a, theory_b = dark_state_exponents(1.25)
    t002_anchor = _find(rows["T002"], gamma=0.3, p=1.25)
    t003_anchor = _find(rows["T003"], gamma=0.3, p=1.25)

    c_alg_small = _find(rows["T006"], gamma=0.3, L=min(sizes), p=1.25)["c_eff"]
    c_alg_large = _find(rows["T006"], gamma=0.3, L=largest, p=1.25)["c_eff"]
    c_area = _find(rows["T001"], gamma=2.0, p=5.0)["c_eff"]
    c_cft = _find(rows["T001"], gamma=0.3, p=5.0)["c_eff"]
    c_alg = _find(rows["T001"], gamma=0.3, p=1.25)["c_eff"]
    max_invariant = max(item.max_invariant_residual for item in results.values())
    max_drift = max(item.stationary_relative_drift for item in results.values())

    assertions = {
        "T001": {
            "passed": bool(c_alg > c_cft > c_area),
            "parameter_status": "reduced_scale",
            "c_algebraic": c_alg,
            "c_cft": c_cft,
            "c_area_law": c_area,
        },
        "T002": {
            "passed": bool(abs(float(t002_anchor["direct_a"]) - theory_a) <= 0.55),
            "parameter_status": "reduced_scale",
            "direct_a": t002_anchor["direct_a"],
            "theory_a": theory_a,
        },
        "T003": {
            # Fig. 1(e) reports b from the mixed finite-size ansatz printed in
            # Supplement Eq. (9).  The raw log-log slope is only a diagnostic:
            # the additive logarithm and offset make it a different observable.
            "passed": bool(abs(float(t003_anchor["fitted_b"]) - theory_b) <= 0.25),
            "parameter_status": "reduced_scale",
            "fitted_b": t003_anchor["fitted_b"],
            "direct_b": t003_anchor["direct_b"],
            "theory_b": theory_b,
        },
        "T004": {
            "passed": bool(
                algebraic_entropy[-1] > cft_entropy[-1] > 1.5 * area_entropy[-1]
            ),
            "parameter_status": "paper_subset_reconstructed_numerics",
            "largest_L_entropy_order": [
                float(algebraic_entropy[-1]),
                float(cft_entropy[-1]),
                float(area_entropy[-1]),
            ],
        },
        "T005": {
            "passed": bool(
                corr_slopes["algebraic"] < corr_slopes["CFT"] < corr_slopes["area_law"]
            ),
            "parameter_status": "paper_subset_reconstructed_numerics",
            "direct_exponents": corr_slopes,
        },
        "T006": {
            "passed": bool(c_alg_large > 1.5 * c_alg_small),
            "parameter_status": "reduced_scale",
            "c_ratio_algebraic": float(c_alg_large / max(c_alg_small, 1e-12)),
        },
        "T007": {
            # The analytic identity alone cannot validate a simulation panel.
            # Require the independently generated finite-size observables to
            # approach both printed exponents as well.
            "passed": bool(
                abs(float(t002_anchor["direct_a"]) - theory_a) <= 0.35
                and abs(float(t003_anchor["fitted_b"]) - theory_b) <= 0.25
                and abs(
                    float(t002_anchor["direct_a"])
                    + float(t003_anchor["fitted_b"])
                    - 2.0
                )
                <= 0.35
            ),
            "parameter_status": "paper_subset_reconstructed_numerics",
            "theory_a": theory_a,
            "theory_b": theory_b,
            "simulation_fitted_entropy_exponent": t003_anchor["fitted_b"],
            "simulation_direct_correlation_exponent": t002_anchor["direct_a"],
            "simulation_entropy_slope": entropy_slopes["algebraic"],
            "simulation_correlation_slope": corr_slopes["algebraic"],
        },
        "T008": {
            "passed": bool(entropy_slopes["algebraic"] > entropy_slopes["CFT"] > 0),
            "parameter_status": "paper_subset_reconstructed_numerics",
            "entropy_slopes": entropy_slopes,
        },
        "T009": {
            "passed": bool(corr_slopes["algebraic"] < corr_slopes["CFT"]),
            "parameter_status": "paper_subset_reconstructed_numerics",
            "correlation_slopes": corr_slopes,
        },
    }
    return {
        "schema_version": 1,
        "paper_id": "2105.08076",
        "profile": config["profile"],
        "artifact_stage": config["artifact_stage"],
        "all_assertions_passed": all(item["passed"] for item in assertions.values()),
        "assertions": assertions,
        "physics": {
            "maximum_gaussian_invariant_residual": max_invariant,
            "maximum_stationary_relative_drift": max_drift,
            "theory_exponent_identity_residual": abs(theory_a + theory_b - 2.0),
        },
        "source_boundary": {
            "author_code_used": False,
            "author_numeric_arrays_used": False,
            "source_pixels_used_as_numeric_input": False,
            "source_figures_read_by_runner": False,
        },
    }


def _consistency_checks(
    results: dict[tuple[int, float, float], EnsembleResult],
    parameters: dict[str, Any],
) -> dict[str, Any]:
    sizes = [int(value) for value in parameters["sizes"]]
    largest = max(sizes)
    algebraic = results[_key(largest, 1.25, 0.3)].half_chain()
    cft = results[_key(largest, 5.0, 0.3)].half_chain()
    return {
        "schema_version": 2,
        "paper_id": "2105.08076",
        "paper_error_candidate_emitted": False,
        "discrepancies": {
            "DISC_WICK_SIGN": {
                "classification": "inconclusive",
                "source_pinpoint": "Main Eq. (4b), MainPRL.tex lines 128-133",
                "checks": wick_sign_checks(),
                "fresh_review_required": True,
            },
            "DISC_RELEVANCE_INEQUALITY": {
                "classification": "inconclusive",
                "source_pinpoint": "MainPRL.tex line 163 / PDF page 4 lower-left paragraph",
                "checks": relevance_inequality_checks(),
                "fresh_review_required": True,
            },
            "DISC_PHASE_LABEL_SWAP": {
                "classification": "inconclusive",
                "source_pinpoint": "Main Fig. 2 caption and Supplement Fig. 1 caption",
                "analytic_checks": phase_label_checks(),
                "independent_simulation_check": {
                    "largest_L": largest,
                    "p1_25_gamma0_3_entropy": algebraic["entropy"],
                    "p5_gamma0_3_entropy": cft["entropy"],
                    "long_range_pair_grows_more": algebraic["entropy"] > cft["entropy"],
                },
                "fresh_review_required": True,
            },
        },
    }


def run(config_path: Path, workspace: Path) -> dict[str, Any]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    parameters = config["parameters"]
    data_dir = workspace / "outputs" / "data"
    figure_dir = workspace / "outputs" / "figures"
    check_dir = workspace / "outputs" / "checks"
    data_dir.mkdir(parents=True, exist_ok=True)
    figure_dir.mkdir(parents=True, exist_ok=True)
    check_dir.mkdir(parents=True, exist_ok=True)

    results = _simulate_grid(parameters)
    _write_ensemble_summary(data_dir / "ensemble_summary.csv", results)
    datasets = _target_datasets(parameters, results, data_dir)
    render_all(data_dir, figure_dir)

    checks = _checks(config, results, datasets)
    consistency = _consistency_checks(results, parameters)
    _write_json(check_dir / "target_checks.json", checks)
    _write_json(check_dir / "paper_consistency_checks.json", consistency)

    generated_paths = sorted(
        [
            *data_dir.glob("*.csv"),
            *figure_dir.glob("*.png"),
            check_dir / "target_checks.json",
            check_dir / "paper_consistency_checks.json",
        ]
    )
    manifest = {
        "schema_version": 1,
        "paper_id": "2105.08076",
        "profile": config["profile"],
        "generated_data_provenance": "independent_numerics",
        "scientific_config_sha256": _sha256(config_path),
        "source_boundary": checks["source_boundary"],
        "outputs": [
            {
                "path": path.relative_to(workspace).as_posix(),
                "sha256": _sha256(path),
                "bytes": path.stat().st_size,
            }
            for path in generated_paths
        ],
    }
    _write_json(check_dir / "generated_data_manifest.json", manifest)
    return {"checks": checks, "consistency": consistency, "manifest": manifest}
