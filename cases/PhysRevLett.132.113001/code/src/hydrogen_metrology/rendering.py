"""Source-independent renderers for the generated numerical observables."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np

COLORS = ("#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00")


def _style() -> None:
    plt.rcParams.update(
        {
            "font.size": 8.5,
            "axes.linewidth": 0.8,
            "xtick.direction": "in",
            "ytick.direction": "in",
            "savefig.dpi": 180,
        }
    )


def _save(fig: plt.Figure, path: Path) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path.as_posix()


def render_stark(rows: list[dict[str, Any]], n: int, path: Path) -> str:
    _style()
    fig, ax = plt.subplots(figsize=(3.45, 2.35))
    names = sorted({str(row["branch"]) for row in rows if row["n"] == n})
    for index, name in enumerate(names):
        selected = [row for row in rows if row["n"] == n and row["branch"] == name]
        ax.plot(
            [row["field_v_per_cm"] for row in selected],
            [row["shift_khz"] for row in selected],
            color=COLORS[index],
            lw=1.25,
            label=name.replace("_", " "),
        )
    ax.set(xlabel=r"Electric field (V cm$^{-1}$)", ylabel="Shift (kHz)")
    ax.legend(frameon=False, fontsize=6.4, ncol=2)
    ax.set_title(f"$n={n}$, $k=0$, $|m_l|=1$")
    return _save(fig, path)


def render_spectrum(rows: list[dict[str, float]], path: Path) -> str:
    _style()
    fig, ax = plt.subplots(figsize=(3.45, 2.2))
    ax.plot(
        [row["frequency_mhz"] for row in rows],
        [row["intensity"] for row in rows],
        color="#111111",
        lw=1.35,
    )
    ax.set(xlabel="Detuning (MHz)", ylabel="Calculated signal (norm.)")
    ax.set_ylim(bottom=0)
    return _save(fig, path)


def render_literature(rows: list[dict[str, Any]], path: Path) -> str:
    _style()
    fig, ax = plt.subplots(figsize=(3.45, 2.8))
    for index, row in enumerate(rows):
        ax.errorbar(
            row["x"],
            row["y"],
            xerr=row["x_sigma"],
            yerr=row["y_sigma"],
            fmt="o",
            ms=4,
            capsize=1.5,
            color=COLORS[index % len(COLORS)],
            label=row["label"],
        )
    ax.axhline(0, color="0.65", lw=0.7)
    ax.axvline(0, color="0.65", lw=0.7)
    ax.set(
        xlabel=r"$(r_p-r_{p,18})/\sigma_{r_p,18}$", ylabel=r"$(R-R_{18})/\sigma_{R,18}$"
    )
    ax.legend(frameon=False, fontsize=5.5, loc="best")
    return _save(fig, path)


def render_regression(
    x: np.ndarray,
    center: np.ndarray,
    band: np.ndarray,
    *,
    xlabel: str,
    path: Path,
) -> str:
    _style()
    fig, ax = plt.subplots(figsize=(3.45, 2.2))
    ax.fill_between(x, center - band, center + band, color="#56B4E9", alpha=0.28)
    ax.plot(x, center, color="#0072B2", lw=1.4)
    ax.axhline(0, color="0.6", lw=0.7)
    ax.set(xlabel=xlabel, ylabel="Ionization-frequency offset (kHz)")
    return _save(fig, path)


def render_uncertainties(rows: list[dict[str, Any]], path: Path) -> str:
    _style()
    fig, ax = plt.subplots(figsize=(4.0, 2.65))
    names = [str(row["name"]).replace("_", " ") for row in rows]
    y = np.arange(len(rows))
    stat = [float(row["stat_khz"]) for row in rows]
    syst = [float(row["syst_khz"]) for row in rows]
    ax.barh(y, stat, color="#0072B2", label="statistical")
    ax.barh(y, syst, left=stat, color="#D55E00", label="systematic")
    ax.set(yticks=y, yticklabels=names, xlabel="Uncertainty contribution (kHz)")
    ax.invert_yaxis()
    ax.legend(frameon=False, fontsize=7)
    return _save(fig, path)


def render_frequency_table(rows: list[dict[str, Any]], path: Path) -> str:
    _style()
    base = 3_289_841_960_200.0
    fig, ax = plt.subplots(figsize=(4.0, 2.45))
    y = np.arange(len(rows))
    values = np.asarray([float(row["frequency_khz"]) for row in rows]) - base
    errors = [float(row["sigma_khz"]) for row in rows]
    ax.errorbar(values, y, xerr=errors, fmt="o", color="#0072B2", capsize=2)
    ax.set(yticks=y, yticklabels=[row["method"] for row in rows])
    ax.set_xlabel(rf"$cR_\infty$ - {base:.0f} kHz")
    ax.invert_yaxis()
    return _save(fig, path)


def render_field_free(rows: list[dict[str, Any]], path: Path) -> str:
    _style()
    fig, axes = plt.subplots(1, 2, figsize=(6.2, 2.35))
    for ax, n in zip(axes, (20, 24), strict=True):
        selected = [row for row in rows if row["n"] == n]
        for j_value in sorted({float(row["j"]) for row in selected}):
            subset = [row for row in selected if row["j"] == j_value]
            ax.scatter(
                [row["l"] for row in subset],
                [row["dirac_shift_khz"] for row in subset],
                s=7,
                label=f"j={j_value:g}",
            )
        ax.set(xlabel="$l$", title=f"$n={n}$")
    axes[0].set_ylabel("Leading Dirac shift (kHz)")
    axes[1].legend(frameon=False, fontsize=6, ncol=2)
    return _save(fig, path)


def render_stark_table(rows: list[dict[str, Any]], path: Path) -> str:
    _style()
    fig, axes = plt.subplots(1, 2, figsize=(6.2, 2.35), sharey=False)
    for ax, n in zip(axes, (20, 24), strict=True):
        selected = [row for row in rows if row["n"] == n]
        names = sorted({str(row["branch"]) for row in selected})
        for index, name in enumerate(names):
            subset = [row for row in selected if row["branch"] == name]
            ax.plot(
                [row["field_v_per_cm"] for row in subset],
                [row["predicted_shift_khz"] for row in subset],
                "o-",
                color=COLORS[index],
                ms=3,
                lw=1,
                label=name,
            )
        ax.set(xlabel=r"Field (V cm$^{-1}$)", title=f"$n={n}$")
    axes[0].set_ylabel("Predicted shift (kHz)")
    axes[1].legend(frameon=False, fontsize=5.4)
    return _save(fig, path)


def render_all(results: dict[str, Any], workspace: Path) -> list[str]:
    root = workspace / "outputs" / "figures" / "feature"
    regression = results["regression_arrays"]
    paths = [
        render_stark(results["stark_rows"], 20, root / "T001_fig1_n20_stark.png"),
        render_stark(results["stark_rows"], 24, root / "T002_fig1_n24_stark.png"),
        render_spectrum(results["spectrum_rows"], root / "T003_fig3_theory.png"),
        render_literature(results["literature_rows"], root / "T004_fig4_metrology.png"),
        render_regression(
            regression["field"],
            regression["field_trend_khz"],
            regression["field_band_khz"],
            xlabel=r"Electric field (V cm$^{-1}$)",
            path=root / "T005_fig5b_stark_model.png",
        ),
        render_regression(
            regression["doppler"],
            regression["doppler_trend_khz"],
            regression["doppler_band_khz"],
            xlabel="Doppler shift (MHz)",
            path=root / "T006_fig5c_doppler_model.png",
        ),
        render_uncertainties(
            results["uncertainty_rows"], root / "T007_table1_uncertainties.png"
        ),
        render_frequency_table(
            results["rydberg_rows"], root / "T008_table2_rydberg.png"
        ),
        render_field_free(
            results["field_free_rows"], root / "T009_supp_field_free.png"
        ),
        render_stark_table(
            results["stark_table_rows"], root / "T010_supp_stark_table.png"
        ),
    ]
    return paths
