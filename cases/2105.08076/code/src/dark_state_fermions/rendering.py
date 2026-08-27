"""Source-independent rendering for all nine numerical targets."""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np


def _read(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _save(fig: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def _style() -> None:
    plt.rcParams.update(
        {
            "font.size": 9,
            "axes.labelsize": 10,
            "axes.titlesize": 10,
            "legend.fontsize": 7,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "figure.facecolor": "white",
        }
    )


def render_t001(data_dir: Path, figure_dir: Path) -> None:
    rows = _read(data_dir / "T001_phase_map.csv")
    p_values = sorted({float(row["p"]) for row in rows})
    gamma_values = sorted({float(row["gamma"]) for row in rows})
    lookup = {
        (float(row["gamma"]), float(row["p"])): float(row["c_eff"]) for row in rows
    }
    matrix = np.asarray(
        [[lookup[(gamma, p)] for gamma in gamma_values] for p in p_values]
    )
    fig, ax = plt.subplots(figsize=(4.0, 3.2))
    image = ax.imshow(
        matrix,
        origin="lower",
        aspect="auto",
        extent=[
            min(gamma_values),
            max(gamma_values),
            1 / max(p_values),
            1 / min(p_values),
        ],
        cmap="turbo",
        interpolation="nearest",
    )
    ax.set_xlabel(r"monitoring rate $\gamma$")
    ax.set_ylabel(r"$1/p$")
    ax.set_title("reduced-scale effective central charge")
    fig.colorbar(image, ax=ax, label=r"$c_{\rm eff}$")
    _save(fig, figure_dir / "T001_main_fig1c.png")


def _render_exponents(
    rows: list[dict[str, str]],
    *,
    key: str,
    theory_key: str,
    ylabel: str,
    filename: str,
    figure_dir: Path,
) -> None:
    grouped: dict[float, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[float(row["gamma"])].append(row)
    fig, ax = plt.subplots(figsize=(4.0, 3.0))
    colors = {0.3: "#2455d6", 1.0: "black", 1.5: "#e53620"}
    for gamma, series in sorted(grouped.items()):
        series.sort(key=lambda row: 1.0 / float(row["p"]))
        ax.plot(
            [1.0 / float(row["p"]) for row in series],
            [float(row[key]) for row in series],
            "x-",
            color=colors.get(gamma),
            label=rf"$\gamma={gamma:g}$",
        )
    theory = [row for row in rows if row[theory_key]]
    theory.sort(key=lambda row: 1.0 / float(row["p"]))
    ax.plot(
        [1.0 / float(row["p"]) for row in theory],
        [float(row[theory_key]) for row in theory],
        color="black",
        linewidth=2.0,
        label="dark-state theory",
    )
    ax.axvline(2 / 3, color="0.5", linestyle="--", linewidth=0.8)
    ax.set_xlabel(r"$1/p$")
    ax.set_ylabel(ylabel)
    ax.legend(frameon=False)
    _save(fig, figure_dir / filename)


def render_t002_t003(data_dir: Path, figure_dir: Path) -> None:
    _render_exponents(
        _read(data_dir / "T002_correlation_exponent.csv"),
        key="direct_a",
        theory_key="theory_a",
        ylabel=r"correlation exponent $a$",
        filename="T002_main_fig1d.png",
        figure_dir=figure_dir,
    )
    _render_exponents(
        _read(data_dir / "T003_entropy_exponent.csv"),
        key="fitted_b",
        theory_key="theory_b",
        ylabel=r"entropy exponent $b$",
        filename="T003_main_fig1e.png",
        figure_dir=figure_dir,
    )


def render_t004_t005(data_dir: Path, figure_dir: Path) -> None:
    colors = {"algebraic": "#9c2be2", "CFT": "#f28e1c", "area_law": "#49bfc1"}
    for filename, y_key, output, log_y in (
        ("T004_entropy_size.csv", "entropy", "T004_main_fig2a.png", True),
        (
            "T005_correlation_size.csv",
            "correlation_positive",
            "T005_main_fig2b.png",
            True,
        ),
    ):
        rows = _read(data_dir / filename)
        grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
        for row in rows:
            grouped[row["physics_phase"]].append(row)
        fig, ax = plt.subplots(figsize=(4.0, 3.0))
        for phase, series in grouped.items():
            series.sort(key=lambda row: int(row["L"]))
            ax.plot(
                [int(row["L"]) for row in series],
                [float(row[y_key]) for row in series],
                "x-",
                color=colors[phase],
                label=phase.replace("_", " "),
            )
        ax.set_xscale("log")
        if log_y:
            ax.set_yscale("log")
        ax.set_xlabel(r"system size $L$")
        ax.set_ylabel(r"$S(L/2,L)$" if y_key == "entropy" else r"$C_+(L/2,L)$")
        ax.legend(frameon=False)
        _save(fig, figure_dir / output)


def render_t006(data_dir: Path, figure_dir: Path) -> None:
    rows = _read(data_dir / "T006_effective_central_charge.csv")
    grouped: dict[tuple[float, int], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[(float(row["gamma"]), int(row["L"]))].append(row)
    fig, ax = plt.subplots(figsize=(4.2, 3.0))
    base = {0.3: "#1455d9", 1.5: "#ef3224", 2.0: "#49bfc1"}
    sizes = sorted({key[1] for key in grouped})
    for (gamma, length), series in sorted(grouped.items()):
        series.sort(key=lambda row: 1.0 / float(row["p"]))
        alpha = 0.25 + 0.75 * (sizes.index(length) + 1) / len(sizes)
        ax.plot(
            [1.0 / float(row["p"]) for row in series],
            [float(row["c_eff"]) for row in series],
            "x-",
            color=base.get(gamma, "0.25"),
            alpha=alpha,
            label=rf"$\gamma={gamma:g}, L={length}$",
        )
    ax.axvline(2 / 3, color="0.5", linestyle="--", linewidth=0.8)
    ax.set_xlabel(r"$1/p$")
    ax.set_ylabel(r"$c_{\rm eff}$")
    ax.legend(frameon=False, ncol=2)
    _save(fig, figure_dir / "T006_main_fig3a.png")


def render_t007(data_dir: Path, figure_dir: Path) -> None:
    rows = _read(data_dir / "T007_algebraic_scaling.csv")
    ell = np.asarray([float(row["ell"]) for row in rows])
    entropy = np.asarray([float(row["entropy"]) for row in rows])
    correlation = np.asarray([float(row["correlation_positive"]) for row in rows])
    theory_s = np.asarray([float(row["theory_entropy"]) for row in rows])
    theory_c = np.asarray([float(row["theory_rescaled_correlation"]) for row in rows])
    fig, ax = plt.subplots(figsize=(4.1, 3.1))
    ax.loglog(ell, entropy, color="#e53620", label=r"$S(l)$")
    ax.loglog(ell, 20 * ell**2 * correlation, color="#2455d6", label=r"$20l^2C_+(l)$")
    ax.loglog(ell, theory_s, "--", color="#e53620", label=r"$l^b$")
    ax.loglog(ell, theory_c, "--", color="#2455d6", label=r"$l^{2-a}$")
    ax.set_xlabel(r"distance $l$")
    ax.set_ylabel("scaled observable")
    ax.legend(frameon=False)
    _save(fig, figure_dir / "T007_main_fig3b.png")


def _render_profiles(
    rows: list[dict[str, str]],
    *,
    y_key: str,
    output: str,
    figure_dir: Path,
) -> None:
    colors = {"algebraic": "#9c2be2", "CFT": "#f28e1c", "area_law": "#49bfc1"}
    grouped: dict[tuple[str, int], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[(row["physics_phase"], int(row["L"]))].append(row)
    sizes = sorted({key[1] for key in grouped})
    fig, ax = plt.subplots(figsize=(4.2, 3.1))
    for (phase, length), series in sorted(grouped.items()):
        series.sort(key=lambda row: float(row["ell"]))
        alpha = 0.25 + 0.75 * (sizes.index(length) + 1) / len(sizes)
        x_key = "chord_length" if y_key == "entropy" else "ell"
        ax.plot(
            [float(row[x_key]) for row in series],
            [float(row[y_key]) for row in series],
            color=colors[phase],
            alpha=alpha,
            label=f"{phase.replace('_', ' ')}, L={length}",
        )
    ax.set_xscale("log")
    if y_key != "entropy":
        ax.set_yscale("log")
    ax.set_xlabel("chord length" if y_key == "entropy" else r"distance $l$")
    ax.set_ylabel(r"$S(l,L)$" if y_key == "entropy" else r"$C_+(l,L)$")
    ax.legend(frameon=False, ncol=2)
    _save(fig, figure_dir / output)


def render_t008_t009(data_dir: Path, figure_dir: Path) -> None:
    _render_profiles(
        _read(data_dir / "T008_subsystem_entropy.csv"),
        y_key="entropy",
        output="T008_supp_fig1a.png",
        figure_dir=figure_dir,
    )
    _render_profiles(
        _read(data_dir / "T009_subsystem_correlation.csv"),
        y_key="correlation_positive",
        output="T009_supp_fig1b.png",
        figure_dir=figure_dir,
    )


def render_all(data_dir: Path, figure_dir: Path) -> None:
    _style()
    render_t001(data_dir, figure_dir)
    render_t002_t003(data_dir, figure_dir)
    render_t004_t005(data_dir, figure_dir)
    render_t006(data_dir, figure_dir)
    render_t007(data_dir, figure_dir)
    render_t008_t009(data_dir, figure_dir)
