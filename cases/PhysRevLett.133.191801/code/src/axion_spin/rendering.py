"""Render independent scientific targets after numerical data are generated."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt


def _style() -> None:
    plt.rcParams.update(
        {
            "font.size": 9,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "figure.dpi": 150,
            "savefig.dpi": 180,
        }
    )


def _save(fig: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def render_all(results: dict[str, Any]) -> list[Path]:
    _style()
    root: Path = results["figure_root"]
    time = results["time"]
    paths: list[Path] = []

    fig, axis = plt.subplots(figsize=(5.0, 2.8))
    axis.plot(
        time,
        results["free_response"],
        color="#2457A7",
        lw=0.8,
        label="Eq. (4) response",
    )
    axis.plot(
        time,
        results["free_envelope"],
        color="#C83E4D",
        lw=1.2,
        label="analytic envelope",
    )
    axis.plot(time, -results["free_envelope"], color="#C83E4D", lw=1.0)
    axis.set(
        xlabel="Time (s)",
        ylabel="Normalized effective field",
        title="T001 - resonant free-decay response",
    )
    axis.legend(frameon=False, ncol=2)
    path = root / "T001_fig2a_free_decay_response.png"
    _save(fig, path)
    paths.append(path)

    fig, axes = plt.subplots(2, 1, figsize=(5.0, 3.7), sharex=True)
    axes[0].plot(time, results["gaussian_drive"].real, color="#6B7280", lw=1.0)
    axes[0].set(ylabel="Drive", title="T002 - Eq. (3) Gaussian-envelope response")
    axes[1].plot(time, results["gaussian_response"].real, color="#2457A7", lw=0.9)
    axes[1].set(xlabel="Time (s)", ylabel="Response")
    path = root / "T002_fig2a_gaussian_response.png"
    _save(fig, path)
    paths.append(path)

    fig, axes = plt.subplots(2, 1, figsize=(5.0, 3.7), sharex=True)
    axes[0].plot(time, results["chirp_drive"].real, color="#6B7280", lw=0.7)
    axes[0].set(ylabel="Drive", title="T003 - Eq. (3) linear-chirp response")
    axes[1].plot(time, results["chirp_response"].real, color="#2457A7", lw=0.8)
    axes[1].set(xlabel="Time (s)", ylabel="Response")
    path = root / "T003_fig2a_chirp_response.png"
    _save(fig, path)
    paths.append(path)

    filtered = results["filter_result"]
    lag_time = filtered.lags * results["filter_dt"]
    fig, axes = plt.subplots(2, 1, figsize=(5.2, 3.8), sharex=False)
    axes[0].plot(time, results["filter_record"], color="#243B6B", lw=0.35)
    axes[0].set(
        ylabel="Synthetic field (pT)",
        title="T004 - matched-filter injection test (synthetic)",
    )
    axes[1].plot(lag_time, filtered.estimates, color="#C83E4D", lw=1.0)
    axes[1].axvline(
        filtered.best_lag * results["filter_dt"], color="black", ls="--", lw=0.8
    )
    axes[1].set(xlabel="Template arrival time (s)", ylabel="Estimated amplitude (pT)")
    path = root / "T004_fig2b_matched_filter_injection.png"
    _save(fig, path)
    paths.append(path)

    fig, axis = plt.subplots(figsize=(4.8, 3.0))
    values = [
        float(results["analytic_sigma"]),
        float(results["repeated_sigma"]),
        float(results["paper_filtered_sigma"]),
    ]
    labels = [
        "Synthetic\nsingle estimate",
        "Synthetic\n1000-shot mean",
        "Paper printed\n30 fT",
    ]
    axis.bar(labels, values, color=["#4C78A8", "#72B7B2", "#E45756"])
    axis.set_yscale("log")
    axis.set_ylabel("Field-estimator sigma (pT)")
    axis.set_title("T005 - matched-filter sensitivity accounting")
    path = root / "T005_fig2c_filter_sensitivity.png"
    _save(fig, path)
    paths.append(path)

    fig, axes = plt.subplots(1, 2, figsize=(6.4, 2.8), layout="constrained")
    axes[0].plot(
        results["gaussian_grid"], results["gaussian_density"], color="#C83E4D", lw=1.4
    )
    axes[0].set(
        xlabel="Exotic field (fT)",
        ylabel="Density (1/fT)",
        title="Printed 30 fT Gaussian",
    )
    axes[1].bar(
        ["stat", "sys", "combined"],
        [140.0, 45.0, results["total_uncertainty"]],
        color=["#4C78A8", "#F2CF5B", "#72B7B2"],
    )
    axes[1].set(ylabel="Uncertainty (aT)", title="Quadrature propagation")
    fig.suptitle("T006 - Fig. 4(a) statistical component only")
    path = root / "T006_fig4a_statistical_model.png"
    _save(fig, path)
    paths.append(path)

    fig, axis = plt.subplots(figsize=(4.8, 3.1))
    axis.loglog(
        results["masses_microev"],
        results["coupling"],
        color="#D62728",
        lw=1.6,
        label="point-source Eq. (1)",
    )
    axis.axvspan(10.0, 1000.0, color="#E5E7EB", alpha=0.7, label="axion window")
    axis.scatter(
        [results["anchor_mass_microev"]],
        [results["anchor_coupling"]],
        color="black",
        s=18,
        zorder=4,
        label="printed anchor normalization",
    )
    axis.set(
        xlabel="Axion mass (micro-eV)",
        ylabel=r"$|g_{ps}^n g_{ps}^n|/4$",
        title="T007 - independent mass dependence",
    )
    axis.legend(frameon=False, fontsize=7)
    path = root / "T007_fig4b_point_source_constraint.png"
    _save(fig, path)
    paths.append(path)
    return paths
