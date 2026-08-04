#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import os
import sys
import time
from pathlib import Path


WORKSPACE = Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR", str(WORKSPACE / ".mplconfig"))
sys.path.insert(0, str(WORKSPACE / "src"))

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

import leaf_thermodynamics as leaf  # noqa: E402


DATA_PATH = WORKSPACE / "outputs" / "data" / "local_canary_l6.csv"
FIGURE_PATH = WORKSPACE / "outputs" / "figures" / "local_canary_l6.png"
CHECK_PATH = WORKSPACE / "outputs" / "checks" / "local_canary_l6.json"

NONINTEGRABLE_FIELD = (
    (np.sqrt(5.0) + 5.0) / 8.0,
    0.5,
    np.sqrt(5.0) / 2.0,
)
DM = np.pi / 20.0
H0_FIELD = (0.0, 0.0, 1.5)


def expectation_curves(
    length: int,
    boundary: str,
    beta: float,
) -> tuple[list[dict[str, object]], dict[str, object]]:
    started = time.perf_counter()
    h = leaf.spin_chain_hamiltonian(
        length,
        NONINTEGRABLE_FIELD,
        DM,
        boundary=boundary,
    ).toarray()
    h0 = leaf.spin_chain_hamiltonian(
        length,
        H0_FIELD,
        0.0,
        boundary=boundary,
    ).toarray()
    h0_energies, h0_basis = np.linalg.eigh(h0)
    h_in_h0_basis = h0_basis.conj().T @ h @ h0_basis
    rho_eigenvalues = leaf.thermal_weights(h0_energies, beta)
    ensemble = leaf.minimum_variance_ensemble(
        rho_eigenvalues,
        h_in_h0_basis,
        rho_basis=h0_basis,
        thermal_energies=h0_energies,
        beta=beta,
    )
    invariants = leaf.ensemble_invariants(
        rho_eigenvalues,
        h_in_h0_basis,
        ensemble,
    )

    h_energies, h_basis = np.linalg.eigh(h)
    del h_energies
    thresholds = np.linspace(0.0, 0.17, 35)
    observables = {
        "sigma_z": [(length // 2 - 1, "z")],
        "sigma_z_sigma_z": [
            (length // 2 - 1, "z"),
            (length // 2, "z"),
        ],
    }
    rows: list[dict[str, object]] = []
    for label, ops in observables.items():
        families = {
            "leaf_centred": (
                leaf.pauli_expectations(
                    ensemble.representatives,
                    length,
                    ops,
                ),
                "centred",
            ),
            "leaf_blocked": (
                leaf.pauli_expectations(
                    ensemble.representatives,
                    length,
                    ops,
                ),
                "blocked",
            ),
            "eth_nonintegrable": (
                leaf.pauli_expectations(h_basis, length, ops),
                "centred",
            ),
            "eth_integrable": (
                leaf.pauli_expectations(h0_basis, length, ops),
                "centred",
            ),
        }
        for family, (values, shell_mode) in families.items():
            curve = leaf.typicality_curve(
                values,
                thresholds=thresholds,
                shell_width=int(round(np.sqrt(1 << length))),
                shell_mode=shell_mode,
            )
            for delta, count, log_count in zip(
                curve["thresholds"],
                curve["counts"],
                curve["log_d_counts"],
                strict=True,
            ):
                rows.append(
                    {
                        "artifact_state": "exploratory",
                        "length": length,
                        "boundary": boundary,
                        "beta": beta,
                        "observable": label,
                        "family": family,
                        "shell_mode": shell_mode,
                        "shell_width": curve["shell_width"],
                        "delta": float(delta),
                        "count": int(count),
                        "log_d_count": (
                            float(log_count) if np.isfinite(log_count) else ""
                        ),
                    }
                )

    runtime = time.perf_counter() - started
    return rows, {
        "boundary": boundary,
        "runtime_seconds": runtime,
        "invariants": invariants,
        "dimension": 1 << length,
        "estimated_dense_complex_matrix_mib": (1 << length) ** 2 * 16 / 2**20,
    }


def write_rows(rows: list[dict[str, object]]) -> None:
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with DATA_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(rows[0]),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def render(rows: list[dict[str, object]]) -> None:
    colors = {"open": "#6d4cc3", "periodic": "#168aad"}
    styles = {
        "leaf_centred": "-",
        "leaf_blocked": "--",
        "eth_nonintegrable": ":",
        "eth_integrable": "-.",
    }
    fig, axes = plt.subplots(1, 2, figsize=(10.6, 4.2), sharey=True, constrained_layout=True)
    for axis, observable in zip(
        axes,
        ("sigma_z", "sigma_z_sigma_z"),
        strict=True,
    ):
        for boundary in ("open", "periodic"):
            for family in styles:
                selected = [
                    row
                    for row in rows
                    if row["boundary"] == boundary
                    and row["observable"] == observable
                    and row["family"] == family
                    and row["log_d_count"] != ""
                ]
                axis.plot(
                    [row["delta"] for row in selected],
                    [row["log_d_count"] for row in selected],
                    color=colors[boundary],
                    linestyle=styles[family],
                    linewidth=1.7,
                    label=f"{boundary}, {family}",
                )
        axis.set_title(observable.replace("_", " "))
        axis.set_xlabel(r"$\Delta$")
        axis.grid(alpha=0.2)
    axes[0].set_ylabel(r"$\log_d N_\Delta$")
    axes[1].legend(fontsize=7, frameon=False, ncol=2)
    fig.suptitle("Exploratory L=6 boundary/shell canary (beta=0.25)")
    FIGURE_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURE_PATH, dpi=200, facecolor="white")
    plt.close(fig)


def main() -> int:
    length = 6
    beta = 0.25
    rows: list[dict[str, object]] = []
    runs: list[dict[str, object]] = []
    for boundary in ("open", "periodic"):
        boundary_rows, run = expectation_curves(length, boundary, beta)
        rows.extend(boundary_rows)
        runs.append(run)
    write_rows(rows)
    render(rows)
    max_invariant_error = max(
        max(
            run["invariants"]["population_sum_error"],
            run["invariants"]["maximum_norm_error"],
            run["invariants"]["reconstruction_fro_error"],
            run["invariants"]["representative_energy_max_error"],
            run["invariants"]["qfi_variance_absolute_error"],
        )
        for run in runs
    )
    passed = max_invariant_error < 1e-9
    payload = {
        "schema_version": 1,
        "paper_id": "2602.12212",
        "status": "passed" if passed else "failed",
        "artifact_state": "exploratory",
        "purpose": "Formula/runtime canary and sensitivity comparison; not a final paper figure.",
        "parameters": {
            "length": length,
            "beta": beta,
            "boundaries": ["open", "periodic"],
            "shell_modes": ["centred", "blocked"],
            "shell_width": int(round(np.sqrt(1 << length))),
            "state_hamiltonian_field": list(H0_FIELD),
            "dynamics_hamiltonian_field": list(NONINTEGRABLE_FIELD),
            "dzyaloshinskii_moriya": DM,
        },
        "runs": runs,
        "maximum_formula_invariant_error": max_invariant_error,
        "data_path": str(DATA_PATH.relative_to(WORKSPACE)),
        "figure_path": str(FIGURE_PATH.relative_to(WORKSPACE)),
    }
    CHECK_PATH.parent.mkdir(parents=True, exist_ok=True)
    CHECK_PATH.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
