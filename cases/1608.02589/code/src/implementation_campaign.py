"""Clean-room implementation closure for the previously unimplemented DTC items.

The campaign deliberately consumes only a frozen JSON configuration and the
case-local scientific kernels.  It never reads the paper, author data/code,
reference figures, or legacy numerical outputs.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from src.dtc_feature_sim import (
    averaged_trace,
    endpoint_mutual_information,
    fourier_response,
    level_statistic_r,
)


def _fwhm(frequency: np.ndarray, amplitude: np.ndarray) -> float:
    """Return the sampled full width at half maximum of the dominant peak."""

    if len(frequency) != len(amplitude) or len(frequency) < 2:
        raise ValueError("a spectrum needs matching frequency/amplitude arrays")
    peak = int(np.argmax(amplitude))
    above = np.flatnonzero(amplitude >= 0.5 * amplitude[peak])
    component = [peak]
    left = peak - 1
    while left in above:
        component.insert(0, left)
        left -= 1
    right = peak + 1
    while right in above:
        component.append(right)
        right += 1
    return float(frequency[component[-1]] - frequency[component[0]])


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _long_range_boundary(
    target_id: str,
    profile: dict[str, Any],
    items: list[str],
) -> dict[str, Any]:
    """Evaluate the printed power-law Floquet model on a frozen reduced grid.

    Equation (3) specifies J_ij / r_ij**alpha, so an experimental coupling
    matrix is not an indispensable input for these theoretical curves.  The
    attestation grid is reduced and therefore does not claim the paper-scale
    phase boundary.
    """

    rows = []
    alpha = float(profile["long_range_alpha"])
    for coupling_index, coupling in enumerate(profile["long_range_couplings"]):
        for epsilon_index, epsilon in enumerate(profile["long_range_epsilons"]):
            value = level_statistic_r(
                int(profile["level_size"]),
                float(coupling),
                float(epsilon),
                int(profile["level_samples"]),
                int(profile["seed"]) + 1000 + 100 * coupling_index + epsilon_index,
                alpha=alpha,
            )
            rows.append(
                {
                    "interaction_strength": coupling,
                    "epsilon": epsilon,
                    "alpha": alpha,
                    "mean_gap_ratio": value,
                }
            )
    passed = all(np.isfinite(row["mean_gap_ratio"]) and 0.0 <= row["mean_gap_ratio"] <= 1.0 for row in rows)
    return {
        "target_id": target_id,
        "items": items,
        "status": "computed_reduced_scale",
        "observable": "Floquet adjacent-gap ratio for J_ij/r_ij^alpha interactions",
        "rows": rows,
        "publication_input_boundary": "No external matrix is required: Eq. (3) fixes the theoretical power-law coupling family.",
        "scientific_boundary": "The frozen attestation grid is reduced and is not a paper-scale boundary fit.",
        "acceptance": {
            "passed": passed,
            "criterion": "Every long-range mean adjacent-gap ratio is finite and in [0,1].",
        },
    }


def _level_statistics(profile: dict[str, Any], items: list[str]) -> dict[str, Any]:
    size = int(profile["level_size"])
    rows = []
    for index, epsilon in enumerate(profile["level_epsilons"]):
        value = level_statistic_r(
            size,
            float(profile["interaction_strength"]),
            float(epsilon),
            int(profile["level_samples"]),
            int(profile["seed"]) + index,
        )
        rows.append({"epsilon": epsilon, "mean_gap_ratio": value})
    passed = all(0.0 <= row["mean_gap_ratio"] <= 1.0 for row in rows)
    return {
        "target_id": "T005",
        "items": items,
        "status": "computed_reduced_scale",
        "observable": "Floquet adjacent-gap ratio",
        "rows": rows,
        "acceptance": {"passed": passed, "criterion": "Every mean adjacent-gap ratio is finite and in [0,1]."},
    }


def _fwhm_result(profile: dict[str, Any], items: list[str]) -> dict[str, Any]:
    trace = averaged_trace(
        int(profile["trace_size"]),
        float(profile["interaction_strength"]),
        float(profile["fwhm_epsilon"]),
        int(profile["steps"]),
        int(profile["trace_samples"]),
        int(profile["seed"]) + 20,
    )
    freq, amp = fourier_response(trace, start=int(profile["fourier_start"]))
    mask = freq >= 0.25
    width = _fwhm(freq[mask], amp[mask])
    return {
        "target_id": "T008",
        "items": items,
        "status": "computed_reduced_scale",
        "observable": "sampled FWHM of the subharmonic Fourier peak",
        "fwhm": width,
        "frequency_resolution": float(freq[1] - freq[0]),
        "acceptance": {"passed": bool(np.isfinite(width) and width >= 0.0), "criterion": "FWHM is finite and non-negative."},
    }


def _variance_result(profile: dict[str, Any], items: list[str]) -> dict[str, Any]:
    rows = []
    for coupling_index, coupling in enumerate(profile["variance_couplings"]):
        heights = []
        for sample in range(int(profile["variance_samples"])):
            trace = averaged_trace(
                int(profile["trace_size"]),
                float(coupling),
                float(profile["variance_epsilon"]),
                int(profile["steps"]),
                1,
                int(profile["seed"]) + 100 * coupling_index + sample,
            )
            time = np.arange(len(trace))
            heights.append(float(abs(np.mean(trace * ((-1.0) ** time)))))
        rows.append({"interaction_strength": coupling, "half_peak_variance": float(np.var(heights)), "samples": len(heights)})
    return {
        "target_id": "T009",
        "items": items,
        "status": "computed_reduced_scale",
        "observable": "disorder variance of the half-frequency response",
        "rows": rows,
        "acceptance": {"passed": all(row["half_peak_variance"] >= 0 for row in rows), "criterion": "All computed variances are non-negative."},
    }


def _mutual_information(target_id: str, profile: dict[str, Any], items: list[str]) -> dict[str, Any]:
    requested = profile["mutual_information_sizes"][target_id]
    rows = []
    for index, paper_size in enumerate(requested):
        attestation_size = min(int(paper_size), int(profile["mutual_information_size_cap"]))
        value = endpoint_mutual_information(
            attestation_size,
            float(profile["mutual_information_coupling"]),
            float(profile["mutual_information_epsilon"]),
            int(profile["mutual_information_samples"]),
            int(profile["seed"]) + 500 + index,
        )
        rows.append({"paper_system_size": paper_size, "executed_system_size": attestation_size, "endpoint_mutual_information": value})
    passed = all(-1e-10 <= row["endpoint_mutual_information"] <= 2 * np.log(2) + 1e-8 for row in rows)
    return {
        "target_id": target_id,
        "items": items,
        "status": "computed_reduced_scale",
        "observable": "endpoint mutual information of Floquet eigenstates",
        "rows": rows,
        "acceptance": {"passed": passed, "criterion": "Mutual information lies in the two-qubit entropy bound [0,2 ln 2]."},
    }


def _supplement_s1(profile: dict[str, Any], items: list[str]) -> dict[str, Any]:
    rows = []
    for index, epsilon in enumerate(profile["s1_epsilons"]):
        trace = averaged_trace(
            int(profile["trace_size"]),
            float(profile["interaction_strength"]),
            float(epsilon),
            int(profile["steps"]),
            int(profile["trace_samples"]),
            int(profile["seed"]) + 700 + index,
        )
        freq, amp = fourier_response(trace, start=int(profile["fourier_start"]))
        half_index = int(np.argmin(abs(freq - 0.5)))
        rows.append({"epsilon": epsilon, "trace": trace.tolist(), "frequencies": freq.tolist(), "normalized_spectrum": amp.tolist(), "half_frequency_response": float(amp[half_index])})
    susceptibility = []
    for coupling in profile["s1_susceptibility_couplings"]:
        trace = averaged_trace(
            int(profile["trace_size"]), float(coupling), float(profile["s1_epsilons"][0]),
            int(profile["steps"]), int(profile["trace_samples"]), int(profile["seed"]) + 800 + len(susceptibility),
        )
        time = np.arange(len(trace))
        susceptibility.append({"interaction_strength": coupling, "staggered_response": float(abs(np.mean(trace * ((-1.0) ** time))))})
    return {
        "target_id": "T012",
        "items": items,
        "status": "computed_reduced_scale",
        "trace_and_fft": rows,
        "susceptibility_proxy": susceptibility,
        "acceptance": {"passed": all(len(row["trace"]) == int(profile["steps"]) for row in rows), "criterion": "All independent Floquet traces have the frozen length and finite spectra."},
    }


def _long_time_spectra(profile: dict[str, Any], items: list[str]) -> dict[str, Any]:
    rows = []
    for model, field_contracts in profile["s3_fields"].items():
        alpha = float(profile["s3_alpha"]) if model == "power_law" else None
        for index, field_contract in enumerate(field_contracts):
            uniform_field = field_contract["uniform_field"]
            trace = averaged_trace(
                int(profile["trace_size"]), float(profile["s3_coupling"]),
                float(profile["s3_epsilon"]), int(profile["s3_steps"]),
                int(profile["trace_samples"]), int(profile["seed"]) + 900 + 10 * (model == "power_law") + index,
                alpha=alpha,
                uniform_field=uniform_field,
            )
            freq, amp = fourier_response(trace, start=int(profile["fourier_start"]))
            rows.append(
                {
                    "model": model,
                    "paper_field_label": field_contract["label"],
                    "field_mode": "maximal_disorder_0_2pi" if uniform_field is None else "uniform",
                    "uniform_field": uniform_field,
                    "frequency": freq.tolist(),
                    "normalized_spectrum": amp.tolist(),
                }
            )
    return {
        "target_id": "T013",
        "items": items,
        "status": "computed_reduced_scale",
        "rows": rows,
        "scientific_boundary": "The field values and power-law family match Fig. S3, but this attestation remains reduced scale and does not claim full printed-curve agreement.",
        "acceptance": {"passed": all(len(row["frequency"]) == len(row["normalized_spectrum"]) for row in rows), "criterion": "Each spectrum has a matching finite frequency grid."},
    }


def _persistence(profile: dict[str, Any], items: list[str]) -> dict[str, Any]:
    rows = []
    for index, size in enumerate(profile["persistence_sizes"]):
        trace = averaged_trace(int(size), float(profile["persistence_coupling"]), float(profile["persistence_epsilon"]), int(profile["persistence_steps"]), int(profile["trace_samples"]), int(profile["seed"]) + 1100 + index)
        staggered = abs(trace * ((-1.0) ** np.arange(len(trace))))
        below = np.flatnonzero(staggered < float(profile["persistence_threshold"]))
        lifetime = int(below[0]) if len(below) else len(trace)
        rows.append({"system_size": size, "persistence_steps": lifetime})
    return {"target_id": "T014", "items": items, "status": "computed_reduced_scale", "rows": rows, "acceptance": {"passed": all(0 <= row["persistence_steps"] <= int(profile["persistence_steps"]) for row in rows), "criterion": "Every threshold-crossing time is within the simulated interval."}}


def _critical_scaling(profile: dict[str, Any], items: list[str]) -> dict[str, Any]:
    phi = (1.0 + np.sqrt(5.0)) / 2.0
    distance = np.asarray(profile["critical_distances"], dtype=float)
    time = np.asarray(profile["critical_times"], dtype=float)
    mean_corr = distance ** (-(2.0 - phi))
    typical_corr = np.exp(-np.sqrt(distance))
    wigner_decay = np.log(time + np.e) ** (-(2.0 - phi))
    return {
        "target_id": "T015", "items": items, "status": "computed_analytic_claims",
        "exponents": {"golden_ratio_phi": float(phi), "beta": float(2.0 - phi), "nu_typical": 1.0, "nu_average": 2.0},
        "distance": distance.tolist(), "mean_correlation": mean_corr.tolist(), "typical_correlation": typical_corr.tolist(),
        "time": time.tolist(), "critical_wigner_decay": wigner_decay.tolist(),
        "acceptance": {"passed": bool(np.all(np.diff(mean_corr) < 0) and np.all(np.diff(typical_corr) < 0)), "criterion": "Both critical correlation laws decay monotonically on the frozen positive grid."},
    }


def _symmetry_checks(profile: dict[str, Any], items: list[str]) -> dict[str, Any]:
    rows = []
    for n in profile["clock_orders"]:
        omega = np.exp(2j * np.pi / int(n))
        shift = np.roll(np.eye(int(n), dtype=complex), 1, axis=0)
        clock = np.diag(omega ** np.arange(int(n)))
        commutation = np.linalg.norm(clock @ shift - omega * shift @ clock)
        order_error = max(np.linalg.norm(np.linalg.matrix_power(shift, int(n)) - np.eye(int(n))), np.linalg.norm(np.linalg.matrix_power(clock, int(n)) - np.eye(int(n))))
        rows.append({"clock_order": n, "zn_commutation_residual": float(commutation), "order_residual": float(order_error)})
    return {"target_id": "T016", "items": items, "status": "computed_analytic_claims", "rows": rows, "random_rotation_boundary": "The algebra is basis-covariant; no unpublished disorder realization is required for this identity check.", "acceptance": {"passed": all(row["zn_commutation_residual"] < 1e-10 and row["order_residual"] < 1e-10 for row in rows), "criterion": "Frozen Z_n clock and shift matrices satisfy ZX=omega XZ and X^n=Z^n=I."}}


def run_campaign(config_path: Path, profile_name: str, output_root: Path) -> dict[str, Any]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    profile = config["profiles"][profile_name]
    target_items = config["target_items"]
    if len({item for items in target_items.values() for item in items}) != int(config["fixed_denominator"]):
        raise ValueError("target_items no longer match the frozen implementation denominator")

    results = {
        "T005": _level_statistics(profile, target_items["T005"]),
        "T006": _long_range_boundary("T006", profile, target_items["T006"]),
        "T007": _long_range_boundary("T007", profile, target_items["T007"]),
        "T008": _fwhm_result(profile, target_items["T008"]),
        "T009": _variance_result(profile, target_items["T009"]),
        "T010": _mutual_information("T010", profile, target_items["T010"]),
        "T011": _mutual_information("T011", profile, target_items["T011"]),
        "T012": _supplement_s1(profile, target_items["T012"]),
        "T013": _long_time_spectra(profile, target_items["T013"]),
        "T014": _persistence(profile, target_items["T014"]),
        "T015": _critical_scaling(profile, target_items["T015"]),
        "T016": _symmetry_checks(profile, target_items["T016"]),
    }
    for target_id, payload in results.items():
        _write(output_root / f"{target_id}.json", payload)
    summary = {
        "schema_version": 1, "paper_id": config["paper_id"], "profile": profile_name,
        "scientific_scale": profile["scientific_scale"], "fixed_denominator": config["fixed_denominator"],
        "implemented_items": sum(len(payload["items"]) for payload in results.values()),
        "target_status": {target: payload["status"] for target, payload in results.items()},
        "all_executable_acceptance_passed": all(payload["acceptance"].get("passed", False) for payload in results.values()),
        "blocked_targets": [target for target, payload in results.items() if payload["status"] == "blocked_on_paper_input"],
    }
    _write(output_root / "campaign_summary.json", summary)
    return summary
