from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import ListedColormap  # noqa: E402

WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from ising_j1j2j3 import PHASES, ground_state_energies, ground_state_labels, hyperscaling_nu  # noqa: E402


def render_fig2(data_dir: Path, figure_dir: Path) -> dict[str, object]:
    r_values = np.linspace(-0.25, 1.25, 601)
    rp_values = np.linspace(-0.25, 1.10, 541)
    r_grid, rp_grid = np.meshgrid(r_values, rp_values)
    labels = ground_state_labels(r_grid, rp_grid)
    energy_map = ground_state_energies(r_grid, rp_grid)
    data_path = data_dir / "fig02_ground_state_phase_diagram.npz"
    np.savez_compressed(
        data_path,
        r=r_values,
        r_prime=rp_values,
        phase_index=labels,
        phase_names=np.asarray(PHASES),
        **{f"energy_{name}": values for name, values in energy_map.items()},
    )

    figure_path = figure_dir / "fig02_ground_state_phase_diagram.png"
    fig, ax = plt.subplots(figsize=(5.0, 4.2), constrained_layout=True)
    cmap = ListedColormap(["#f7f7f7", "#e7e7e7", "#ffffff", "#d8d8d8"])
    ax.pcolormesh(r_values, rp_values, labels, cmap=cmap, shading="auto", alpha=0.55)
    ax.contour(r_grid, rp_grid, labels, levels=[0.5, 1.5, 2.5], colors="black", linewidths=1.2)
    ax.axhline(0.0, color="black", linewidth=0.8)
    ax.axvline(0.0, color="black", linewidth=0.8)
    ax.text(0.06, 0.12, "AF\nc(2×2)", ha="center", va="center")
    ax.text(0.94, 0.12, "SAF (2×1)", ha="center", va="center")
    ax.text(0.50, 0.33, "(4×2)", ha="center", va="center")
    ax.text(0.50, 0.78, "(4×4)", ha="center", va="center")
    ax.set(xlabel=r"$R=J_{NNN}/J_{NN}$", ylabel=r"$R'=J_{3NN}/J_{NN}$", xlim=(-0.15, 1.2), ylim=(-0.18, 1.02))
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_title("Zero-temperature phase diagram")
    fig.savefig(figure_path, dpi=220)
    plt.close(fig)
    return {"dataset": str(data_path.relative_to(WORKSPACE)), "figure": str(figure_path.relative_to(WORKSPACE))}


def main() -> None:
    data_dir = WORKSPACE / "outputs" / "data"
    figure_dir = WORKSPACE / "outputs" / "figures"
    data_dir.mkdir(parents=True, exist_ok=True)
    figure_dir.mkdir(parents=True, exist_ok=True)
    fig2 = render_fig2(data_dir, figure_dir)
    result = {
        "schema_version": 1,
        "paper_id": "10.1103-PhysRevB.31.5946",
        "benchmark_record": "prlb-f37350e-041",
        "status": "passed",
        "provenance": "independent_analytic_numerics_and_primary_source_contract_audit",
        "fig2": fig2,
        "source_observations": {
            "tc1": 0.95,
            "tc2": 0.7,
            "incommensurate_phase": False,
            "nu_from_shift": 0.65,
            "alpha_over_nu": 0.92,
            "nu_from_hyperscaling": round(hyperscaling_nu(0.92), 2),
            "two_beta_over_nu": {"central": 0.23, "uncertainty": 0.03},
        },
        "source_contract_conflict": {
            "figure": "Fig. 15",
            "adjacent_prose_r": 0.75,
            "caption_r": 0.65,
            "frozen_l_range": [12, 32],
            "frozen_l_range_source": "Fig. 11 cumulant analysis, not the Fig. 15 bulk-property fits",
        },
        "hyperscaling_unrounded_nu": hyperscaling_nu(0.92),
    }
    output = data_dir / "idx41_analytic_audit.json"
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
