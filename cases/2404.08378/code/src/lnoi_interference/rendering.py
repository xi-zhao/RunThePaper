"""Render frozen scientific arrays without consulting source figures."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .quantum import FOCK_LABELS, hom_visibility

COLORS = {"20": "#f28e2b", "11": "#d64f8c", "02": "#22a6a1"}


def _save(fig: plt.Figure, root: Path, name: str) -> Path:
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path


def _style_axis(axis: plt.Axes) -> None:
    axis.spines[["top", "right"]].set_visible(False)
    axis.grid(alpha=0.18, linewidth=0.6)


def render_all(results: dict[str, Any], workspace: Path) -> list[Path]:
    root = workspace / "outputs" / "figures" / "feature"
    paths: list[Path] = []

    fig, axes = plt.subplots(2, 1, figsize=(4.2, 4.5), constrained_layout=True)
    for axis, mode, title in (
        (axes[0], results["pump_mode"], "781 nm"),
        (axes[1], results["telecom_mode"], "1562 nm"),
    ):
        mesh = axis.pcolormesh(
            mode.x_um,
            mode.y_um,
            mode.intensity,
            shading="auto",
            cmap="magma",
        )
        axis.contour(
            mode.x_um,
            mode.y_um,
            mode.refractive_index,
            levels=[1.2, 1.8],
            colors="white",
            linewidths=0.5,
        )
        axis.set(
            xlabel="x (µm)",
            ylabel="y (µm)",
            title=f"{title}, n_eff={mode.effective_index:.4f}",
        )
        fig.colorbar(mesh, ax=axis, label="normalized |E|²")
    paths.append(_save(fig, root, "T001_mode_profiles.png"))

    fig, axes = plt.subplots(
        2, 1, figsize=(5.2, 4.7), sharex=True, constrained_layout=True
    )
    for input_index, axis in enumerate(axes):
        for output_index, output_port in enumerate(("a", "b")):
            axis.plot(
                results["theta_classical"] / np.pi,
                results["transfer"][output_index, input_index],
                label=f"output {output_port}",
            )
        axis.set(
            ylabel="relative intensity", title=f"input {(('a', 'b')[input_index])}"
        )
        _style_axis(axis)
        axis.legend(frameon=False, ncol=2)
    axes[-1].set_xlabel("MZI phase θ / π")
    paths.append(_save(fig, root, "T002_mzi_transfer.png"))

    surface_target = {"11": "T003", "20": "T005", "02": "T007"}
    cut_target = {"11": "T004", "20": "T006", "02": "T008"}
    for state_index, state in enumerate(FOCK_LABELS):
        theta_mesh, phi_mesh = np.meshgrid(
            results["theta_surface"] / np.pi,
            results["phi_surface"] / np.pi,
            indexing="ij",
        )
        fig = plt.figure(figsize=(5.1, 4.1))
        axis = fig.add_subplot(111, projection="3d")
        axis.plot_surface(
            theta_mesh,
            phi_mesh,
            results["surfaces"][state_index],
            cmap="plasma",
            linewidth=0,
            antialiased=True,
        )
        axis.set(xlabel="θ / π", ylabel="ϕ / π", zlabel=f"P({state})", zlim=(0, 1))
        axis.view_init(elev=29, azim=-53)
        paths.append(
            _save(fig, root, f"{surface_target[state]}_probability_surface_{state}.png")
        )

        fig, axis = plt.subplots(figsize=(5.2, 3.2), constrained_layout=True)
        for theta_label, label in (("pi_over_2", "θ=π/2"), ("pi", "θ=π")):
            axis.plot(
                results["phi_cut"] / np.pi,
                results["cut_arrays"][theta_label][:, state_index],
                label=label,
                color=COLORS[state] if theta_label == "pi_over_2" else "#1b9e9a",
            )
        axis.set(xlabel="N00N phase ϕ / π", ylabel=f"P({state})", ylim=(-0.03, 1.03))
        _style_axis(axis)
        axis.legend(frameon=False)
        paths.append(_save(fig, root, f"{cut_target[state]}_phase_cuts_{state}.png"))

    fig, axis = plt.subplots(figsize=(5.2, 3.2), constrained_layout=True)
    axis.plot(results["delay_fs"], results["hom_counts"], color="#d64f8c", linewidth=2)
    axis.set(xlabel="relative delay (fs)", ylabel="coincidence rate (Hz)")
    _style_axis(axis)
    paths.append(_save(fig, root, "T009_hom_delay_model.png"))

    for model, target_bunched, target_split in (
        ("balance", "T010", "T011"),
        ("purity", "T012", "T013"),
    ):
        model_rows = [
            row for row in results["imperfection_rows"] if row["model"] == model
        ]
        parameters = sorted({float(row["parameter"]) for row in model_rows})
        for observable, target, ylabel in (
            ("bunched_probability", target_bunched, "P(20)+P(02)"),
            ("split_probability", target_split, "P(11)"),
        ):
            fig, axis = plt.subplots(figsize=(5.2, 3.2), constrained_layout=True)
            for parameter in parameters:
                rows = [
                    row for row in model_rows if float(row["parameter"]) == parameter
                ]
                axis.plot(
                    [float(row["phi_rad"]) / np.pi for row in rows],
                    [float(row[observable]) for row in rows],
                    label=f"{model[0]}={parameter:g}",
                )
            axis.set(xlabel="ϕ / π", ylabel=ylabel, ylim=(-0.03, 1.03))
            _style_axis(axis)
            axis.legend(frameon=False, ncol=2, fontsize=8)
            paths.append(_save(fig, root, f"{target}_{model}_{observable}.png"))

    fig, axis = plt.subplots(figsize=(5.2, 3.2), constrained_layout=True)
    for device, result in results["spectral_results"].items():
        wavelength = result["signal_wavelength_nm"]
        reflectivity = result["signal_reflectivity"]
        axis.plot(
            wavelength,
            hom_visibility(reflectivity),
            label=f"{device}, integrated V={result['visibility']:.3f}",
        )
    axis.set(
        xlabel="signal wavelength (nm)",
        ylabel="local HOM visibility",
        ylim=(0.45, 1.02),
    )
    _style_axis(axis)
    axis.legend(frameon=False)
    paths.append(_save(fig, root, "T014_spectral_hom_visibility.png"))

    fig, axis = plt.subplots(figsize=(5.2, 3.2), constrained_layout=True)
    axis.plot(
        results["coupler_counts"],
        results["ideal_loss"],
        "o-",
        label="ideal 3.010 dB/coupler",
    )
    axis.plot(
        results["coupler_counts"],
        results["printed_excess_loss"],
        "s-",
        label="including printed 0.25 dB excess",
    )
    axis.set(xlabel="coupler count", ylabel="cumulative loss (dB)")
    _style_axis(axis)
    axis.legend(frameon=False)
    paths.append(_save(fig, root, "T015_coupler_loss.png"))

    fig, axis = plt.subplots(figsize=(5.2, 3.2), constrained_layout=True)
    axis.semilogy(
        results["gaps_um"],
        np.maximum(results["electrode_loss"], 1e-12),
        color="#4e79a7",
    )
    axis.axvline(
        2.0, color="black", linestyle="--", linewidth=1, label="paper device gap"
    )
    axis.set(xlabel="waveguide-electrode gap (µm)", ylabel="loss (dB/mm)")
    _style_axis(axis)
    axis.legend(frameon=False)
    paths.append(_save(fig, root, "T016_electrode_overlap_loss.png"))

    brightness = results["claims"]["brightness"]
    fig, axis = plt.subplots(figsize=(5.2, 3.2), constrained_layout=True)
    names = ["detected/s", "source/s", "brightness\n/s/mW"]
    values = [
        brightness["detected_pairs_per_s"],
        brightness["source_pairs_per_s"],
        brightness["brightness_pairs_per_s_per_mw"],
    ]
    axis.bar(names, values, color=["#59a14f", "#f28e2b", "#4e79a7"])
    axis.set_yscale("log")
    axis.set_ylabel("pairs (log scale)")
    _style_axis(axis)
    paths.append(_save(fig, root, "T017_brightness_arithmetic.png"))

    bandwidth = results["claims"]["bandwidth"]
    fig, axis = plt.subplots(figsize=(5.2, 3.2), constrained_layout=True)
    labels = ["0.441 pulse TBP", "HOM autocorrelation", "paper approx."]
    values = [
        bandwidth["pulse_tbp_0p441_bandwidth_nm"],
        bandwidth["hom_autocorrelation_bandwidth_nm"],
        50.0,
    ]
    axis.bar(labels, values, color=["#4e79a7", "#e15759", "#59a14f"])
    axis.set_ylabel("inferred bandwidth (nm)")
    axis.tick_params(axis="x", rotation=12)
    _style_axis(axis)
    paths.append(_save(fig, root, "T018_bandwidth_conventions.png"))
    return paths
