from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from lyapunov_band import write_json


def plot_case(workspace: Path) -> dict:
    workspace = workspace.resolve()
    data_dir = workspace / "outputs" / "data"
    figure_dir = workspace / "outputs" / "figures"
    figure_dir.mkdir(parents=True, exist_ok=True)

    fig3_path = plot_fig3(data_dir, figure_dir)
    fig4_path = plot_fig4(data_dir, figure_dir)
    fig5_path = plot_fig5(data_dir, figure_dir)
    result = {
        "status": "passed",
        "artifact_stage": "exploratory",
        "parameter_match": "reduced_scale",
        "figures": [
            {"paper_item": "Fig. 3", "path": str(fig3_path.relative_to(workspace)), "data_backed": True},
            {"paper_item": "Fig. 4", "path": str(fig4_path.relative_to(workspace)), "data_backed": True},
            {"paper_item": "Fig. 5", "path": str(fig5_path.relative_to(workspace)), "data_backed": True},
        ],
    }
    write_json(workspace / "outputs" / "checks" / "plot_artifacts.json", result)
    return result


def plot_fig3(data_dir: Path, figure_dir: Path) -> Path:
    grid = _read_csv(data_dir / "fig3_lyapunov_grid.csv")
    real_axis, imag_axis, fields = _reshape_grid(grid)
    scaling = _read_csv(data_dir / "fig3_potential_scaling.csv")

    fig, axes = plt.subplots(1, 3, figsize=(12.5, 3.7), constrained_layout=True)
    extent = [real_axis[0], real_axis[-1], imag_axis[0], imag_axis[-1]]
    image = axes[0].imshow(
        fields["ed_histogram_norm"],
        origin="lower",
        extent=extent,
        aspect="auto",
        cmap="magma",
    )
    axes[0].set_title("(a) OBC exact diagonalization")
    fig.colorbar(image, ax=axes[0], label="normalized density")

    image = axes[1].imshow(
        fields["lyapunov_density_positive_norm"],
        origin="lower",
        extent=extent,
        aspect="auto",
        cmap="magma",
    )
    _plot_mobility_contours(axes[1], real_axis, imag_axis, fields, color="#00d5ff", linewidth=1.3)
    axes[1].set_title("(c) Lyapunov density + mobility edge")
    fig.colorbar(image, ax=axes[1], label="normalized density")

    for label, color, marker in [("skin", "#2563eb", "*"), ("alm", "#dc2626", "s")]:
        subset = scaling[scaling["label"] == label]
        lengths = subset["L"].astype(float)
        deviations = subset["delta_phi"].astype(float)
        slope, intercept = np.polyfit(np.log(lengths), np.log(deviations), 1)
        axes[2].loglog(lengths, deviations, marker=marker, color=color, linestyle="none", label=f"{label}: fit {slope:.2f}")
        dense_lengths = np.geomspace(lengths.min(), lengths.max(), 100)
        axes[2].loglog(dense_lengths, np.exp(intercept) * dense_lengths**slope, color=color, linewidth=1.2)
    axes[2].set_title("(d) finite-size potential convergence")
    axes[2].set_xlabel("L")
    axes[2].set_ylabel(r"$\Delta\phi$")
    axes[2].legend(frameon=False, fontsize=8)

    for axis in axes[:2]:
        axis.set_xlabel(r"Re $E$")
        axis.set_ylabel(r"Im $E$")
    fig.suptitle("arXiv:2507.09447 — exploratory reduced-scale Fig. 3", fontsize=11)
    path = figure_dir / "fig3_reproduction.png"
    fig.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_fig4(data_dir: Path, figure_dir: Path) -> Path:
    grid = _read_csv(data_dir / "fig4_lyapunov_grid.csv")
    real_axis, imag_axis, fields = _reshape_grid(grid)
    winding_points = _read_csv(data_dir / "fig4_winding_checks.csv")

    fig, axes = plt.subplots(1, 2, figsize=(8.6, 3.8), constrained_layout=True)
    extent = [real_axis[0], real_axis[-1], imag_axis[0], imag_axis[-1]]
    for axis, field, title in [
        (axes[0], "ed_histogram_norm", "(a) PBC exact diagonalization"),
        (axes[1], "lyapunov_density_positive_norm", "(b) Lyapunov density + winding"),
    ]:
        image = axis.imshow(fields[field], origin="lower", extent=extent, aspect="auto", cmap="magma")
        axis.set_title(title)
        axis.set_xlabel(r"Re $E$")
        axis.set_ylabel(r"Im $E$")
        fig.colorbar(image, ax=axis, label="normalized density")
    for row in winding_points:
        axes[1].text(
            float(row["real_energy"]),
            float(row["imag_energy"]),
            f"{int(row['lyapunov_winding']):+d}",
            color="white",
            ha="center",
            va="center",
            fontsize=9,
            fontweight="bold",
        )
    fig.suptitle("arXiv:2507.09447 — exploratory reduced-scale Fig. 4", fontsize=11)
    path = figure_dir / "fig4_reproduction.png"
    fig.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_fig5(data_dir: Path, figure_dir: Path) -> Path:
    mobility = _read_csv(data_dir / "fig5_mobility_grid.csv")
    alpha = _read_csv(data_dir / "fig5_alpha.csv")
    w_values = np.unique(mobility["W"])
    colors = plt.cm.magma(np.linspace(0.25, 0.9, len(w_values)))

    fig, axes = plt.subplots(1, 2, figsize=(8.6, 3.8), constrained_layout=True)
    for color, disorder_strength in zip(colors, w_values):
        subset = mobility[np.isclose(mobility["W"], disorder_strength)]
        real_axis, imag_axis, fields = _reshape_grid(subset)
        _plot_mobility_contours(axes[0], real_axis, imag_axis, fields, color=color, linewidth=1.5)
        axes[0].plot([], [], color=color, label=f"W={disorder_strength:g}")
    axes[0].set_title("(a) mobility-edge shrinkage")
    axes[0].set_xlabel(r"Re $E$")
    axes[0].set_ylabel(r"Im $E$")
    axes[0].legend(frameon=False, fontsize=7, ncol=2)

    axes[1].errorbar(
        alpha["W"],
        alpha["alpha"],
        yerr=alpha["binomial_standard_error"],
        color="black",
        marker="o",
        markersize=3.5,
        linewidth=1.0,
        capsize=2,
    )
    axes[1].axvline(2.1, color="#dc2626", linestyle="--", linewidth=1.0, label=r"paper $W_c\approx2.1$")
    axes[1].set_xlim(0.0, 3.0)
    axes[1].set_ylim(-0.03, 1.05)
    axes[1].set_title("(b) Anderson-localized fraction")
    axes[1].set_xlabel("W")
    axes[1].set_ylabel(r"$\alpha$")
    axes[1].legend(frameon=False, fontsize=8)
    fig.suptitle("arXiv:2507.09447 — exploratory reduced-scale Fig. 5", fontsize=11)
    path = figure_dir / "fig5_reproduction.png"
    fig.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return path


