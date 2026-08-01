#!/usr/bin/env python3
"""Independently reproduce Supplementary Fig. S4 from Eqs. (S24)-(S26)."""

from __future__ import annotations

import csv
import json
from pathlib import Path
import sys

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from scipy.spatial import cKDTree


CODE_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = CODE_ROOT.parent if CODE_ROOT.name == "code" else CODE_ROOT
sys.path.insert(0, str(CODE_ROOT))

from src.geometry_adaptive import (  # noqa: E402
    full_right_eigensystem,
)
from src.supplementary_models import (  # noqa: E402
    double_chain_bloch_spectrum,
    double_chain_hamiltonian,
    double_chain_tdl_spectrum,
    fit_boundary_exponential,
    site_probability,
)


PAPER_LENGTHS = (20, 40, 60, 80)
SCALING_LENGTHS = (20, 30, 40, 50, 60, 70, 80, 100, 120)
TDL_FINE_RESOLUTION = (801, 161)
TDL_COARSE_RESOLUTION = (401, 101)
PARAMETERS = {
    "t1_left": 0.5,
    "t1_right": 1.0,
    "t2_left": 1.0,
    "t2_right": 0.5,
    "potential": 0.5,
    "coupling": 0.01,
}


def configure_matplotlib() -> None:
    mpl.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
            "mathtext.fontset": "stix",
            "axes.linewidth": 0.8,
            "pdf.fonttype": 42,
            "svg.fonttype": "none",
            "svg.hashsalt": "pragent-2407.01296",
        }
    )


