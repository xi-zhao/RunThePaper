"""Render reduced-scale figures from independently generated records only."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.axes_grid1.inset_locator import inset_axes


BLUE_RED = plt.get_cmap("coolwarm")


def _select(records: Iterable[dict[str, Any]], **criteria: Any) -> list[dict[str, Any]]:
    return [
        row
        for row in records
        if all(row.get(key) == value for key, value in criteria.items())
    ]


def _group(records: Iterable[dict[str, Any]], key: str) -> dict[Any, list[dict[str, Any]]]:
    grouped: dict[Any, list[dict[str, Any]]] = defaultdict(list)
    for row in records:
        grouped[row[key]].append(row)
    return dict(grouped)


def _ordered(records: Iterable[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    return sorted(records, key=lambda row: float(row[key]))


def _style_axis(axis: plt.Axes) -> None:
    axis.tick_params(direction="in", top=True, right=True, labelsize=8)
    for spine in axis.spines.values():
        spine.set_linewidth(0.7)


def _label_panel(axis: plt.Axes, label: str) -> None:
    axis.text(-0.17, 1.03, label, transform=axis.transAxes, fontsize=14, fontweight="bold")


def _finish(figure: plt.Figure, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=250, facecolor="white", bbox_inches="tight")
    plt.close(figure)
    return path


def _render_figure1(
    output: Path,
    parameters: dict[str, Any],
    datasets: dict[str, list[dict[str, Any]]],
) -> Path:
    entropy = datasets["half_entropy.csv"]
    fits = datasets["cft_fits.csv"]
    qsd_half = _select(entropy, protocol="qsd")
    qsd_fits = _select(fits, protocol="qsd")
    qsdc_fits = _select(fits, protocol="qsdc")
    maximum_length = max(int(value) for value in parameters["regular_sizes"])
    figure, axes = plt.subplots(1, 3, figsize=(11.6, 3.45))

    grouped_gamma = _group(qsd_half, "gamma")
    gammas = sorted(grouped_gamma)
    for index, gamma in enumerate(gammas):
        rows = _ordered(grouped_gamma[gamma], "length")
        axes[0].plot(
            [row["length"] for row in rows],
            [row["mean_entropy"] for row in rows],
            "o-",
            ms=2.8,
            lw=1.0,
            color=BLUE_RED(index / max(1, len(gammas) - 1)),
            label=f"{gamma:g}",
        )
    axes[0].set_xscale("log")
    axes[0].set_xlabel("L")
    axes[0].set_ylabel(r"$\overline{S}_{\rm vN}(L/2,L)$")
    axes[0].legend(title=r"$\gamma$", ncol=2, fontsize=5.7, title_fontsize=7, frameon=False)
    inset = inset_axes(axes[0], width="39%", height="40%", loc="upper left")
    for index, gamma in enumerate(gammas[:8]):
        rows = _ordered(grouped_gamma[gamma], "length")
        inset.plot(
            [row["length"] for row in rows],
            [row["mean_entropy"] for row in rows],
            "o-",
            ms=1.7,
            lw=0.7,
            color=BLUE_RED(index / max(1, len(gammas) - 1)),
        )
    inset.tick_params(labelsize=5, direction="in")
    _label_panel(axes[0], "c)")

    qsd_rows = _ordered(_select(qsd_fits, length=maximum_length), "gamma")
    qsdc_rows = _ordered(qsdc_fits, "gamma")
    for rows, label, color, marker in (
        (qsd_rows, "QSD", "#6A3D9A", "o"),
        (qsdc_rows, "QSDc", "#1F78B4", "x"),
    ):
        positive = [row for row in rows if row["gamma"] > 0 and row["central_charge"] > 0]
        axes[1].plot(
            [row["gamma"] for row in positive],
            [row["central_charge"] for row in positive],
            marker + "-",
            ms=3,
            lw=1.1,
            color=color,
            label=label,
        )
    axes[1].set_xscale("log")
    axes[1].set_yscale("log")
    axes[1].set_xlabel(r"$\gamma$")
    axes[1].set_ylabel(r"$c(\gamma)$")
    axes[1].legend(frameon=False, fontsize=7)
    central_inset = inset_axes(axes[1], width="42%", height="38%", loc="lower left")
    for rows, color, marker in ((qsd_rows, "#6A3D9A", "o"), (qsdc_rows, "#1F78B4", "x")):
        central_inset.plot(
            [row["gamma"] for row in rows if row["gamma"] > 0],
            [max(float(row["central_charge"]), 0.0) for row in rows if row["gamma"] > 0],
            marker + "-",
            ms=2,
            lw=0.7,
            color=color,
        )
    central_inset.tick_params(labelsize=5, direction="in")
    _label_panel(axes[1], "d)")

    for rows, label, color, marker in (
        (qsd_rows, "QSD", "#6A3D9A", "o"),
        (qsdc_rows, "QSDc", "#1F78B4", "x"),
    ):
        rows = [row for row in rows if row["gamma"] > 0]
        axes[2].plot(
            [row["gamma"] for row in rows],
            [row["residual_entropy"] for row in rows],
            marker + "-",
            ms=3,
            lw=1.1,
            color=color,
            label=label,
        )
    axes[2].axhline(0.0, color="0.3", lw=0.7, ls="--")
    axes[2].set_xlabel(r"$\gamma$")
    axes[2].set_ylabel(r"$s_0(\gamma)$")
    residual_inset = inset_axes(axes[2], width="43%", height="41%", loc="lower right")
    for rows, color in ((qsd_rows, "#6A3D9A"), (qsdc_rows, "#1F78B4")):
        rows = [row for row in rows if row["gamma"] > 0 and abs(row["residual_entropy"]) > 1e-8]
        residual_inset.loglog(
            [row["gamma"] for row in rows],
            [abs(row["residual_entropy"]) for row in rows],
            "o-",
            ms=2,
            lw=0.7,
            color=color,
        )
    residual_inset.tick_params(labelsize=5, direction="in")
    _label_panel(axes[2], "e)")
    for axis in axes:
        _style_axis(axis)
    figure.suptitle("Reduced-scale independent QSD reproduction", fontsize=9)
    figure.tight_layout()
    return _finish(figure, output)


def _render_figure2(
    output: Path,
    parameters: dict[str, Any],
    datasets: dict[str, list[dict[str, Any]]],
) -> Path:
    entropy = _select(datasets["regular_entropy.csv"], protocol="qsd")
    half = _select(datasets["half_entropy.csv"], protocol="qsd")
    fits = _select(datasets["cft_fits.csv"], protocol="qsd")
    maximum_length = max(int(value) for value in parameters["regular_sizes"])
    gamma_c = float(parameters["bkt_gamma_c"])
    alpha = float(parameters["bkt_alpha"])
    figure = plt.figure(figsize=(11.7, 5.2))
    grid = figure.add_gridspec(2, 2, width_ratios=(1.05, 1.35), hspace=0.28, wspace=0.30)
    axis_a = figure.add_subplot(grid[:, 0])
    axis_b = figure.add_subplot(grid[0, 1])
    axis_c = figure.add_subplot(grid[1, 1])

    groups = _group(_select(entropy, length=maximum_length), "gamma")
    gammas = sorted(groups)
    for index, gamma in enumerate(gammas):
        rows = _ordered(groups[gamma], "chord_coordinate")
        axis_a.plot(
            [row["chord_coordinate"] for row in rows],
            [row["mean_entropy"] for row in rows],
            "o-",
            ms=2.5,
            lw=0.9,
            color=BLUE_RED(index / max(1, len(gammas) - 1)),
            label=f"{gamma:g}",
        )
    axis_a.set_xscale("log")
    axis_a.set_xlabel(r"$\sin(\pi l/L)$")
    axis_a.set_ylabel(r"$\overline{S}_{\rm vN}(l,L)$")
    axis_a.legend(title=r"$\gamma$", ncol=2, fontsize=5.5, title_fontsize=7, frameon=False)
    inset_a = inset_axes(axis_a, width="43%", height="36%", loc="upper left")
    for index, gamma in enumerate(gammas[7:]):
        rows = _ordered(groups[gamma], "chord_coordinate")
        inset_a.plot(
            [row["chord_coordinate"] for row in rows],
            [row["mean_entropy"] for row in rows],
            "o-",
            ms=1.5,
            lw=0.6,
            color=BLUE_RED((index + 7) / max(1, len(gammas) - 1)),
        )
    inset_a.set_xscale("log")
    inset_a.tick_params(labelsize=5, direction="in")
    _label_panel(axis_a, "a)")

    half_groups = _group(half, "length")
    for length, rows in sorted(half_groups.items()):
        rows = _ordered(rows, "gamma")
        gamma_values = np.asarray([row["gamma"] for row in rows])
        entropy_values = np.asarray([row["mean_entropy"] for row in rows])
        critical_entropy = float(np.interp(gamma_c, gamma_values, entropy_values))
        axis_b.plot(
            (gamma_values - gamma_c) * np.log(float(length)) ** 2,
            entropy_values - critical_entropy,
            "o-",
            ms=2.8,
            lw=0.8,
            label=f"L={length}",
        )
    axis_b.set_xlabel(r"$(\gamma-\gamma_c)\log(L)^2$")
    axis_b.set_ylabel(r"$\overline{S}(\gamma)-\overline{S}(\gamma_c)$")
    axis_b.legend(frameon=False, fontsize=6, ncol=2)
    inset_b = inset_axes(axis_b, width="39%", height="42%", loc="upper right")
    for length, rows in sorted(half_groups.items()):
        rows = _ordered(rows, "gamma")
        inset_b.plot(
            [row["gamma"] for row in rows],
            [row["mean_entropy"] for row in rows],
            "o-",
            ms=1.5,
            lw=0.5,
        )
    inset_b.tick_params(labelsize=5, direction="in")
    _label_panel(axis_b, "b)")

    for length, rows in sorted(_group(fits, "length").items()):
        rows = [row for row in _ordered(rows, "gamma") if row["gamma"] > gamma_c]
        x_values = [
            np.log(float(length)) - alpha / np.sqrt(float(row["gamma"]) - gamma_c)
            for row in rows
        ]
        g_length = 1.0 / (1.0 + 1.0 / (2.0 * np.log(float(length)) - 4.37))
        y_values = [
            g_length * float(row["gamma"]) * max(float(row["central_charge"]), 0.0)
            for row in rows
        ]
        axis_c.plot(x_values, y_values, "o", ms=3, label=f"L={length}")
    axis_c.axhline(0.0, color="0.2", lw=0.6, ls=":")
    axis_c.axhline(2.0, color="0.2", lw=0.6, ls=":")
    axis_c.set_xlabel(r"$\log(L)-\alpha/\sqrt{\gamma-\gamma_c}$")
    axis_c.set_ylabel(r"$g(L)\,\gamma c(\gamma)$")
    _label_panel(axis_c, "c)")
    for axis in (axis_a, axis_b, axis_c):
        _style_axis(axis)
    return _finish(figure, output)


def _render_figure3(
    output: Path,
    parameters: dict[str, Any],
    datasets: dict[str, list[dict[str, Any]]],
) -> Path:
    mutual = _select(datasets["fixed_mutual_information.csv"], protocol="qsd")
    cross = datasets["cross_ratio_mutual_information.csv"]
    correlations = datasets["spatial_correlations.csv"]
    maximum_length = max(int(value) for value in parameters["regular_sizes"])
    figure, axes = plt.subplots(1, 4, figsize=(13.2, 3.45), gridspec_kw={"width_ratios": [1.0, 0.9, 0.9, 1.35]})

    for length, rows in sorted(_group(mutual, "length").items()):
        rows = _ordered(rows, "gamma")
        axes[0].plot(
            [row["gamma"] for row in rows],
            [row["mean_mutual_information"] for row in rows],
            "o-",
            ms=2.6,
            lw=0.8,
            label=f"{length}",
        )
    axes[0].set_xlabel(r"$\gamma$")
    axes[0].set_ylabel(r"$\mathcal{I}(r_{AB}=L/2)$")
    axes[0].legend(title="L", fontsize=5.8, title_fontsize=7, frameon=False)
    inset = inset_axes(axes[0], width="43%", height="38%", loc="upper right")
    for _, rows in sorted(_group(mutual, "length").items()):
        rows = _ordered(rows, "gamma")
        inset.semilogy(
            [row["gamma"] for row in rows],
            [max(float(row["mean_mutual_information"]), 1e-12) for row in rows],
            "o-",
            ms=1.3,
            lw=0.5,
        )
    inset.tick_params(labelsize=5, direction="in")
    _label_panel(axes[0], "a)")

    for axis, gamma, label in ((axes[1], 0.25, "b)"), (axes[2], 6.0, "c)")):
        rows = _ordered(_select(cross, gamma=gamma), "eta")
        axis.loglog(
            [row["eta"] for row in rows],
            [max(float(row["mean_mutual_information"]), 1e-15) for row in rows],
            "o",
            ms=2.7,
            color="#5B7BE5" if gamma < 1 else "#E76F51",
        )
        axis.set_xlabel(r"$\eta$")
        axis.set_ylabel(r"$\mathcal{I}(\eta)$")
        axis.text(0.08, 0.90, rf"$\gamma={gamma:g}$", transform=axis.transAxes, fontsize=9)
        _label_panel(axis, label)

    gamma_values = [0.05, 0.15, 0.2, 0.35, 0.5, 1.0, 2.0, 4.0]
    for index, gamma in enumerate(gamma_values):
        rows = _ordered(
            _select(correlations, length=maximum_length, gamma=gamma),
            "scaled_distance",
        )
        axes[3].loglog(
            [row["scaled_distance"] for row in rows],
            [row["mean_correlation"] for row in rows],
            "o-",
            ms=2.1,
            lw=0.8,
            color=BLUE_RED(index / (len(gamma_values) - 1)),
            label=f"{gamma:g}",
        )
    axes[3].set_xlabel(r"$L/\pi\sin(\pi l/L)$")
    axes[3].set_ylabel(r"$\overline{C}(l,0)$")
    axes[3].legend(title=r"$\gamma$", ncol=2, fontsize=5.3, title_fontsize=6.5, frameon=False)
    inset_d = inset_axes(axes[3], width="43%", height="38%", loc="upper right")
    for length, rows in sorted(
        _group(_select(correlations, gamma=0.25), "length").items()
    ):
        rows = _ordered(rows, "scaled_distance")
        inset_d.loglog(
            [row["scaled_distance"] for row in rows],
            [row["mean_correlation"] for row in rows],
            "-",
            lw=0.7,
            label=f"{length}",
        )
    inset_d.tick_params(labelsize=5, direction="in")
    _label_panel(axes[3], "d)")
    for axis in axes:
        _style_axis(axis)
    figure.tight_layout()
    return _finish(figure, output)


def _render_appendix_main(
    output: Path,
    datasets: dict[str, list[dict[str, Any]]],
) -> Path:
    time_records = datasets["time_entropy.csv"]
    qj_entropy = datasets["qj_entropy.csv"]
    qj_fits = datasets["qj_cft_fits.csv"]
    qj_mutual = datasets["qj_mutual_information.csv"]
    qsdc_mutual = _select(datasets["fixed_mutual_information.csv"], protocol="qsdc")
    figure = plt.figure(figsize=(10.8, 7.1))
    grid = figure.add_gridspec(2, 2, hspace=0.34, wspace=0.30)
    axes = [figure.add_subplot(grid[row, column]) for row in range(2) for column in range(2)]

    for index, (gamma, rows) in enumerate(sorted(_group(time_records, "gamma").items())):
        rows = _ordered(rows, "time")
        axes[0].plot(
            [row["time"] for row in rows],
            [row["mean_entropy"] for row in rows],
            lw=0.9,
            color=BLUE_RED(index / max(1, len(_group(time_records, "gamma")) - 1)),
            label=f"{gamma:g}",
        )
    axes[0].set_xlabel("t")
    axes[0].set_ylabel(r"$\overline{S}_{\rm vN}(L/2,t)$")
    axes[0].legend(title=r"$\gamma$", ncol=2, fontsize=5.5, title_fontsize=7, frameon=False)
    _label_panel(axes[0], "a)")

    groups = _group(qj_entropy, "gamma")
    for index, gamma in enumerate(sorted(groups)):
        rows = _ordered(groups[gamma], "chord_coordinate")
        axes[1].plot(
            [row["chord_coordinate"] for row in rows],
            [row["mean_entropy"] for row in rows],
            "o-",
            ms=2.2,
            lw=0.8,
            color=BLUE_RED(index / max(1, len(groups) - 1)),
            label=f"{gamma:g}",
        )
    axes[1].set_xscale("log")
    axes[1].set_xlabel(r"$\sin(\pi l/L)$")
    axes[1].set_ylabel(r"$\overline{S}_{\rm vN}^{\rm QJ}(l,L)$")
    axes[1].legend(title=r"$\gamma$", ncol=2, fontsize=5.4, title_fontsize=7, frameon=False)
    inset_b = inset_axes(axes[1], width="38%", height="40%", loc="upper left")
    rows = _ordered(qj_fits, "gamma")
    inset_b.loglog(
        [row["gamma"] for row in rows],
        [max(float(row["central_charge"]), 1e-8) for row in rows],
        "ko-",
        ms=1.8,
        lw=0.6,
    )
    inset_b.tick_params(labelsize=5, direction="in")
    _label_panel(axes[1], "b)")

    rows = _ordered(qj_mutual, "gamma")
    axes[2].plot(
        [row["gamma"] for row in rows],
        [row["mean_mutual_information"] for row in rows],
        "o-",
        ms=3,
        lw=1.0,
        color="#8DD36F",
    )
    axes[2].axhline(0.0, color="0.2", ls="--", lw=0.7)
    axes[2].set_xlabel(r"$\gamma$")
    axes[2].set_ylabel(r"$\mathcal{I}_{\rm QJ}(r_{AB}=L/2)$")
    _label_panel(axes[2], "c)")

    rows = _ordered(qsdc_mutual, "gamma")
    axes[3].loglog(
        [row["gamma"] for row in rows],
        [max(float(row["mean_mutual_information"]), 1e-12) for row in rows],
        "o-",
        ms=3,
        lw=1.0,
        color="#FB9A99",
    )
    axes[3].set_xlabel(r"$\gamma$")
    axes[3].set_ylabel(r"$\mathcal{I}_{\rm QSDc}(r_{AB}=L/2)$")
    _label_panel(axes[3], "d)")
    for axis in axes:
        _style_axis(axis)
    return _finish(figure, output)


def _render_random_hopping(
    output: Path,
    datasets: dict[str, list[dict[str, Any]]],
) -> Path:
    records = datasets["random_hopping_entropy.csv"]
    figure, axis = plt.subplots(figsize=(5.2, 4.2))
    groups = _group(records, "gamma")
    for index, gamma in enumerate(sorted(groups)):
        rows = _ordered(groups[gamma], "chord_coordinate")
        axis.plot(
            [row["chord_coordinate"] for row in rows],
            [row["mean_entropy"] for row in rows],
            "o-",
            ms=3,
            lw=1.0,
            color=BLUE_RED(index / max(1, len(groups) - 1)),
            label=f"{gamma:g}",
        )
    axis.set_xscale("log")
    axis.set_xlabel(r"$\sin(\pi l/L)$")
    axis.set_ylabel(r"$\overline{S}_{\rm vN}(l,L)$")
    axis.legend(title=r"$\gamma$", frameon=False, fontsize=7)
    _style_axis(axis)
    figure.tight_layout()
    return _finish(figure, output)


def _render_autocorrelation(
    output: Path,
    datasets: dict[str, list[dict[str, Any]]],
) -> Path:
    autocorrelation = datasets["autocorrelation.csv"]
    density = datasets["density_identity.csv"]
    figure, axes = plt.subplots(1, 2, figsize=(9.4, 3.6))
    groups = _group(autocorrelation, "gamma")
    for index, gamma in enumerate(sorted(groups)):
        rows = [row for row in _ordered(groups[gamma], "tau") if row["tau"] > 0]
        axes[0].loglog(
            [row["tau"] for row in rows],
            [row["mean_correlation"] for row in rows],
            "o-",
            ms=2.4,
            lw=0.9,
            color=BLUE_RED(index / max(1, len(groups) - 1)),
            label=f"{gamma:g}",
        )
    axes[0].set_xlabel(r"$\tau$")
    axes[0].set_ylabel(r"$\overline{C}(0,\tau)$")
    axes[0].legend(title=r"$\gamma$", frameon=False, fontsize=7)
    _label_panel(axes[0], "a)")

    rows = _ordered(density, "scaled_distance")
    axes[1].loglog(
        [row["scaled_distance"] for row in rows],
        [max(float(row["independent_density_difference"]), 1e-8) for row in rows],
        "o",
        ms=3,
        label="independent density difference",
    )
    axes[1].loglog(
        [row["scaled_distance"] for row in rows],
        [row["direct_fock_correlation"] for row in rows],
        "-",
        lw=1.1,
        color="#F28E2B",
        label="direct $|D_{i,i+l}|^2$",
    )
    axes[1].set_xlabel(r"$L/\pi\sin(\pi l/L)$")
    axes[1].set_ylabel("connected density signal")
    axes[1].legend(frameon=False, fontsize=6.5)
    _label_panel(axes[1], "b)")
    for axis in axes:
        _style_axis(axis)
    figure.tight_layout()
    return _finish(figure, output)


def _render_statistics(
    output: Path,
    datasets: dict[str, list[dict[str, Any]]],
) -> Path:
    records = datasets["entropy_histogram_samples.csv"]
    gammas = [0.25, 2.0, 6.0]
    protocols = ["qsd", "qsdc"]
    figure, axes = plt.subplots(2, 3, figsize=(8.5, 4.7))
    for row_index, protocol in enumerate(protocols):
        for column_index, gamma in enumerate(gammas):
            axis = axes[row_index, column_index]
            values = [
                record["half_entropy"]
                for record in records
                if record["protocol"] == protocol and record["gamma"] == gamma
            ]
            axis.hist(
                values,
                bins=24,
                density=True,
                color="#1F77B4" if protocol == "qsd" else "#FF7F0E",
                alpha=0.95,
            )
            if row_index == 0:
                axis.set_title(rf"$\gamma={gamma:g}$", fontsize=9)
            if column_index == 0:
                axis.set_ylabel(protocol.upper())
            if row_index == 1:
                axis.set_xlabel(r"$\overline{S}_{\rm vN}(L/2,L)$")
            _style_axis(axis)
    figure.tight_layout()
    return _finish(figure, output)


def render_all(
    *,
    workspace: Path,
    parameters: dict[str, Any],
    datasets: dict[str, list[dict[str, Any]]],
) -> list[Path]:
    output = workspace / "outputs" / "figures"
    return [
        _render_figure1(output / "main_fig1_numeric_cde.png", parameters, datasets),
        _render_figure2(output / "main_fig2_abc.png", parameters, datasets),
        _render_figure3(output / "main_fig3_abcd.png", parameters, datasets),
        _render_appendix_main(output / "supp_figure_qj_abcd.png", datasets),
        _render_autocorrelation(output / "supp_autocorrelation_ab.png", datasets),
        _render_random_hopping(output / "supp_random_hopping.png", datasets),
        _render_statistics(output / "supp_entropy_statistics.png", datasets),
    ]
