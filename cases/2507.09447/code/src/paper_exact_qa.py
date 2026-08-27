from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import scipy.interpolate
import scipy.stats

from lyapunov_band import normalized_positive_density, write_json
from paper_exact_reproduction import load_paper_config


def evaluate_scientific_match(workspace: Path) -> dict[str, Any]:
    """Evaluate paper-scale physical agreement separately from image styling."""

    workspace = workspace.resolve()
    data_dir = workspace / "outputs" / "paper_exact" / "data"
    checks_dir = workspace / "outputs" / "checks"
    config = load_paper_config(workspace)
    thresholds = config["scientific_qa"]
    ed = _load_npz(data_dir / "paper_ed_histograms.npz")
    theory = _load_npz(data_dir / "paper_fig34_theory.npz")
    contours = _load_npz(data_dir / "paper_fig5_contours.npz")
    profiles = _load_npz(data_dir / "paper_profiles.npz")
    scaling = _read_csv(data_dir / "paper_scaling.csv")
    alpha = _read_csv(data_dir / "paper_alpha.csv")

    theory_obc_on_ed = resample_regular_grid(
        theory["obc_density"],
        theory["real_axis"],
        theory["imag_axis"],
        ed["real_axis"],
        ed["imag_axis"],
    )
    theory_pbc_on_ed = resample_regular_grid(
        theory["pbc_density"],
        theory["real_axis"],
        theory["imag_axis"],
        ed["real_axis"],
        ed["imag_axis"],
    )
    density_metrics = {
        "obc_overlap": probability_overlap(ed["obc_density"], theory_obc_on_ed),
        "pbc_overlap": probability_overlap(ed["pbc_density"], theory_pbc_on_ed),
    }

    scaling_metrics: dict[str, dict[str, float]] = {}
    fit_min_length = int(config["fig3_fig4"]["scaling_fit_min_length"])
    for spec in config["fig3_fig4"]["scaling_energies"]:
        subset = scaling[scaling["label"] == spec["label"]]
        subset = subset[subset["L"].astype(float) >= fit_min_length]
        slope, intercept = np.polyfit(
            np.log(subset["L"].astype(float)),
            np.log(subset["delta_phi"].astype(float)),
            1,
        )
        scaling_metrics[spec["label"]] = {
            "fit_exponent_L": float(slope),
            "fit_intercept": float(intercept),
            "paper_exponent_L": float(spec["paper_exponent"]),
            "paper_intercept": float(spec["paper_intercept"]),
            "fit_min_length": fit_min_length,
            "absolute_exponent_gap": float(abs(slope - float(spec["paper_exponent"]))),
        }

    exponents = profiles["selected_lyapunov_exponents"]
    alm_count = profiles["alm_profiles"].shape[0]
    profile_metrics = {
        "all_alm_central_exponents_straddle_zero": bool(
            np.all((exponents[:alm_count, 1] < 0.0) & (exponents[:alm_count, 2] > 0.0))
        ),
        "critical_min_abs_central_exponent": float(min(abs(exponents[alm_count, 1]), abs(exponents[alm_count, 2]))),
        "skin_central_exponents_have_same_sign": bool(exponents[alm_count + 1, 1] * exponents[alm_count + 1, 2] > 0.0),
    }

    skin_areas = np.mean(
        ~((contours["exponents"][..., 1] < 0.0) & (contours["exponents"][..., 2] > 0.0)),
        axis=(1, 2),
    )
    contour_spearman = float(scipy.stats.spearmanr(contours["W"], skin_areas).statistic)
    alpha_candidates = alpha["W"][alpha["alpha"] >= 0.98]
    estimated_wc = float(alpha_candidates[0]) if alpha_candidates.size else None

    gates = {
        "ed_ensemble_complete": int(ed["completed_realizations"].item()) == 3200,
        "obc_finite_tdl_density_overlap": density_metrics["obc_overlap"]
        >= float(thresholds["finite_tdl_density_overlap_min"]),
        "pbc_finite_tdl_density_overlap": density_metrics["pbc_overlap"]
        >= float(thresholds["finite_tdl_density_overlap_min"]),
        "scaling_exponents_match": all(
            metrics["absolute_exponent_gap"] <= float(thresholds["scaling_exponent_gap_max"])
            for metrics in scaling_metrics.values()
        ),
        "alm_profiles_classified": profile_metrics["all_alm_central_exponents_straddle_zero"],
        "critical_profile_near_zero_le": profile_metrics["critical_min_abs_central_exponent"]
        <= float(thresholds["critical_lyapunov_abs_max"]),
        "skin_profile_classified": profile_metrics["skin_central_exponents_have_same_sign"],
        "mobility_contours_shrink": contour_spearman <= float(thresholds["mobility_area_spearman_max"]),
        "transition_matches_paper": estimated_wc is not None
        and abs(estimated_wc - 2.1) <= float(thresholds["transition_W_tolerance"]),
    }
    result = {
        "status": "paper_scale_feature_match" if all(gates.values()) else "partial",
        "artifact_stage": "paper_matched_reproduction",
        "parameter_match": "paper_reported_plus_documented_inference",
        "gate_flags": gates,
        "acceptance_thresholds": thresholds,
        "density_metrics": density_metrics,
        "scaling_metrics": scaling_metrics,
        "profile_metrics": profile_metrics,
        "fig5_metrics": {
            "skin_area_spearman": contour_spearman,
            "estimated_Wc_alpha_ge_0_98": estimated_wc,
            "paper_Wc": 2.1,
            "alpha_at_W_3": float(alpha["alpha"][-1]),
        },
        "limitations": [
            "author random seeds and eigenstate selection windows are unavailable",
            "author transfer length, QR interval, and Fig. 5 quadrature details are unavailable",
            "the source PDFs were manually assembled in Adobe Illustrator",
        ],
    }
    write_json(checks_dir / "paper_scientific_similarity.json", result)
    return result


def resample_regular_grid(
    values: np.ndarray,
    source_real: np.ndarray,
    source_imag: np.ndarray,
    target_real: np.ndarray,
    target_imag: np.ndarray,
) -> np.ndarray:
    interpolator = scipy.interpolate.RegularGridInterpolator(
        (source_imag, source_real),
        np.asarray(values, dtype=float),
        bounds_error=False,
        fill_value=0.0,
    )
    target_real_grid, target_imag_grid = np.meshgrid(target_real, target_imag)
    points = np.column_stack([target_imag_grid.ravel(), target_real_grid.ravel()])
    return interpolator(points).reshape(target_imag.size, target_real.size)


def probability_overlap(left: np.ndarray, right: np.ndarray) -> float:
    left_probability = normalized_positive_density(left)
    right_probability = normalized_positive_density(right)
    return float(np.minimum(left_probability, right_probability).sum())


def _load_npz(path: Path) -> dict[str, np.ndarray]:
    with np.load(path, allow_pickle=False) as data:
        return {name: data[name].copy() for name in data.files}


def _read_csv(path: Path) -> np.ndarray:
    data = np.genfromtxt(path, delimiter=",", names=True, dtype=None, encoding="utf-8")
    return np.atleast_1d(data)
