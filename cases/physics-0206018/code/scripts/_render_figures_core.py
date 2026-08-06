#!/usr/bin/env python3
"""Render generated BEM arrays; this stage may later host layout comparison."""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import PchipInterpolator


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="outputs/data/bem_reproduction.npz")
    parser.add_argument("--output-dir", default="outputs/figures")
    args = parser.parse_args()
    data = np.load(args.data)
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)

    plt.rcParams.update({"font.size": 9, "axes.linewidth": 0.8})
    fig, ax = plt.subplots(figsize=(4.0, 3.0), constrained_layout=True)
    ax.plot(data["scan_k"], data["scan_sigma"], color="black", lw=0.9)
    ax.set(xlabel=r"$kR$", ylabel=r"$\sigma/R$", xlim=(20, 25))
    fig.savefig(output / "fig5_cross_section.png", dpi=220)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(5.0, 3.7), constrained_layout=True)
    image = ax.imshow(
        data["near_intensity"],
        origin="lower",
        extent=(data["near_x"][0], data["near_x"][-1], data["near_y"][0], data["near_y"][-1]),
        cmap="gray",
        vmin=0,
        vmax=1,
        interpolation="bilinear",
        aspect="equal",
    )
    for cavity in np.unique(data["mesh_cavity"]):
        selected = data["mesh_cavity"] == cavity
        contour = np.vstack((data["mesh_start"][selected], data["mesh_start"][selected][0]))
        ax.plot(contour[:, 0], contour[:, 1], color="white", alpha=0.45, lw=0.35)
    ax.set(xlabel=r"$x/R$", ylabel=r"$y/R$")
    fig.colorbar(image, ax=ax, label=r"normalized $|\psi|^2$", fraction=0.046)
    fig.savefig(output / "fig6_near_field.png", dpi=220)
    plt.close(fig)

    degrees = (np.rad2deg(data["far_angle"]) + 180) % 360 - 180
    order = np.argsort(degrees)
    fig, ax = plt.subplots(figsize=(4.0, 3.0), constrained_layout=True)
    ax.plot(degrees[order], data["far_intensity"][order], color="black", lw=0.55)
    ax.set(
        xlabel=r"$\theta$",
        ylabel=r"normalized $|\psi(r,\theta)|^2$",
        xlim=(-180, 180),
        ylim=(0, 1.02),
        xticks=[-180, -90, 0, 90, 180],
    )
    fig.savefig(output / "fig7_far_field.png", dpi=220)
    plt.close(fig)

    # RenderContract channel: only canvas, axes, line style, palette, and
    # interpolation are adjusted.  The frozen numerical arrays above are not
    # changed or refit to source pixels.
    smooth_k = np.linspace(data["scan_k"].min(), data["scan_k"].max(), 900)
    smooth_sigma = PchipInterpolator(data["scan_k"], data["scan_sigma"])(smooth_k)
    fig = plt.figure(figsize=(1170 / 150, 1035 / 150), dpi=150)
    ax = fig.add_axes([0.112, 0.17, 0.86, 0.805])
    ax.plot(smooth_k, smooth_sigma, color="black", lw=0.48)
    ax.set(xlim=(20, 25), ylim=(3.5, 7.0), xlabel="kR", ylabel="σ/R")
    ax.tick_params(direction="in", top=True, right=True, width=0.55, labelsize=28)
    ax.minorticks_on()
    ax.xaxis.label.set_size(32)
    ax.yaxis.label.set_size(32)
    for spine in ax.spines.values():
        spine.set_linewidth(0.55)
    fig.savefig(output / "fig5_render_contract.png", dpi=150)
    plt.close(fig)

    fig = plt.figure(figsize=(903 / 150, 985 / 150), dpi=150, facecolor="white")
    ax = fig.add_axes([0.008, 0.095, 0.984, 0.902])
    ax.imshow(
        data["near_intensity"],
        origin="lower",
        cmap="gray",
        vmin=0,
        vmax=1,
        interpolation="bilinear",
        aspect="auto",
    )
    for cavity in np.unique(data["mesh_cavity"]):
        selected = data["mesh_cavity"] == cavity
        contour = np.vstack((data["mesh_start"][selected], data["mesh_start"][selected][0]))
        px = np.interp(contour[:, 0], (data["near_x"][0], data["near_x"][-1]), (0, data["near_intensity"].shape[1] - 1))
        py = np.interp(contour[:, 1], (data["near_y"][0], data["near_y"][-1]), (0, data["near_intensity"].shape[0] - 1))
        ax.plot(px, py, color="black", lw=2.2)
    ax.set_axis_off()
    scale = fig.add_axes([0.002, 0.012, 0.98, 0.068])
    scale.imshow(np.linspace(0, 1, 256)[None, :], cmap="gray", aspect="auto", vmin=0, vmax=1)
    scale.set_axis_off()
    fig.savefig(output / "fig6_render_contract.png", dpi=150)
    plt.close(fig)

    fig = plt.figure(figsize=(1198 / 150, 1008 / 150), dpi=150)
    ax = fig.add_axes([0.11, 0.17, 0.845, 0.825])
    ax.plot(degrees[order], data["far_intensity"][order], color="black", lw=0.42)
    ax.set(xlim=(-180, 180), ylim=(0, 1.02), xlabel="θ", ylabel="|ψ(r,θ)|² (arb. units)")
    ax.set_xticks([-180, -90, 0, 90, 180], ["−180°", "−90°", "0°", "90°", "180°"])
    ax.set_yticks([0], ["0"])
    ax.tick_params(direction="in", top=True, right=True, width=0.5, labelsize=28)
    ax.xaxis.label.set_size(32)
    ax.yaxis.label.set_size(32)
    for spine in ax.spines.values():
        spine.set_linewidth(0.5)
    fig.savefig(output / "fig7_render_contract.png", dpi=150)
    plt.close(fig)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
