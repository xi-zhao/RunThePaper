#!/usr/bin/env python3
"""Independently reproduce Supplementary Fig. S6 from Eq. (S28)."""

from __future__ import annotations

import csv
from dataclasses import asdict
import json
from pathlib import Path
import sys

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np


CODE_ROOT = Path(__file__).resolve().parents[1]
CASE_ROOT = CODE_ROOT.parent
sys.path.insert(0, str(CODE_ROOT))

from src.geometry_adaptive import (  # noqa: E402
    basis_hopping_model,
    model_eq11,
    model_eq15,
)
from src.supplementary_models import (  # noqa: E402
    find_fermi_points,
    winding_sweep,
)


# An even midpoint grid avoids the transverse momenta 0 and +/-pi/2 where the
# point gap closes and the winding number is mathematically undefined.
FIXED_SAMPLES = 240
INTEGRATION_SAMPLES = 4096


def configure_matplotlib() -> None:
    mpl.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
            "mathtext.fontset": "stix",
            "axes.linewidth": 0.8,
            "pdf.fonttype": 42,
            "svg.fonttype": "none",
        }
    )


def write_rows(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def compute() -> tuple[list[dict[str, object]], list[dict[str, object]], dict[str, object]]:
    fixed = (np.arange(FIXED_SAMPLES, dtype=np.float64) + 0.5) * (
        2.0 * np.pi / FIXED_SAMPLES
    ) - np.pi
    normal_winding = winding_sweep(
        model_eq11(),
        fixed,
        integration_axis=1,
        momentum_samples=INTEGRATION_SAMPLES,
    )
    critical_basis = basis_hopping_model(model_eq15(), "rhombus")
    critical_winding = winding_sweep(
        critical_basis,
        fixed,
        integration_axis=1,
        momentum_samples=INTEGRATION_SAMPLES,
    )
    winding_rows: list[dict[str, object]] = []
    for panel, basis, values in (
        ("normal_eq11_square", "kx_fixed_ky_integrated", normal_winding),
        ("critical_eq15_rhombus", "k11_fixed_k1bar1_integrated", critical_winding),
    ):
        for momentum, winding in zip(fixed, values, strict=True):
            winding_rows.append(
                {
                    "panel": panel,
                    "basis": basis,
                    "fixed_momentum": momentum,
                    "reference_energy_real": 0.0,
                    "reference_energy_imag": 0.0,
                    "winding": int(winding),
                }
            )

    fermi_rows: list[dict[str, object]] = []
    normal_points = find_fermi_points(model_eq11())
    critical_points = find_fermi_points(model_eq15())
    for point in normal_points:
        fermi_rows.append(
            {
                "panel": "normal_eq11_square",
                "momentum_x": point.momentum_1,
                "momentum_y": point.momentum_2,
                "display_momentum_1": point.momentum_1,
                "display_momentum_2": point.momentum_2,
                "charge": point.charge,
                "residual": point.residual,
                "jacobian_determinant": point.jacobian_determinant,
            }
        )
    for point in critical_points:
        k_11 = 0.5 * (point.momentum_1 + point.momentum_2)
        k_1bar1 = 0.5 * (-point.momentum_1 + point.momentum_2)
        fermi_rows.append(
            {
                "panel": "critical_eq15_rhombus",
                "momentum_x": point.momentum_1,
                "momentum_y": point.momentum_2,
                "display_momentum_1": k_11,
                "display_momentum_2": k_1bar1,
                "charge": point.charge,
                "residual": point.residual,
                "jacobian_determinant": point.jacobian_determinant,
            }
        )

    normal_values = set(normal_winding.tolist())
    critical_values = set(critical_winding.tolist())
    acceptance = {
        "normal_winding_is_sign_consistent": normal_values == {0, 1},
        "critical_winding_changes_sign": critical_values == {-1, 1},
        "normal_fermi_points_resolved": len(normal_points) == 2,
        "critical_fermi_points_resolved": len(critical_points) == 4,
        "normal_topological_charge_balances": sum(point.charge for point in normal_points)
        == 0,
        "critical_topological_charge_balances": sum(
            point.charge for point in critical_points
        )
        == 0,
        "fermi_point_residuals_small": max(
            point.residual for point in (*normal_points, *critical_points)
        )
        < 1e-9,
    }
    check = {
        "schema_version": 1,
        "paper_id": "2407.01296",
        "target_id": "T005",
        "figure_refs": ["Supplementary Fig. S6(a)", "Supplementary Fig. S6(b)"],
        "status": "passed" if all(acceptance.values()) else "failed",
        "artifact_stage": "scientific_reproduction",
        "generated_data_provenance": "independent_numerics",
        "source_pixels_copied_into_reproduction": False,
        "formula_refs": ["EQC004", "EQC009"],
        "reference_energy": [0.0, 0.0],
        "fixed_momentum_samples": FIXED_SAMPLES,
        "integration_samples": INTEGRATION_SAMPLES,
        "normal_winding_values": sorted(normal_values),
        "critical_winding_values": sorted(critical_values),
        "normal_fermi_points": [asdict(point) for point in normal_points],
        "critical_fermi_points": [asdict(point) for point in critical_points],
        "acceptance": acceptance,
    }
    return winding_rows, fermi_rows, check


def render(
    path: Path,
    winding_rows: list[dict[str, object]],
    fermi_rows: list[dict[str, object]],
) -> None:
    configure_matplotlib()
    figure, axes = plt.subplots(1, 2, figsize=(7.2, 3.15), constrained_layout=True)
    settings = (
        (
            axes[0],
            "normal_eq11_square",
            r"$k_x$",
            r"$k_y$",
            "(a) Eq. (11): sign-consistent winding",
        ),
        (
            axes[1],
            "critical_eq15_rhombus",
            r"$k_{11}$",
            r"$k_{1\bar{1}}$",
            "(b) Eq. (15): winding sign change",
        ),
    )
    for axis, panel, x_label, y_label, title in settings:
        selected = [row for row in winding_rows if row["panel"] == panel]
        winding = np.asarray([row["winding"] for row in selected], dtype=float)
        background = np.repeat(winding[None, :], 2, axis=0)
        axis.imshow(
            background,
            extent=(-np.pi, np.pi, -np.pi, np.pi),
            origin="lower",
            aspect="equal",
            cmap="coolwarm",
            vmin=-1,
            vmax=1,
            alpha=0.32,
            interpolation="nearest",
        )
        points = [row for row in fermi_rows if row["panel"] == panel]
        for charge, color in ((1, "#0072B2"), (-1, "#D55E00")):
            charged = [row for row in points if int(row["charge"]) == charge]
            axis.scatter(
                [row["display_momentum_1"] for row in charged],
                [row["display_momentum_2"] for row in charged],
                s=35,
                color=color,
                edgecolor="white",
                linewidth=0.5,
                label=f"charge {charge:+d}",
                zorder=3,
            )
        axis.set_xlim(-np.pi, np.pi)
        axis.set_ylim(-np.pi, np.pi)
        axis.set_xticks((-np.pi, 0.0, np.pi), labels=(r"$-\pi$", "0", r"$\pi$"))
        axis.set_yticks((-np.pi, 0.0, np.pi), labels=(r"$-\pi$", "0", r"$\pi$"))
        axis.set_xlabel(x_label)
        axis.set_ylabel(y_label)
        axis.set_title(title, loc="left", fontsize=9.5)
        axis.legend(frameon=False, fontsize=7, loc="upper right")

    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=240)
    figure.savefig(path.with_suffix(".svg"))
    plt.close(figure)


def main() -> int:
    winding_rows, fermi_rows, check = compute()
    data_dir = CASE_ROOT / "outputs" / "data"
    check_dir = CASE_ROOT / "outputs" / "checks"
    figure_path = CASE_ROOT / "outputs" / "figures" / "supp_fig_s6_reproduction.png"
    write_rows(data_dir / "supp_fig_s6_winding.csv", winding_rows)
    write_rows(data_dir / "supp_fig_s6_fermi_points.csv", fermi_rows)
    render(figure_path, winding_rows, fermi_rows)
    check_dir.mkdir(parents=True, exist_ok=True)
    (check_dir / "supp_fig_s6.json").write_text(
        json.dumps(check, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(check, indent=2, ensure_ascii=False))
    return 0 if check["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
