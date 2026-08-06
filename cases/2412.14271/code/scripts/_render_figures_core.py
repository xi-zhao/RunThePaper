#!/usr/bin/env python3
"""Render frozen analytic and quantum arrays without changing their values."""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


COLORS = {5: "#11cbd7", 13: "#169fe6", 15: "#111bc1"}


def panel_label(ax: plt.Axes, label: str) -> None:
    ax.text(0.03, 0.96, f"({label})", transform=ax.transAxes, ha="left", va="top", fontsize=12)


def fock_bar(ax: plt.Axes, probability: np.ndarray, color: str, label: str, xlim: tuple[int, int]) -> None:
    n = np.arange(probability.size)
    ax.vlines(n, 0, probability, color=color, lw=0.65)
    ax.set(xlim=xlim, ylim=(0, max(float(probability.max()) * 1.08, 1e-4)), xlabel="n", ylabel="P(n)")
    panel_label(ax, label)


def render_fig2(analytic: np.lib.npyio.NpzFile, quantum: np.lib.npyio.NpzFile, output: Path) -> None:
    fig = plt.figure(figsize=(11.0, 5.8), constrained_layout=True)
    grid = fig.add_gridspec(2, 4)
    axes = [fig.add_subplot(grid[0, i]) for i in range(4)] + [fig.add_subplot(grid[1, i]) for i in range(3)]
    coupling = analytic["one_lambda"]
    threshold = float(analytic["one_lambda_c"])
    ax = axes[0]
    ax.plot(coupling, analytic["one_normal_photons"], color="black", lw=1.2)
    ax.plot(coupling, analytic["one_super_photons"], color="#d62728", ls="--", lw=1.2)
    ax.set(xlabel=r"$\lambda/\omega_c$", ylabel=r"$\langle n\rangle/N$", xlim=(0.1, 2), ylim=(-0.05, 5.2))
    panel_label(ax, "a")
    ax = axes[1]
    ax.plot(coupling, analytic["one_super_jx_positive"], color="#1f77b4", ls="--", label=r"$J_x$")
    ax.plot(coupling, analytic["one_super_jz"], color="#d62728", ls="--", label=r"$J_z$")
    ax.plot(coupling, analytic["one_normal_jz"], color="black", lw=1.1)
    ax.set(xlabel=r"$\lambda/\omega_c$", ylabel=r"$\langle J_i\rangle/N$", xlim=(0.1, 2), ylim=(-1.1, 1.1))
    ax.legend(frameon=False, fontsize=8)
    panel_label(ax, "b")
    for index, cutoff in enumerate(quantum["cutoff"]):
        axes[2].plot(quantum["lambda"], quantum["photon_mean"][index] / 5, marker="o", ms=3, label=f"M={cutoff}")
        axes[3].plot(quantum["lambda"], quantum["spin_z_mean"][index], marker="o", ms=3, label=f"M={cutoff}")
    axes[2].set(xlabel=r"$\lambda/\omega_c$", ylabel=r"$\langle n\rangle/N$", xlim=(0.1, 2))
    axes[3].set(xlabel=r"$\lambda/\omega_c$", ylabel=r"$\langle J_z\rangle/N$", xlim=(0.1, 2), ylim=(-1.05, 0.2))
    axes[2].legend(frameon=False, fontsize=7)
    panel_label(axes[2], "c")
    panel_label(axes[3], "d")
    for ax in axes[:4]:
        ax.axvline(threshold, color="#2ca02c", ls="--", lw=1)
    for panel_index, cutoff in enumerate((60, 80, 100)):
        key = f"M{cutoff}_l1p25_fock"
        fock_bar(axes[4 + panel_index], quantum[key], ("#ff8c00", "#ff4b13", "#b9232c")[panel_index], chr(101 + panel_index), (0, cutoff))
    fig.savefig(output / "fig2.png", dpi=220)
    plt.close(fig)


