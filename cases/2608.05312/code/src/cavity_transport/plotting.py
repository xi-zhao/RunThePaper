"""Data-backed plots for the paper targets."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

from .artifacts import read_csv


BLUE = "#0077b6"
ORANGE = "#d95f02"
GREEN = "#009e73"
RED = "#b23a2b"
GRAY = "#777777"
PINK = "#ff4fa3"


def _log_edges(values: np.ndarray) -> np.ndarray:
    """Cell edges for positive log-spaced centers."""

    centers = np.asarray(values, dtype=float)
    if centers.ndim != 1 or centers.size < 2 or np.any(centers <= 0):
        raise ValueError("log-grid centers must contain at least two positive values")
    interior = np.sqrt(centers[:-1] * centers[1:])
    return np.concatenate(
        ([centers[0] ** 2 / interior[0]], interior, [centers[-1] ** 2 / interior[-1]])
    )


def _finish(fig: plt.Figure, png_path: Path) -> dict[str, str]:
    png_path.parent.mkdir(parents=True, exist_ok=True)
    pdf_path = png_path.with_suffix(".pdf")
    fig.savefig(png_path, dpi=220, bbox_inches="tight")
    fig.savefig(pdf_path, bbox_inches="tight")
    plt.close(fig)
    return {"png": str(png_path), "pdf": str(pdf_path)}


def render_side_by_side(reference: Path, reproduction: Path, output: Path) -> Path:
    """Feature-level comparison; intentionally no pixel-difference score."""

    ref = np.asarray(Image.open(reference).convert("RGB"))
    rep = np.asarray(Image.open(reproduction).convert("RGB"))
    fig, axes = plt.subplots(1, 2, figsize=(15, 6), constrained_layout=True)
    axes[0].imshow(ref)
    axes[0].set_title("Paper source figure (reference only)")
    axes[1].imshow(rep)
    axes[1].set_title("Independent reproduction")
    for axis in axes:
        axis.axis("off")
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return output


def plot_dynamics(data_path: Path, output: Path) -> dict[str, str]:
    rows = read_csv(data_path)
    fig, axes = plt.subplots(1, 4, figsize=(16, 4.2), constrained_layout=True)

    def series(panel: str, mechanism: str, n_sites: int, observable: str):
        selected = [
            row
            for row in rows
            if row["panel"] == panel
            and row["mechanism"] == mechanism
            and int(row["n_sites"]) == n_sites
            and row["observable"] == observable
        ]
        selected.sort(key=lambda row: float(row["time"]))
        return (
            np.asarray([float(row["time"]) for row in selected]),
            np.asarray([float(row["mean"]) for row in selected]),
        )

    shades = {4: "#ffb482", 16: "#e66c2c", 32: "#8c2d04"}
    for n_sites in (4, 16, 32):
        t, p_dark = series("ab", "dephasing", n_sites, "dark")
        axes[0].plot(t, p_dark, "--", color=shades[n_sites], label=f"deph N={n_sites}")
        t, p_sink = series("ab", "dephasing", n_sites, "sink")
        axes[1].plot(t, p_sink, "--", color=shades[n_sites], label=f"deph N={n_sites}")
        t, p_dark = series("ab", "rescue", n_sites, "dark")
        axes[0].plot(t, p_dark, color=BLUE, alpha=0.45 + n_sites / 90)
        t, p_sink = series("ab", "rescue", n_sites, "sink")
        axes[1].plot(t, p_sink, color=BLUE, alpha=0.45 + n_sites / 90)

    axes[0].plot([], [], color=BLUE, label="rescue (all N)")
    axes[1].plot([], [], color=BLUE, label="rescue (all N)")
    axes[0].set_title("(a) dark population")
    axes[1].set_title("(b) sink efficiency")
    axes[0].legend(fontsize=7)
    axes[1].legend(fontsize=7)

    styles = {
        "bright": (GREEN, "-", "bright"),
        "dark": (RED, "-", "dark"),
        "cavity": (GRAY, ":", "cavity"),
        "sink": ("black", "--", "sink"),
    }
    for axis, mechanism, title in (
        (axes[2], "rescue", "(c) rescue, N=6"),
        (axes[3], "dephasing", "(d) dephasing, N=6"),
    ):
        for observable, (color, line_style, label) in styles.items():
            t, value = series("cd", mechanism, 6, observable)
            axis.plot(t, value, line_style, color=color, label=label)
        axis.set_title(title)
        axis.legend(fontsize=8)

    for axis in axes:
        axis.set_xlim(0, 30)
        axis.set_ylim(0, 1.05)
        axis.set_xlabel(r"time $t$ ($\hbar$/meV)")
        axis.grid(alpha=0.15)
    axes[0].set_ylabel("population")
    axes[2].set_ylabel("population")
    return _finish(fig, output)


def plot_scaling(data_path: Path, output: Path) -> dict[str, str]:
    rows = read_csv(data_path)
    fig, axis = plt.subplots(figsize=(7.8, 5.2), constrained_layout=True)
    styles = {
        "rescue": (BLUE, "o", "-", "rescue channel"),
        "dephasing": (ORANGE, "s", "--", "dephasing channel"),
        "baseline": (GRAY, "^", ":", "no dissipation"),
        "combined": (PINK, "D", "none", "combined channel"),
    }
    for mechanism, (color, marker, line, label) in styles.items():
        selected = [row for row in rows if row["mechanism"] == mechanism]
        selected.sort(key=lambda row: int(row["n_sites"]))
        n = np.asarray([int(row["n_sites"]) for row in selected])
        eta = np.asarray([float(row["eta_mean"]) for row in selected])
        err = np.asarray([float(row["eta_sem"]) for row in selected])
        axis.errorbar(
            n,
            eta,
            yerr=err,
            color=color,
            marker=marker,
            linestyle=line,
            capsize=2,
            label=label,
        )
    axis.set_xlabel("system size, N")
    axis.set_ylabel(r"peak efficiency, $\eta^*$")
    axis.set_xlim(2, 100)
    axis.set_ylim(-0.02, 1.04)
    axis.grid(alpha=0.2)
    axis.legend()
    axis.set_title("Figure 1(c): reconstructed full-Lindbladian size scaling")
    return _finish(fig, output)


def plot_scaling_laws(data_path: Path, fit_payload: dict, output: Path) -> dict[str, str]:
    rows = read_csv(data_path)
    by_n: dict[int, dict[str, float]] = {}
    for row in rows:
        by_n.setdefault(int(row["n_sites"]), {})[row["mechanism"]] = float(row["eta_mean"])
    n = np.asarray(sorted(by_n))
    gap = np.asarray([by_n[int(x)]["rescue"] - by_n[int(x)]["dephasing"] for x in n])
    deficit = 1.0 - gap

    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.2), constrained_layout=True)
    axes[0].plot(n, gap, "o", color=BLUE, label="generated gap")
    log_fit = fit_payload["log_fit_n_le_32"]
    xfit = np.linspace(3, 96, 300)
    yfit = log_fit["slope"] * np.log(xfit) + log_fit["intercept"]
    axes[0].plot(xfit[xfit <= 32], yfit[xfit <= 32], color="black", label="fit N≤32")
    axes[0].plot(xfit[xfit > 32], yfit[xfit > 32], "--", color="black", alpha=0.6)
    axes[0].axhspan(1, max(1.08, float(yfit.max())), color="gray", alpha=0.15)
    axes[0].set_xlabel("N")
    axes[0].set_ylabel(r"$\Delta\eta_{peak}$")
    axes[0].legend(fontsize=8)
    axes[0].grid(alpha=0.2)

    axes[1].loglog(n, deficit, "o", color=BLUE, label="1 - generated gap")
    power = fit_payload["power_fit_n_ge_16"]
    xpower = np.logspace(np.log10(16), np.log10(max(n)), 200)
    ypower = np.exp(power["log_prefactor"]) * xpower ** (-power["alpha"])
    axes[1].loglog(xpower, ypower, color="black", label=fr"fit $N^{{-{power['alpha']:.2f}}}$")
    axes[1].loglog(xpower, ypower[0] * (xpower / xpower[0]) ** -1, ":", color=GRAY, label=r"$N^{-1}$")
    axes[1].set_xlabel("N")
    axes[1].set_ylabel(r"$1-\Delta\eta_{peak}$")
    axes[1].legend(fontsize=8)
    axes[1].grid(alpha=0.2, which="both")
    return _finish(fig, output)


def _map_arrays(rows: list[dict[str, str]], n_sites: int):
    selected = [row for row in rows if int(row["n_sites"]) == n_sites]
    x = np.asarray(sorted({float(row["thermal_ratio"]) for row in selected}))
    y = np.asarray(sorted({float(row["rate_ratio"]) for row in selected}))
    z = np.full((len(y), len(x)), np.nan)
    index_x = {value: i for i, value in enumerate(x)}
    index_y = {value: i for i, value in enumerate(y)}
    for row in selected:
        z[index_y[float(row["rate_ratio"])], index_x[float(row["thermal_ratio"])]] = float(row["delta_eta"])
    return x, y, z


def plot_temperature(
    map_path: Path,
    lines_path: Path,
    output: Path,
) -> dict[str, str]:
    map_rows = read_csv(map_path)
    line_rows = read_csv(lines_path)
    fig = plt.figure(figsize=(8, 9), constrained_layout=True)
    grid = fig.add_gridspec(2, 2, height_ratios=(1.35, 1))
    map_axis = fig.add_subplot(grid[0, :])
    axes = [fig.add_subplot(grid[1, 0]), fig.add_subplot(grid[1, 1])]
    x, y, z = _map_arrays(map_rows, 6)
    mesh = map_axis.pcolormesh(
        _log_edges(x), _log_edges(y), z, shading="auto", cmap="RdBu_r", vmin=-0.35, vmax=0.35
    )
    map_axis.contour(x, y, z, levels=[0], colors="black", linewidths=1.5)
    map_axis.set_xscale("log")
    map_axis.set_yscale("log")
    map_axis.set_xlabel(r"$k_BT/\Delta$")
    map_axis.set_ylabel(r"$\gamma_{rec}/\gamma_{deph}$")
    map_axis.set_title(r"(a) N=6, $\Delta\eta=\eta_{rec}-\eta_{deph}$")
    fig.colorbar(mesh, ax=map_axis, label=r"$\Delta\eta$")

    colors = {"both": "black", "rescue": BLUE, "dephasing": ORANGE}
    lines = {"both": "-", "rescue": "-", "dephasing": "--"}
    for axis, n_sites, title in zip(axes, (6, 64), ("(b) N=6", "(c) N=64")):
        for mechanism in ("both", "rescue", "dephasing"):
            selected = [
                row for row in line_rows
                if int(row["n_sites"]) == n_sites and row["mechanism"] == mechanism
            ]
            selected.sort(key=lambda row: float(row["thermal_ratio"]))
            axis.plot(
                [float(row["thermal_ratio"]) for row in selected],
                [float(row["eta_mean"]) for row in selected],
                lines[mechanism],
                color=colors[mechanism],
                marker="o" if mechanism == "rescue" else None,
                markersize=3,
                label=mechanism,
            )
        axis.set_xscale("log")
        axis.set_ylim(0, 1.05)
        axis.set_xlabel(r"$k_BT/\Delta$")
        axis.set_ylabel(r"efficiency $\eta$")
        axis.set_title(title)
        axis.grid(alpha=0.2)
        axis.legend(fontsize=8)
    return _finish(fig, output)


def plot_temperature_n64(map_path: Path, output: Path) -> dict[str, str]:
    rows = read_csv(map_path)
    x, y, z = _map_arrays(rows, 64)
    fig, axis = plt.subplots(figsize=(7.2, 4.8), constrained_layout=True)
    mesh = axis.pcolormesh(
        _log_edges(x), _log_edges(y), z, shading="auto", cmap="RdBu_r", vmin=-0.15, vmax=0.9
    )
    axis.contour(x, y, z, levels=[0], colors="black", linewidths=1.5)
    axis.set_xscale("log")
    axis.set_yscale("log")
    axis.set_xlabel(r"$k_BT/\Delta$")
    axis.set_ylabel(r"$\gamma_{rec}/\gamma_{deph}$")
    axis.set_title(r"Figure S4: N=64 rescue advantage $\Delta\eta$")
    fig.colorbar(mesh, ax=axis, label=r"$\Delta\eta$")
    return _finish(fig, output)


def plot_site_n_sweep(data_path: Path, output: Path) -> dict[str, str]:
    rows = read_csv(data_path)
    map_rows = [row for row in rows if row["record_kind"] == "map"]
    rec_rates = np.asarray(sorted({float(row["gamma_rec"]) for row in map_rows}))
    deph_rates = np.asarray(sorted({float(row["gamma_deph"]) for row in map_rows}))
    z = np.empty((len(deph_rates), len(rec_rates)))
    ix = {value: i for i, value in enumerate(rec_rates)}
    iy = {value: i for i, value in enumerate(deph_rates)}
    for row in map_rows:
        z[iy[float(row["gamma_deph"])], ix[float(row["gamma_rec"])]] = float(row["eta_mean"])

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5), constrained_layout=True)
    mesh = axes[0].pcolormesh(
        _log_edges(rec_rates),
        _log_edges(deph_rates),
        z,
        shading="auto",
        cmap="viridis",
        vmin=0,
        vmax=1,
    )
    axes[0].set_xscale("log")
    axes[0].set_yscale("log")
    axes[0].set_xlabel(r"rescue rate $\gamma_{rec}$")
    axes[0].set_ylabel(r"dephasing rate $\gamma_{deph}$")
    axes[0].set_title("(a) site-N drain efficiency")
    fig.colorbar(mesh, ax=axes[0], label=r"$\eta$")
    for mechanism, color, marker in (("rescue", BLUE, "o"), ("dephasing", ORANGE, "s")):
        cut = [row for row in rows if row["record_kind"] == "cut" and row["mechanism"] == mechanism]
        cut.sort(key=lambda row: float(row["rate"]))
        axes[1].plot(
            [float(row["rate"]) for row in cut],
            [float(row["eta_mean"]) for row in cut],
            color=color,
            marker=marker,
            markersize=3,
            label=mechanism,
        )
    axes[1].set_xscale("log")
    axes[1].set_ylim(0, 1.02)
    axes[1].set_xlabel("pure-channel rate (meV)")
    axes[1].set_ylabel(r"efficiency $\eta$")
    axes[1].set_title("(b) pure-channel cuts")
    axes[1].legend()
    axes[1].grid(alpha=0.2)
    return _finish(fig, output)


def plot_site_n_dynamics(data_path: Path, output: Path) -> dict[str, str]:
    rows = read_csv(data_path)
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.1), constrained_layout=True)
    styles = {
        "bright": (ORANGE, "-"),
        "dark": (BLUE, "-"),
        "cavity": (GREEN, ":"),
        "sink": (GRAY, "--"),
    }
    for axis, condition, title in zip(
        axes, ("without_rescue", "with_rescue"), ("(a) without rescue", "(b) with rescue")
    ):
        for observable, (color, style) in styles.items():
            selected = [
                row for row in rows
                if row["condition"] == condition and row["observable"] == observable
            ]
            selected.sort(key=lambda row: float(row["time"]))
            axis.plot(
                [float(row["time"]) for row in selected],
                [float(row["value"]) for row in selected],
                style,
                color=color,
                label=observable,
            )
        axis.set_xlim(0, 60)
        axis.set_ylim(0, 1.02)
        axis.set_xlabel(r"time ($\hbar$/meV)")
        axis.set_ylabel("manifold population")
        axis.set_title(title)
        axis.legend(fontsize=8)
        axis.grid(alpha=0.2)
    return _finish(fig, output)
