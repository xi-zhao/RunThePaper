"""Rendering lane for independently generated QFIM data."""

from __future__ import annotations

from pathlib import Path
from typing import Mapping

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np


def _sphere_coordinates(theta: np.ndarray, phi: np.ndarray) -> tuple[np.ndarray, ...]:
    theta_grid, phi_grid = np.meshgrid(theta, phi, indexing="ij")
    return (
        np.sin(theta_grid) * np.cos(phi_grid),
        np.sin(theta_grid) * np.sin(phi_grid),
        np.cos(theta_grid),
    )


def render_husimi(
    path: Path,
    theta: np.ndarray,
    phi: np.ndarray,
    probability: np.ndarray,
) -> None:
    x, y, z = _sphere_coordinates(theta, phi)
    normalized = probability / max(float(probability.max()), np.finfo(float).eps)
    colors = plt.get_cmap("turbo")(normalized)
    fig = plt.figure(figsize=(4.2, 3.8), constrained_layout=True)
    axis = fig.add_subplot(111, projection="3d")
    axis.plot_surface(
        x,
        y,
        z,
        facecolors=colors,
        linewidth=0,
        antialiased=False,
        shade=False,
        rcount=min(81, theta.size),
        ccount=min(161, phi.size),
    )
    axis.set_xlabel(r"$\langle J_x\rangle$", labelpad=-2)
    axis.set_ylabel(r"$\langle J_y\rangle$", labelpad=-2)
    axis.set_zlabel(r"$\langle J_z\rangle$", labelpad=-2)
    axis.set_box_aspect((1, 1, 1))
    axis.set_axis_off()
    scalar = plt.cm.ScalarMappable(
        cmap="turbo", norm=plt.Normalize(0, probability.max())
    )
    scalar.set_array([])
    fig.colorbar(
        scalar,
        ax=axis,
        fraction=0.04,
        pad=0.01,
        label=r"$|\langle\theta,\phi|\psi(t)\rangle|^2$",
    )
    fig.savefig(path, dpi=220, transparent=False)
    plt.close(fig)


def render_oat_spectrum(path: Path, data: Mapping[str, np.ndarray]) -> None:
    fig, axis = plt.subplots(figsize=(5.2, 3.6), constrained_layout=True)
    x = data["normalized_time"]
    axis.plot(x, data["lambda_1"], color="#e66101", lw=2.1, label=r"$\lambda_1$")
    axis.plot(
        x, data["lambda_2"], color="#1f78b4", lw=2.0, ls="--", label=r"$\lambda_2$"
    )
    axis.plot(
        x, data["lambda_3"], color="#d73027", lw=1.8, ls=":", label=r"$\lambda_3$"
    )
    axis.plot(
        x,
        data["analytic_qfi"],
        color="black",
        lw=1.4,
        ls="-.",
        label=r"$\mathcal{F}_{\rm OAT}$",
    )
    axis.axhline(20, color="0.75", lw=0.8)
    axis.set(
        xlim=(0, 1),
        ylim=(0, 410),
        xlabel=r"Time $t/[\pi/(2\chi)]$",
        ylabel=r"$\lambda_i$",
    )
    axis.grid(alpha=0.22, ls=":")
    axis.legend(ncol=2, frameon=False, fontsize=9)
    fig.savefig(path, dpi=220)
    plt.close(fig)


def render_generator_path(path: Path, data: Mapping[str, np.ndarray]) -> None:
    u = np.linspace(0, 2 * np.pi, 41)
    v = np.linspace(0, np.pi, 21)
    x = np.outer(np.cos(u), np.sin(v))
    y = np.outer(np.sin(u), np.sin(v))
    z = np.outer(np.ones_like(u), np.cos(v))
    fig = plt.figure(figsize=(4.4, 4.0), constrained_layout=True)
    axis = fig.add_subplot(111, projection="3d")
    axis.plot_wireframe(x, y, z, color="0.72", linewidth=0.35, rstride=4, cstride=4)
    scatter = axis.scatter(
        data["coefficient_Jx"],
        data["coefficient_Jy"],
        data["coefficient_Jz"],
        c=data["lambda_max"],
        cmap="turbo",
        s=11,
        depthshade=False,
    )
    axis.plot(
        data["coefficient_Jx"],
        data["coefficient_Jy"],
        data["coefficient_Jz"],
        color="0.2",
        lw=0.7,
        alpha=0.55,
    )
    axis.set_box_aspect((1, 1, 1))
    axis.set(xlim=(-1.05, 1.05), ylim=(-1.05, 1.05), zlim=(-1.05, 1.05))
    axis.set_xlabel(r"$J_x$")
    axis.set_ylabel(r"$J_y$")
    axis.set_zlabel(r"$J_z$")
    fig.colorbar(scatter, ax=axis, fraction=0.04, pad=0.04, label=r"$\lambda_{\max}$")
    fig.savefig(path, dpi=220)
    plt.close(fig)


def render_su4_spectrum(path: Path, data: Mapping[str, np.ndarray]) -> None:
    colors = (
        "#e66101",
        "#1f78b4",
        "#e6ab02",
        "#6a3d9a",
        "#33a02c",
        "#b15928",
        "#a6cee3",
        "#cab2d6",
    )
    styles = ("-", "--", "-.", ":", "-", "--", "-.", ":")
    fig, axis = plt.subplots(figsize=(5.5, 3.8), constrained_layout=True)
    x = data["normalized_time"]
    for index in range(8):
        axis.plot(
            x,
            data[f"lambda_{index + 1}"],
            color=colors[index],
            ls=styles[index],
            lw=1.7,
            label=rf"$\lambda_{{{index + 1}}}$",
        )
    axis.plot(
        x, data["subgroup_max"], color="black", lw=1.5, ls="--", label="J/K/E max"
    )
    axis.axhline(20, color="0.75", lw=0.8)
    axis.set(
        xlim=(0, 1),
        ylim=(0, 155),
        xlabel=r"Time $t/[\pi/(2\chi)]$",
        ylabel=r"$\lambda_i$",
    )
    axis.grid(alpha=0.22, ls=":")
    axis.legend(ncol=3, frameon=False, fontsize=8, loc="upper center")
    fig.savefig(path, dpi=220)
    plt.close(fig)


def render_su4_coefficients(
    path: Path,
    normalized_time: np.ndarray,
    coefficients: np.ndarray,
    names: tuple[str, ...],
) -> None:
    fig, axis = plt.subplots(figsize=(6.0, 4.5), constrained_layout=True)
    image = axis.imshow(
        coefficients.T,
        origin="upper",
        aspect="auto",
        interpolation="nearest",
        extent=(normalized_time[0], normalized_time[-1], len(names) - 0.5, -0.5),
        cmap="viridis",
        vmin=-1,
        vmax=1,
    )
    axis.set_yticks(np.arange(len(names)))
    axis.set_yticklabels(names)
    axis.set_xlabel(r"Time $t/[\pi/(2\chi)]$")
    axis.set_ylabel(r"Basis operator $G_\mu$")
    fig.colorbar(image, ax=axis, label=r"Coefficient $\mathcal{O}^\mu$")
    fig.savefig(path, dpi=220)
    plt.close(fig)