def write_rows(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def normalized_residual(
    hamiltonian: np.ndarray,
    eigenvalue: complex,
    eigenvector: np.ndarray,
) -> float:
    vector = np.asarray(eigenvector, dtype=np.complex128)
    operator_norm = float(np.max(np.sum(np.abs(hamiltonian), axis=1)))
    numerator = float(np.linalg.norm(hamiltonian @ vector - eigenvalue * vector))
    denominator = (operator_norm + abs(eigenvalue)) * float(np.linalg.norm(vector))
    return numerator / denominator


def compute() -> tuple[
    list[dict[str, object]],
    list[dict[str, object]],
    list[dict[str, object]],
    dict[str, object],
]:
    spectra: list[dict[str, object]] = []
    profiles: list[dict[str, object]] = []
    scaling: list[dict[str, object]] = []

    momentum = np.linspace(-np.pi, np.pi, 1600, endpoint=False)
    periodic = double_chain_bloch_spectrum(momentum, **PARAMETERS)
    for band in range(periodic.shape[1]):
        for k, value in zip(momentum, periodic[:, band], strict=True):
            spectra.append(
                {
                    "series": "PBC",
                    "length": 0,
                    "band": band + 1,
                    "momentum": k,
                    "real_energy": value.real,
                    "imag_energy": value.imag,
                    "root_gap": "",
                }
            )

    cached: dict[int, tuple[np.ndarray, np.ndarray]] = {}
    maximum_residual = 0.0
    for length in SCALING_LENGTHS:
        matrix = double_chain_hamiltonian(length, **PARAMETERS)
        eigensystem = full_right_eigensystem(matrix)
        cached[length] = (eigensystem.eigenvalues, eigensystem.right_eigenvectors)
        dense = matrix.toarray()
        selected_indices = {
            "wing_max_real": int(np.argmax(eigensystem.eigenvalues.real)),
            "central_max_imag": int(np.argmax(eigensystem.eigenvalues.imag)),
        }
        for state, index in selected_indices.items():
            probability = site_probability(eigensystem.right_eigenvectors[:, index])
            fit = fit_boundary_exponential(probability)
            residual = normalized_residual(
                dense,
                complex(eigensystem.eigenvalues[index]),
                eigensystem.right_eigenvectors[:, index],
            )
            maximum_residual = max(maximum_residual, residual)
            scaling.append(
                {
                    "state": state,
                    "length": length,
                    "inverse_length": 1.0 / length,
                    "eigenvalue_real": eigensystem.eigenvalues[index].real,
                    "eigenvalue_imag": eigensystem.eigenvalues[index].imag,
                    "kappa": fit.kappa,
                    "fit_r_squared": fit.r_squared,
                    "fit_point_count": fit.point_count,
                    "peak_site": fit.peak_site,
                    "normalized_residual": residual,
                }
            )
            if length == 80:
                for site, value in enumerate(probability):
                    profiles.append(
                        {
                            "state": state,
                            "length": length,
                            "site": site + 1,
                            "probability": value,
                            "probability_over_max": value / probability.max(),
                        }
                    )

    for length in PAPER_LENGTHS:
        eigenvalues = cached[length][0]
        for value in eigenvalues:
            spectra.append(
                {
                    "series": f"OBC_L{length}",
                    "length": length,
                    "band": 0,
                    "momentum": "",
                    "real_energy": value.real,
                    "imag_energy": value.imag,
                    "root_gap": "",
                }
            )

    tdl = double_chain_tdl_spectrum(
        real_samples=TDL_FINE_RESOLUTION[0],
        imaginary_samples=TDL_FINE_RESOLUTION[1],
        **PARAMETERS,
    )
    coarse_tdl = double_chain_tdl_spectrum(
        real_samples=TDL_COARSE_RESOLUTION[0],
        imaginary_samples=TDL_COARSE_RESOLUTION[1],
        **PARAMETERS,
    )
    for value, root_gap in zip(tdl.energies, tdl.root_gaps, strict=True):
        spectra.append(
            {
                "series": "exact_TDL_root_condition",
                "length": 0,
                "band": 0,
                "momentum": "",
                "real_energy": value.real,
                "imag_energy": value.imag,
                "root_gap": root_gap,
            }
        )

    tdl_points = np.column_stack((tdl.energies.real, tdl.energies.imag))
    coarse_points = np.column_stack(
        (coarse_tdl.energies.real, coarse_tdl.energies.imag)
    )
    tdl_tree = cKDTree(tdl_points)
    coarse_tree = cKDTree(coarse_points)
    fine_to_coarse = coarse_tree.query(tdl_points)[0]
    coarse_to_fine = tdl_tree.query(coarse_points)[0]
    conjugation_error = tdl_tree.query(
        np.column_stack((tdl.energies.real, -tdl.energies.imag))
    )[0]
    finite_size_to_tdl: dict[str, dict[str, float]] = {}
    for length in PAPER_LENGTHS:
        values = cached[length][0]
        distances = tdl_tree.query(
            np.column_stack((values.real, values.imag))
        )[0]
        finite_size_to_tdl[str(length)] = {
            "mean": float(np.mean(distances)),
            "median": float(np.median(distances)),
            "p95": float(np.quantile(distances, 0.95)),
            "maximum": float(np.max(distances)),
        }

    central = [row for row in scaling if row["state"] == "central_max_imag"]
    inverse_length = np.asarray([row["inverse_length"] for row in central], dtype=float)
    kappa = np.asarray([row["kappa"] for row in central], dtype=float)
    coefficients = np.polyfit(inverse_length, kappa, 1)
    prediction = np.polyval(coefficients, inverse_length)
    total_sum = float(np.sum((kappa - np.mean(kappa)) ** 2))
    regression_r_squared = 1.0 - float(np.sum((kappa - prediction) ** 2)) / total_sum
    wing_80 = next(
        row for row in scaling if row["state"] == "wing_max_real" and row["length"] == 80
    )
    central_80 = next(
        row
        for row in scaling
        if row["state"] == "central_max_imag" and row["length"] == 80
    )
    paper_p95 = np.asarray(
        [finite_size_to_tdl[str(length)]["p95"] for length in PAPER_LENGTHS],
        dtype=np.float64,
    )
    acceptance = {
        "caption_obc_lengths_complete": sorted(PAPER_LENGTHS)
        == sorted(
            {
                int(row["length"])
                for row in spectra
                if str(row["series"]).startswith("OBC_L")
            }
        ),
        "periodic_bands_independently_generated": sum(
            row["series"] == "PBC" for row in spectra
        )
        == 3200,
        "central_kappa_decreases_with_size": bool(np.all(np.diff(kappa) < 0.0)),
        "central_kappa_scales_linearly_in_inverse_length": regression_r_squared > 0.99,
        "central_tdl_intercept_near_zero": abs(float(coefficients[1])) < 0.02,
        "wing_state_remains_more_localized": float(wing_80["kappa"])
        > 3.0 * float(central_80["kappa"]),
        "selected_eigenpairs_have_small_residual": maximum_residual < 1e-10,
        "profile_fits_are_resolved": min(float(row["fit_r_squared"]) for row in scaling)
        > 0.88,
        "exact_tdl_middle_root_condition_satisfied": float(np.max(tdl.root_gaps))
        <= tdl.root_gap_tolerance,
        "exact_tdl_has_conjugation_symmetry": float(np.max(conjugation_error)) < 1e-12,
        "exact_tdl_is_resolution_stable": float(np.quantile(fine_to_coarse, 0.95))
        < 0.01
        and float(np.quantile(coarse_to_fine, 0.95)) < 0.01,
        "finite_obc_spectra_converge_toward_exact_tdl": bool(
            np.all(np.diff(paper_p95) < 0.0)
        ),
        "largest_paper_obc_spectrum_is_close_to_exact_tdl": float(paper_p95[-1])
        < 0.1,
    }
    check = {
        "schema_version": 1,
        "paper_id": "2407.01296",
        "target_id": "T004",
        "figure_refs": ["Supplementary Fig. S4(a)", "Supplementary Fig. S4(b)"],
        "status": "passed" if all(acceptance.values()) else "failed",
        "artifact_stage": "scientific_reproduction",
        "generated_data_provenance": "independent_numerics",
        "source_pixels_copied_into_reproduction": False,
        "formula_refs": ["EQC007", "EQC008", "EQC015"],
        "parameters": PARAMETERS,
        "paper_lengths": list(PAPER_LENGTHS),
        "scaling_lengths": list(SCALING_LENGTHS),
        "tdl_construction": "Eq. (S24) quartic with ordered-root condition |beta_2(E)|=|beta_3(E)|",
        "tdl_resolution": {
            "fine": list(TDL_FINE_RESOLUTION),
            "coarse": list(TDL_COARSE_RESOLUTION),
            "fine_points": int(tdl.energies.size),
            "coarse_points": int(coarse_tdl.energies.size),
            "root_gap_tolerance": tdl.root_gap_tolerance,
            "maximum_root_gap": float(np.max(tdl.root_gaps)),
            "fine_to_coarse_p95_distance": float(
                np.quantile(fine_to_coarse, 0.95)
            ),
            "coarse_to_fine_p95_distance": float(
                np.quantile(coarse_to_fine, 0.95)
            ),
        },
        "finite_size_to_exact_tdl": finite_size_to_tdl,
        "central_kappa_regression": {
            "slope": float(coefficients[0]),
            "intercept": float(coefficients[1]),
            "r_squared": regression_r_squared,
        },
        "maximum_selected_eigenpair_residual": maximum_residual,
        "acceptance": acceptance,
        "execution_budget": {
            "hardware_class": "local_cpu",
            "wall_clock_budget_seconds": 60,
        },
    }
    return spectra, profiles, scaling, check


def render(
    path: Path,
    spectra: list[dict[str, object]],
    profiles: list[dict[str, object]],
    scaling: list[dict[str, object]],
    check: dict[str, object],
) -> None:
    configure_matplotlib()
    figure, axes = plt.subplots(1, 2, figsize=(8.2, 3.25), constrained_layout=True)
    spectrum_axis, profile_axis = axes
    colors = {20: "#E69F00", 40: "#CC79A7", 60: "#D55E00", 80: "#0072B2"}
    tdl = [row for row in spectra if row["series"] == "exact_TDL_root_condition"]
    spectrum_axis.scatter(
        [row["real_energy"] for row in tdl],
        [row["imag_energy"] for row in tdl],
        s=2.0,
        color="0.72",
        linewidths=0,
        label="exact TDL (root condition)",
    )
    periodic = [row for row in spectra if row["series"] == "PBC"]
    spectrum_axis.scatter(
        [row["real_energy"] for row in periodic],
        [row["imag_energy"] for row in periodic],
        s=1.2,
        color="#56B4E9",
        linewidths=0,
        label="PBC",
    )
    for length in PAPER_LENGTHS:
        selected = [row for row in spectra if row["series"] == f"OBC_L{length}"]
        spectrum_axis.scatter(
            [row["real_energy"] for row in selected],
            [row["imag_energy"] for row in selected],
            s=3.0,
            color=colors[length],
            linewidths=0,
            label=f"L={length}",
        )
    spectrum_axis.set_xlabel(r"Re $E$")
    spectrum_axis.set_ylabel(r"Im $E$")
    spectrum_axis.set_title("(a) Eq. (S24) spectra", loc="left", fontsize=10)
    spectrum_axis.legend(frameon=False, fontsize=6.5, ncol=2)

    for state, color, label in (
        ("wing_max_real", "#0072B2", "largest Re(E)"),
        ("central_max_imag", "#D55E00", "largest Im(E)"),
    ):
        selected = [row for row in profiles if row["state"] == state]
        profile_axis.plot(
            [row["site"] for row in selected],
            [row["probability_over_max"] for row in selected],
            color=color,
            linewidth=1.15,
            label=label,
        )
    profile_axis.set_xlabel("site")
    profile_axis.set_ylabel(r"$|A|^2 / \max |A|^2$")
    profile_axis.set_title("(b) L=80 right eigenstates", loc="left", fontsize=10)
    profile_axis.legend(
        frameon=False,
        fontsize=6.5,
        loc="upper left",
        bbox_to_anchor=(0.02, 0.98),
    )
    inset = profile_axis.inset_axes((0.51, 0.47, 0.45, 0.45))
    central = [row for row in scaling if row["state"] == "central_max_imag"]
    x = np.asarray([row["inverse_length"] for row in central], dtype=float)
    y = np.asarray([row["kappa"] for row in central], dtype=float)
    regression = check["central_kappa_regression"]
    line = np.linspace(0.0, float(x.max()) * 1.05, 100)
    inset.scatter(x, y, s=9.0, color="black")
    inset.plot(
        line,
        float(regression["slope"]) * line + float(regression["intercept"]),
        color="0.5",
        linewidth=0.8,
    )
    inset.set_xlabel(r"$1/L$", fontsize=7)
    inset.set_ylabel(r"$\kappa$", fontsize=7)
    inset.tick_params(labelsize=6)

    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=240)
    svg_path = path.with_suffix(".svg")
    figure.savefig(svg_path, metadata={"Date": None})
    # The master case keeps a publication PDF, while the sanitized public
    # projection intentionally permits only PNG/SVG generated figures.
    if CODE_ROOT.name != "code":
        figure.savefig(
            path.with_suffix(".pdf"),
            metadata={"CreationDate": None, "ModDate": None},
        )
    plt.close(figure)
    svg_text = svg_path.read_text(encoding="utf-8")
    svg_path.write_text(
        "\n".join(line.rstrip() for line in svg_text.splitlines()) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    spectra, profiles, scaling, check = compute()
    data_dir = OUTPUT_ROOT / "outputs" / "data"
    check_dir = OUTPUT_ROOT / "outputs" / "checks"
    figure_path = OUTPUT_ROOT / "outputs" / "figures" / "supp_fig_s4_reproduction.png"
    write_rows(data_dir / "supp_fig_s4_spectra.csv", spectra)
    write_rows(data_dir / "supp_fig_s4_profiles.csv", profiles)
    write_rows(data_dir / "supp_fig_s4_scaling.csv", scaling)
    render(figure_path, spectra, profiles, scaling, check)
    check_dir.mkdir(parents=True, exist_ok=True)
    (check_dir / "supp_fig_s4.json").write_text(
        json.dumps(check, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(check, indent=2, ensure_ascii=False))
    return 0 if check["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