def render_fig3(analytic: np.lib.npyio.NpzFile, quantum: np.lib.npyio.NpzFile, output: Path) -> None:
    fig = plt.figure(figsize=(10.0, 8.2), constrained_layout=True)
    grid = fig.add_gridspec(3, 3, height_ratios=(1, 1, 1.25))
    labels = ["N5_l062", "N5_l079", "N5_l110", "N15_l062", "N15_l079", "N15_l110"]
    panels = ["a", "b", "c", "d", "e", "f"]
    limits = [(0, 100), (0, 100), (0, 100), (0, 100), (0, 180), (0, 240)]
    for index, (label, panel, limit) in enumerate(zip(labels, panels, limits, strict=True)):
        ax = fig.add_subplot(grid[index // 3, index % 3])
        fock_bar(ax, quantum[f"{label}_fock"], ("#ff9700" if index % 3 == 0 else "#ff4b13" if index % 3 == 1 else "#b9232c"), panel, limit)
    ax = fig.add_subplot(grid[2, :])
    coupling = analytic["two_lambda"]
    ax.plot(coupling, analytic["two_coherent_high"], color="black", lw=1.8, label="coherent high (stable)")
    ax.plot(
        coupling,
        analytic["two_squeezed_high"],
        color="#7f3c8d",
        lw=1.4,
        ls=":",
        label="squeezed high (nonlinear unstable)",
    )
    ax.plot(coupling, analytic["two_squeezed_low"], color="black", lw=1.2, ls="-.", label="squeezed low (unstable)")
    for size in (5, 13, 15):
        selected = quantum["branch_N"] == size
        order = np.argsort(quantum["branch_lambda"][selected])
        x = quantum["branch_lambda"][selected][order]
        y = (quantum["branch_photon_mean"][selected] / size)[order]
        ax.plot(x, y, marker={5: "^", 13: "s", 15: "*"}[size], ms=5, lw=1, color=COLORS[size], label=f"N={size}")
    ax.set(xlabel=r"$\lambda/\omega_c$", ylabel=r"$\langle a^\dagger a\rangle/N$", xlim=(0.1, 1.25), ylim=(-0.2, 11))
    ax.legend(frameon=False, fontsize=7, ncol=2)
    panel_label(ax, "g")
    fig.savefig(output / "fig3.png", dpi=220)
    plt.close(fig)


def render_fig4(quantum: np.lib.npyio.NpzFile, output: Path) -> None:
    fig, axes = plt.subplots(2, 3, figsize=(9.0, 6.0), constrained_layout=True)
    axis = quantum["wigner_axis"]
    labels = ["N5_l062", "N5_l079", "N5_l110", "N15_l062", "N15_l079", "N15_l110"]
    for index, (ax, label) in enumerate(zip(axes.flat, labels, strict=True)):
        wigner = quantum[f"{label}_wigner"]
        vmax = np.quantile(np.abs(wigner), 0.995)
        ax.imshow(wigner, origin="lower", extent=(axis[0], axis[-1], axis[0], axis[-1]), cmap="Blues", vmin=0, vmax=vmax, interpolation="bilinear")
        ax.set(xlabel="x", ylabel="p", aspect="equal")
        panel_label(ax, chr(97 + index))
    fig.savefig(output / "fig4.png", dpi=220)
    plt.close(fig)


def scatter_real_spectrum(ax: plt.Axes, coupling: np.ndarray, spectrum: np.ndarray, color: str) -> None:
    for index, value in enumerate(coupling):
        row = spectrum[index]
        valid = np.isfinite(row.real)
        ax.scatter(np.full(np.count_nonzero(valid), value), row.real[valid], s=10, color=color)


def render_supplement(analytic: np.lib.npyio.NpzFile, quantum: np.lib.npyio.NpzFile, parity: np.lib.npyio.NpzFile, output: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(8.0, 3.0), constrained_layout=True)
    scatter_real_spectrum(axes[0], analytic["one_stability_lambda"], analytic["one_normal_eigenvalues"], "#1324cc")
    scatter_real_spectrum(axes[1], analytic["one_stability_lambda"], analytic["one_super_eigenvalues"], "#159437")
    for index, ax in enumerate(axes):
        ax.axhline(0, color="gray", lw=0.7, ls="--")
        ax.set(xlabel=r"$\lambda/\omega_c$", ylabel=r"Re$(\epsilon)$", xlim=(0.1, 1.25))
        panel_label(ax, chr(97 + index))
    fig.savefig(output / "figS1.png", dpi=220)
    plt.close(fig)

    fig, axes = plt.subplots(1, 3, figsize=(11.0, 3.0), constrained_layout=True)
    names = ["normal", "coherent_high", "squeezed_low"]
    colors = ["#1324cc", "#159437", "#e21f26"]
    for index, (ax, name, color) in enumerate(zip(axes, names, colors, strict=True)):
        spectrum_key = "normal_eigenvalues" if name == "normal" else f"audit_{name}_eigenvalues"
        scatter_real_spectrum(ax, analytic["audit_lambda"], analytic[spectrum_key], color)
        ax.axhline(0, color="gray", lw=0.7, ls="--")
        ax.set(xlabel=r"$\lambda/\omega_c$", ylabel=r"Re$(\epsilon)$", xlim=(0.6, 1.25), ylim=(-2.2, 2.2))
        panel_label(ax, chr(97 + index))
    fig.savefig(output / "figS2.png", dpi=220)
    plt.close(fig)

    selected = quantum["branch_N"] == 15
    order = np.argsort(quantum["branch_lambda"][selected])
    x = quantum["branch_lambda"][selected][order]
    fig, ax = plt.subplots(figsize=(5.2, 3.8), constrained_layout=True)
    ax.plot(x, (quantum["branch_photon_mean_4"][selected] / 15)[order], marker="s", color="#55bce7", label="4 trajectories")
    ax.plot(x, (quantum["branch_photon_mean"][selected] / 15)[order], marker="*", color="#111bc1", label="final count")
    ax.plot(analytic["two_lambda"], analytic["two_coherent_high"], color="black", lw=1.5, label="analytic")
    ax.set(xlabel=r"$\lambda/\omega_c$", ylabel=r"$\langle a^\dagger a\rangle/N$", xlim=(0.6, 1.15), ylim=(-0.2, 11))
    ax.legend(frameon=False)
    fig.savefig(output / "figS5.png", dpi=220)
    plt.close(fig)

    fig, axes = plt.subplots(1, 3, figsize=(10.0, 3.0), constrained_layout=True)
    eigenvalues = parity["liouvillian_eigenvalues"]
    axes[0].scatter(eigenvalues.real, eigenvalues.imag, color="#19b5d1", s=24)
    axes[0].axvline(0, color="gray", lw=0.6)
    axes[0].set(xlabel=r"Re$(\epsilon)$", ylabel=r"Im$(\epsilon)$")
    panel_label(axes[0], "a")
    fock_bar(axes[1], parity["fock_initial_15"], "#179bd7", "b", (0, 50))
    fock_bar(axes[2], parity["fock_initial_10"], "#179bd7", "c", (0, 50))
    fig.savefig(output / "figS_parity.png", dpi=220)
    plt.close(fig)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default="outputs/data")
    parser.add_argument("--output-dir", default="outputs/figures")
    args = parser.parse_args()
    data = Path(args.data_dir)
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.size": 9, "axes.linewidth": 0.8, "savefig.facecolor": "white"})
    with (
        np.load(data / "analytic_branches.npz") as analytic,
        np.load(data / "main_quantum.npz") as main_quantum,
        np.load(data / "fig2_quantum.npz") as one_quantum,
        np.load(data / "figS_parity.npz") as parity,
    ):
        render_fig2(analytic, one_quantum, output)
        render_fig3(analytic, main_quantum, output)
        render_fig4(main_quantum, output)
        render_supplement(analytic, main_quantum, parity, output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