def _read_csv(path: Path) -> np.ndarray:
    data = np.genfromtxt(path, delimiter=",", names=True, dtype=None, encoding="utf-8")
    return np.atleast_1d(data)


def _reshape_grid(data: np.ndarray) -> tuple[np.ndarray, np.ndarray, dict[str, np.ndarray]]:
    real_axis = np.unique(data["real_energy"].astype(float))
    imag_axis = np.unique(data["imag_energy"].astype(float))
    order = np.lexsort((data["real_energy"], data["imag_energy"]))
    fields: dict[str, np.ndarray] = {}
    for name in data.dtype.names or ():
        if name in {"real_energy", "imag_energy"}:
            continue
        if np.issubdtype(data[name].dtype, np.number):
            fields[name] = data[name][order].reshape(imag_axis.size, real_axis.size)
    return real_axis, imag_axis, fields


def _plot_mobility_contours(
    axis: plt.Axes,
    real_axis: np.ndarray,
    imag_axis: np.ndarray,
    fields: dict[str, np.ndarray],
    *,
    color: object,
    linewidth: float,
) -> None:
    """Plot gamma_2=0 and gamma_3=0 separately to avoid branch-switch artifacts."""

    for field in ("gamma_2", "gamma_3"):
        values = fields[field]
        if float(np.min(values)) <= 0.0 <= float(np.max(values)):
            axis.contour(
                real_axis,
                imag_axis,
                values,
                levels=[0.0],
                colors=[color],
                linewidths=linewidth,
            )
