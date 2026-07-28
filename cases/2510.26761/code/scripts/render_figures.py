#!/usr/bin/env python3
"""Render the public figures from the included generated field arrays."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import TwoSlopeNorm
from matplotlib.patches import Circle


CODE_ROOT = Path(__file__).resolve().parents[1]
CASE_ROOT = CODE_ROOT.parent
DATA_ROOT = CASE_ROOT / "outputs" / "data"
FIGURE_ROOT = CASE_ROOT / "outputs" / "figures"


def diverging_norm(field: np.ndarray) -> TwoSlopeNorm:
    limit = float(np.max(np.abs(field)))
    return TwoSlopeNorm(vmin=-limit, vcenter=0.0, vmax=limit)


def render_overview() -> Path:
    fields = np.load(DATA_ROOT / "overview_fields.npz")
    metrics = json.loads((DATA_ROOT / "overview_metrics.json").read_text())
    cut_axis = fields["cut_axis"]
    full_cut = fields["full_cut"]
    slice_axis = fields["slice_axis"]
    equal_slice = fields["equal_slice"]
    com_axis = fields["com_axis"]
    com_wigner = fields["com_wigner"]
    smoothed = fields["smoothed_com_wigner"]

    fig = plt.figure(figsize=(16, 4.8), constrained_layout=True)
    ax3d = fig.add_subplot(1, 4, 1, projection="3d")
    grid = np.meshgrid(cut_axis, cut_axis, cut_axis, indexing="ij")
    positive = full_cut > 0.15 * float(full_cut.max())
    negative = full_cut < 0.15 * float(full_cut.min())
    ax3d.scatter(
        grid[0][positive],
        grid[1][positive],
        grid[2][positive],
        s=4,
        alpha=0.28,
        color="#dc2626",
        label="positive",
    )
    ax3d.scatter(
        grid[0][negative],
        grid[1][negative],
        grid[2][negative],
        s=4,
        alpha=0.28,
        color="#2563eb",
        label="negative",
    )
    ax3d.set_title("Three-mode cut")
    ax3d.set_xlabel(r"$\mathrm{Re}\,\alpha_+$")
    ax3d.set_ylabel(r"$\mathrm{Im}\,\alpha_+$")
    ax3d.set_zlabel(r"$\mathrm{Re}\,\alpha_-$")
    ax3d.legend(frameon=False, fontsize=8)

    panels = [
        (equal_slice, slice_axis, "Equal-coordinate slice"),
        (com_wigner, com_axis, "Center-of-mass Wigner"),
        (smoothed, com_axis, "Gaussian-smoothed Wigner"),
    ]
    for index, (field, axis, title) in enumerate(panels, start=2):
        ax = fig.add_subplot(1, 4, index)
        image = ax.imshow(
            field,
            origin="lower",
            extent=[axis[0], axis[-1], axis[0], axis[-1]],
            cmap="RdBu_r",
            norm=diverging_norm(field),
            aspect="equal",
        )
        ax.contour(
            axis,
            axis,
            field,
            levels=[0.0],
            colors="black",
            linewidths=0.7,
        )
        ax.set_title(title)
        ax.set_xlabel("real coordinate")
        ax.set_ylabel("imaginary coordinate")
        fig.colorbar(image, ax=ax, shrink=0.78)

    volume = metrics["convergence"][-1]["negativity_volume"]
    derived = metrics["state_derived_gme_bound"]
    printed = metrics["source_printed_gme_bound"]
    fig.suptitle(
        "Fig. 1 numerical fields — "
        f"N={volume:.7f}, derived bound={derived:.7f}, printed bound={printed:.7f}",
        fontsize=12,
    )
    output = FIGURE_ROOT / "overview_numeric_surfaces.png"
    FIGURE_ROOT.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return output


def render_w_state() -> Path:
    fields = np.load(DATA_ROOT / "w_state_fields.npz")
    metrics = json.loads((DATA_ROOT / "w_state_metrics.json").read_text())
    alpha_axis = fields["alpha_axis"]
    wigner = fields["wigner"]
    xi_axis = fields["xi_axis"]
    characteristic = fields["characteristic"]
    difference_real = fields["difference_points_real"]
    difference_imag = fields["difference_points_imag"]

    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.8), constrained_layout=True)
    image0 = axes[0].imshow(
        wigner,
        origin="lower",
        extent=[alpha_axis[0], alpha_axis[-1], alpha_axis[0], alpha_axis[-1]],
        cmap="RdBu_r",
        norm=diverging_norm(wigner),
        aspect="equal",
    )
    axes[0].contour(alpha_axis, alpha_axis, wigner, levels=[0.0], colors="black")
    axes[0].add_patch(
        Circle((0.0, 0.0), metrics["disk_radius"], fill=False, color="#f59e0b", lw=2)
    )
    axes[0].set_title(
        "Finite-disk witness\n"
        f"rcrit={metrics['critical_radius']:.7f}, r=0.7 margin="
        f"{metrics['certification_margin']:.2e}"
    )
    axes[0].set_xlabel(r"$\mathrm{Re}\,\alpha$")
    axes[0].set_ylabel(r"$\mathrm{Im}\,\alpha$")
    fig.colorbar(image0, ax=axes[0], shrink=0.82)

    image1 = axes[1].imshow(
        characteristic,
        origin="lower",
        extent=[xi_axis[0], xi_axis[-1], xi_axis[0], xi_axis[-1]],
        cmap="RdBu_r",
        norm=diverging_norm(characteristic),
        aspect="equal",
    )
    axes[1].scatter(
        difference_real,
        difference_imag,
        marker="x",
        s=36,
        linewidths=1.2,
        color="black",
    )
    axes[1].set_title(
        "Finite characteristic witness\n"
        f"19 differences, witness={metrics['characteristic_witness']:.7f}"
    )
    axes[1].set_xlabel(r"$\mathrm{Re}\,\xi$")
    axes[1].set_ylabel(r"$\mathrm{Im}\,\xi$")
    fig.colorbar(image1, ax=axes[1], shrink=0.82)

    output = FIGURE_ROOT / "w_state_wigner_characteristic.png"
    FIGURE_ROOT.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return output


def main() -> int:
    for output in (render_overview(), render_w_state()):
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
