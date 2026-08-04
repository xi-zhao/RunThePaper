"""Render data-backed comparisons for the four frozen idx56 benchmark tasks."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


HERE = Path(__file__).resolve().parent
WS = HERE.parent
sys.path.insert(0, str(WS / "src"))

from zn_lgt import symmetry_augment_polyakov  # noqa: E402


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    checks = WS / "outputs" / "checks"
    data = WS / "outputs" / "data"
    figures = WS / "outputs" / "figures"
    figures.mkdir(parents=True, exist_ok=True)

    z7 = read_json(checks / "idx56_z7_smoke_cold.json")["summaries"]
    z4_rows = read_csv(data / "idx56_z4_beta1p543_paper_measurements_hot.csv")
    z4 = np.asarray(
        [complex(float(row["polyakov_real"]), float(row["polyakov_imag"])) for row in z4_rows]
    )
    z4_augmented = symmetry_augment_polyakov(z4, 4)
    z3_path = checks / "idx56_z3_smoke_hot.json"
    z3 = read_json(z3_path)["summaries"][0] if z3_path.exists() else None
    analytic = read_csv(data / "idx56_analytic_paper_exact.csv")

    fig, axes = plt.subplots(2, 2, figsize=(10.5, 8.0), constrained_layout=True)

    beta = np.asarray([1.0, 2.0, 2.5])
    paper_polyakov = np.asarray([0.05, 0.65, 0.97])
    generated_polyakov = np.asarray([row["mean_polyakov_abs"] for row in z7])
    axes[0, 0].plot(beta, paper_polyakov, "o--", label="frozen benchmark (~)")
    axes[0, 0].plot(beta, generated_polyakov, "s-", label="generated, cold smoke")
    axes[0, 0].set(
        xlabel=r"$\beta$",
        ylabel=r"$\langle|\bar P|\rangle$",
        title="(a) Z7 Polyakov-loop anchors",
    )
    axes[0, 0].legend(frameon=False)

    # Plot a deterministic subset; the data artifact retains every augmented point.
    stride = max(1, len(z4_augmented) // 6000)
    shown = z4_augmented[::stride]
    axes[0, 1].scatter(shown.real, shown.imag, s=2, alpha=0.25, rasterized=True)
    axes[0, 1].set_aspect("equal")
    axes[0, 1].set(
        xlabel=r"Re $\bar P$",
        ylabel=r"Im $\bar P$",
        title="(b) Z4 symmetry-augmented Polyakov histogram",
    )

    if z3 is None:
        axes[1, 0].text(0.5, 0.5, "Z3 smoke run pending", ha="center", va="center")
        z3_value = None
    else:
        z3_value = z3["action_susceptibility"]
        axes[1, 0].bar(["benchmark (~)", "generated smoke"], [18.0, z3_value])
        axes[1, 0].set_ylabel(r"$\chi_S$")
    axes[1, 0].set_title(r"(c) Z3, $L=8,\ \beta=0.512,\ \mu=1$")

    n_values = np.asarray([int(row["n"]) for row in analytic])
    ratios = np.asarray([float(row["ratio"]) for row in analytic])
    axes[1, 1].plot(n_values, ratios, "o-", label="finite-torus analytic")
    axes[1, 1].scatter([7], [1.1], marker="x", s=80, label="frozen benchmark (~)")
    axes[1, 1].set(
        xlabel="n",
        ylabel=r"$C(n)/C(n+1)$",
        title="(d) L=16 Coulomb ratio",
    )
    axes[1, 1].legend(frameon=False)

    output = figures / "idx56_benchmark_comparison.png"
    fig.savefig(output, dpi=220)
    plt.close(fig)

    payload = {
        "status": "passed",
        "artifact": str(output.relative_to(WS)),
        "generated_data_provenance": "independent_monte_carlo_and_analytic_reference",
        "z7": {
            "paper_approx": paper_polyakov.tolist(),
            "generated": generated_polyakov.tolist(),
            "absolute_error": np.abs(generated_polyakov - paper_polyakov).tolist(),
            "parameter_match": "reduced_scale",
        },
        "z4": {
            "samples_raw": int(len(z4)),
            "samples_symmetry_augmented": int(len(z4_augmented)),
            "mean_abs_polyakov": float(np.mean(np.abs(z4))),
            "q_raw": float(abs(np.mean(z4)) / np.mean(np.abs(z4))),
            "q_symmetry_augmented": float(
                abs(np.mean(z4_augmented)) / np.mean(np.abs(z4_augmented))
            ),
            "parameter_match": "paper_subset_burnin_unreported",
        },
        "z3": {
            "paper_approx": 18.0,
            "generated": z3_value,
            "parameter_match": "reduced_scale" if z3 is not None else "not_run",
        },
        "analytic": {
            "paper_approx_c7_over_c8": 1.1,
            "generated_c7_over_c8": float(ratios[-1]),
            "parameter_match": "paper_exact_analytic_curve",
        },
        "truth_boundary": [
            "Frozen benchmark values marked '~' have no supplied uncertainty or tolerance.",
            "Z4 q=0 follows the supplement's explicit complete Z4 rotation augmentation; raw-chain q is reported separately.",
            "The analytic Coulomb curve does not replace the missing paper-scale Monte Carlo correlator data.",
        ],
    }
    (checks / "idx56_benchmark_comparison.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
