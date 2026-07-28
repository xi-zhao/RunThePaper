from __future__ import annotations

import argparse
import csv
import os
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np


WORKSPACE = Path(__file__).resolve().parents[1]
DATA_DIR = WORKSPACE / "outputs" / "data"
FIGURE_DIR = WORKSPACE / "outputs" / "figures"


def _require_guard(target_id: str, stage: str) -> None:
    if os.environ.get("PRAGENT_GUARDED_TARGET_ID") != target_id:
        raise SystemExit(
            f"render_reproduction.py --target {target_id} must be called "
            f"through run_target.py for {target_id}"
        )
    if os.environ.get("PRAGENT_GUARDED_STAGE") != stage:
        raise SystemExit("script --stage must match PRAGENT_GUARDED_STAGE")


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _set_paper_style() -> None:
    mpl.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["STIX Two Text", "STIXGeneral", "DejaVu Serif"],
            "mathtext.fontset": "stix",
            "axes.linewidth": 1.5,
            "xtick.major.width": 1.5,
            "ytick.major.width": 1.5,
            "xtick.major.size": 8,
            "ytick.major.size": 8,
            "xtick.direction": "in",
            "ytick.direction": "in",
            "xtick.top": True,
            "ytick.right": True,
            "savefig.facecolor": "white",
            "figure.facecolor": "white",
        }
    )


def _render_t001() -> Path:
    rows = _read_rows(DATA_DIR / "swap_dephasing.csv")
    time = np.array([float(row["time"]) for row in rows])
    exact = np.array([float(row["exact_overlap"]) for row in rows])
    sampled = np.array([float(row["quasi_sampled_overlap"]) for row in rows])

    # Match the source panel's raster extent and axes placement. All plotted
    # coordinates still come exclusively from the independently generated CSV.
    fig = plt.figure(figsize=(10.94, 7.64), dpi=100)
    ax = fig.add_axes([0.1152, 0.1440, 0.8650, 0.8272])
    ax.plot(
        time,
        exact,
        color="#14365F",
        linewidth=3.6,
        label=r"$e^{t\mathcal{L}}(\rho)$",
        zorder=2,
    )
    ax.plot(
        time,
        sampled,
        linestyle="none",
        marker="o",
        markersize=4.8,
        color="#D64F38",
        label="Quasi-sampling",
        zorder=3,
    )
    ax.set_xlim(-0.2, 10.2)
    ax.set_ylim(0.0, 1.05)
    ax.set_xticks(np.arange(0, 11, 2))
    ax.set_yticks(np.arange(0.0, 1.01, 0.2))
    ax.set_xlabel("Time", fontsize=31)
    ax.set_ylabel(
        r"$\langle\psi_0|\rho(t)|\psi_0\rangle$",
        fontsize=31,
    )
    ax.tick_params(labelsize=19, pad=10)
    legend = ax.legend(
        loc="upper right",
        bbox_to_anchor=(0.972, 0.967),
        fontsize=22,
        frameon=True,
        borderpad=0.45,
        handlelength=2.4,
        labelspacing=0.45,
    )
    legend.get_frame().set_edgecolor("#222222")
    legend.get_frame().set_linewidth(1.8)

    output = FIGURE_DIR / "fig2_swap_dephasing.png"
    fig.savefig(output, dpi=100)
    plt.close(fig)
    return output


def _render_t002() -> Path:
    rows = _read_rows(DATA_DIR / "programming_cost.csv")
    branches: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        branches.setdefault(row["branch"], []).append(row)
    for branch_rows in branches.values():
        branch_rows.sort(key=lambda row: float(row["epsilon"]))

    pure = branches["pure_damping"]
    rotated = branches["damping_plus_z"]
    pure_epsilon = np.array([float(row["epsilon"]) for row in pure])
    pure_kappa = np.array([float(row["kappa"]) for row in pure])
    rotated_epsilon = np.array([float(row["epsilon"]) for row in rotated])
    rotated_kappa = np.array([float(row["kappa"]) for row in rotated])

    fig = plt.figure(figsize=(10.93, 7.64), dpi=100)
    ax = fig.add_axes([0.1107, 0.1440, 0.8555, 0.8272])
    ax.plot(
        pure_epsilon,
        pure_kappa,
        color="#14365F",
        marker="o",
        markersize=7.2,
        linewidth=3.6,
        label="Damping",
        zorder=3,
    )
    ax.plot(
        rotated_epsilon,
        rotated_kappa,
        color="#D64F38",
        marker="o",
        markersize=7.2,
        linewidth=3.6,
        label=r"Damping with $Z$ rotation",
        zorder=3,
    )
    ax.axhline(1.0, color="#777777", linewidth=1.4, linestyle=(0, (5, 2)))
    ax.set_xlim(-0.004, 0.204)
    ax.set_ylim(0.94, 2.30)
    ax.set_xticks(np.arange(0.0, 0.201, 0.025))
    ax.set_yticks(np.arange(1.0, 2.21, 0.2))
    ax.xaxis.set_major_formatter(mpl.ticker.FormatStrFormatter("%.3f"))
    ax.set_xlabel(r"Error rate $\epsilon$", fontsize=31)
    ax.set_ylabel(r"$2^{\gamma_\epsilon(\mathcal{E})}$", fontsize=31)
    ax.tick_params(labelsize=19, pad=9)
    legend = ax.legend(
        loc="upper right",
        bbox_to_anchor=(0.972, 0.972),
        fontsize=22,
        frameon=True,
        borderpad=0.45,
        handlelength=2.4,
        labelspacing=0.45,
    )
    legend.get_frame().set_edgecolor("#222222")
    legend.get_frame().set_linewidth(1.8)

    output = FIGURE_DIR / "fig3_programming_cost.png"
    fig.savefig(output, dpi=100)
    plt.close(fig)
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", choices=["T001", "T002"], required=True)
    parser.add_argument(
        "--stage",
        choices=["exploratory", "final_reproduction"],
        required=True,
    )
    args = parser.parse_args()
    _require_guard(args.target, args.stage)
    _set_paper_style()
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    output = _render_t001() if args.target == "T001" else _render_t002()
    print(output.relative_to(WORKSPACE))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
