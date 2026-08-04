#!/usr/bin/env python3
"""Render OBC dynamic targets only from frozen independent numerical arrays."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


WORKSPACE = Path(__file__).resolve().parents[2]
DATA_DIR = WORKSPACE / "outputs" / "data"
FIGURE_DIR = WORKSPACE / "outputs" / "figures"


def save(figure: plt.Figure, stem: str) -> None:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    for suffix in ("png",):
        figure.savefig(FIGURE_DIR / f"{stem}.{suffix}", dpi=220, bbox_inches="tight")
    plt.close(figure)


def adjacent_phase(states: np.ndarray, *, zero_to_twopi: bool = False) -> np.ndarray:
    values = np.angle(states[:, 1:] * states[:, :-1].conj())
    return np.mod(values, 2.0 * np.pi) if zero_to_twopi else values


def render_fig3_de() -> None:
    data = np.load(DATA_DIR / "fig3_dynamic_scan.npz")
    figure, axes = plt.subplots(1, 2, figsize=(10.2, 3.7))
    kappa = data["kappa"]
    measured_frequency = data["frequency_branch"]
    measured_q = np.mod(data["wavevector_branch"], np.pi)
    # Each independent seed chooses one of the two PH partners.  Canonicalize
    # to the lower-q member solely for continuous rendering; no data changes.
    q = np.minimum(measured_q, np.pi - measured_q)
    q[~np.isfinite(measured_frequency)] = np.nan
    q_partner = np.pi - q
    frequency = -np.abs(measured_frequency)
    partner_frequency = np.abs(measured_frequency)
    dispersion = -2.0 * np.cos(q)
    axes[0].plot(kappa, frequency, "o-", color="#4c72b0", ms=3, label=r"$\langle\omega\rangle_j$")
    axes[0].plot(kappa, partner_frequency, "o-", color="#4c72b0", ms=3)
    axes[0].plot(kappa, dispersion, "--", color="#6baed6", lw=1.5, label=r"$-2J\cos\langle q\rangle_j$")
    twin = axes[0].twinx()
    twin.plot(kappa, q, color="#55a868", lw=1.8, label=r"$\langle q\rangle_j$")
    twin.plot(kappa, q_partner, color="#55a868", lw=1.8)
    axes[0].set(xlim=(0, 3), ylim=(-2.15, 2.15), xlabel=r"$\kappa/J$", ylabel=r"$\langle\omega\rangle_j/J$")
    twin.set(ylim=(0, np.pi), ylabel=r"$\langle q\rangle_j$")
    twin.set_yticks([0, np.pi / 4, np.pi / 2, 3 * np.pi / 4, np.pi])
    twin.set_yticklabels(["0", r"$\pi/4$", r"$\pi/2$", r"$3\pi/4$", r"$\pi$"])
    axes[0].set_title("(d) frequency–wavevector locking", loc="left")
    axes[0].grid(alpha=0.28)
    lines = axes[0].lines[:2] + [axes[0].lines[2], twin.lines[0]]
    axes[0].legend(lines, [line.get_label() for line in lines], fontsize=7, loc="lower left")

    axes[1].plot(kappa, data["density_rate_average"], color="#4c72b0", lw=2)
    axes[1].axvline(float(data["density_rate_profile_kappa_actual"]), color="gray", ls="--", lw=1)
    axes[1].set(xlim=(0, 3), xlabel=r"$\kappa/J$", ylabel=r"$\langle|\partial_t r_j^2|\rangle_{j,t}/J$")
    axes[1].set_title("(e) edge-amplitude dynamics", loc="left")
    axes[1].grid(alpha=0.28)
    inset = axes[1].inset_axes([0.48, 0.48, 0.48, 0.44])
    inset.plot(
        np.arange(1, data["density_rate_profile_kappa21"].size + 1),
        data["density_rate_profile_kappa21"],
        color="#4c72b0",
    )
    inset.set(xlabel="site $j$", ylabel="rate")
    inset.tick_params(labelsize=7)
    inset.grid(alpha=0.2)
    figure.suptitle("Main Fig. 3(d,e) — independent long-time Eq. (2) dynamics", fontsize=11)
    save(figure, "main_fig3_de_independent")


def render_fig4() -> None:
    data = np.load(DATA_DIR / "representative_dynamics.npz")
    figure = plt.figure(figsize=(12.0, 9.0))
    grid = figure.add_gridspec(3, 4, height_ratios=(1, 1, 0.72), hspace=0.54, wspace=0.30)
    labels = (
        ("phase_iv_periodic", "(b) Phase IV", r"$\gamma=.3,\ \kappa=2.2$"),
        ("phase_iii_edge", "(c) Phase III", r"$\gamma=.4,\ \kappa=1.25$"),
    )
    for row, (key, panel, parameters) in enumerate(labels):
        times = data[f"{key}_time"]
        states = data[f"{key}_state"]
        selection = times <= 50.0
        amplitude_axis = figure.add_subplot(grid[row, 0:2])
        phase_axis = figure.add_subplot(grid[row, 2:4])
        amplitude = np.abs(states[selection])
        phase = adjacent_phase(states[selection])
        image_amp = amplitude_axis.imshow(
            amplitude,
            origin="lower",
            aspect="auto",
            extent=(1, states.shape[1], 0, times[selection][-1]),
            cmap="viridis",
        )
        image_phase = phase_axis.imshow(
            phase,
            origin="lower",
            aspect="auto",
            extent=(1, states.shape[1] - 1, 0, times[selection][-1]),
            cmap="coolwarm",
            vmin=-np.pi / 2,
            vmax=np.pi / 2,
        )
        amplitude_axis.set(title=f"{panel}: amplitude ({parameters})", ylabel=r"$Jt$")
        phase_axis.set(title="adjacent phase difference")
        if row == 1:
            amplitude_axis.set_xlabel("site $j$")
            phase_axis.set_xlabel("site $j$")
        figure.colorbar(image_amp, ax=amplitude_axis, fraction=0.025, pad=0.02)
        figure.colorbar(image_phase, ax=phase_axis, fraction=0.025, pad=0.02)

    profile_axis = figure.add_subplot(grid[2, 0:2])
    phase_time_axis = figure.add_subplot(grid[2, 2:4])
    for key, color, short in (("phase_iv_periodic", "#4c72b0", "b"), ("phase_iii_edge", "#55a868", "c")):
        states = data[f"{key}_state"]
        rate = np.mean(np.abs(data[f"{key}_density_rate"]), axis=0)
        profile_axis.plot(np.arange(1, rate.size + 1), rate, color=color, lw=1.8, label=short)
        site = min(74, states.shape[1] - 1)
        phase_time_axis.plot(
            data[f"{key}_time"],
            np.angle(states[:, site]),
            color=color,
            lw=1.2,
            label=short,
        )
    profile_axis.set(xlabel="site $j$", ylabel=r"$\langle|\partial_t r_j^2|\rangle_t/J$", title="(d) independently found attractors")
    profile_axis.legend()
    profile_axis.grid(alpha=0.25)
    phase_time_axis.set(xlim=(0, 50), xlabel=r"$Jt$", ylabel=r"$\phi_{75}(t)$", title="(e) site-75 phase")
    phase_time_axis.set_yticks([-np.pi, 0, np.pi])
    phase_time_axis.set_yticklabels([r"$-\pi$", "0", r"$\pi$"])
    phase_time_axis.legend()
    phase_time_axis.grid(alpha=0.25)
    figure.suptitle(
        "Main Fig. 4(b–e) — formula-driven dynamics (five-state hierarchy remains partial)",
        fontsize=11,
        y=0.985,
    )
    save(figure, "main_fig4_bcde_independent")


def render_fig5() -> None:
    lce = np.load(DATA_DIR / "fig5_lyapunov_sweep.npz")
    portraits = np.load(DATA_DIR / "phase_portraits_and_edge_cases.npz")
    figure, axes = plt.subplots(1, 2, figsize=(11.2, 4.5))
    colors = ("#55a868", "#dd8452", "#4c72b0", "#cc78bc")
    for index in range(4):
        axes[0].plot(
            lce["gamma"],
            lce["exponents"][:, index],
            "o-",
            ms=3.2,
            lw=1.4,
            color=colors[index],
            label=fr"$\lambda_{index + 1}$",
        )
    axes[0].axhline(0, color="black", ls="--", lw=1)
    axes[0].set(xlabel=r"$\gamma/J$", ylabel=r"$\lambda_i/J$", title="(a) four largest Benettin LCEs")
    axes[0].grid(alpha=0.25)
    axes[0].legend(ncol=2, fontsize=8)

    portrait_colors = {
        "phase_i": "#e78ac3",
        "phase_ii": "#66c2a5",
        "phase_iii": "#8da0cb",
        "phase_iv": "#fc8d62",
    }
    for label, color in portrait_colors.items():
        axes[1].plot(
            portraits[f"portrait_{label}_phase_first"],
            portraits[f"portrait_{label}_phase_second"],
            color=color,
            lw=0.45,
            alpha=0.75,
            label=label.replace("_", " ").title(),
        )
    axes[1].set(xlim=(0, 2 * np.pi), ylim=(0, 2 * np.pi), xlabel=r"$\phi_i(t)$", ylabel=r"$\phi_j(t)$", title="(b) edge phase portraits")
    ticks = [0, np.pi / 2, np.pi, 3 * np.pi / 2, 2 * np.pi]
    labels = ["0", r"$\pi/2$", r"$\pi$", r"$3\pi/2$", r"$2\pi$"]
    axes[1].set_xticks(ticks, labels)
    axes[1].set_yticks(ticks, labels)
    axes[1].legend(fontsize=8)
    axes[1].grid(alpha=0.18)
    figure.suptitle("End Matter Fig. 5 — independent tangent-flow and trajectory reproduction", fontsize=11)
    save(figure, "main_fig5_lyapunov_portraits_independent")


def render_fig6() -> None:
    data = np.load(DATA_DIR / "representative_dynamics.npz")
    figure = plt.figure(figsize=(12.1, 5.7))
    grid = figure.add_gridspec(3, 4, width_ratios=(1.25, 1.25, 1, 1), hspace=0.12, wspace=0.38)
    state = data["phase_iv_periodic_state"]
    time = data["phase_iv_periodic_time"]
    sites = np.arange(1, state.shape[1] + 1)
    ph_state = ((-1.0) ** sites)[None, :] * state.conj()
    original_phase = adjacent_phase(state, zero_to_twopi=True)
    conjugate_phase = adjacent_phase(ph_state, zero_to_twopi=True)
    difference = np.abs(data["ph_restoration_difference"])
    panels = (
        (original_phase, time, r"(a.i) $\delta\phi_j(t)$", "twilight", 0, 2 * np.pi),
        (conjugate_phase, time, r"(a.ii) $\mathcal{PH}[\delta\phi_j(t)]$", "twilight", 0, 2 * np.pi),
        (difference, time[: difference.shape[0]], r"(a.iii) $|\delta\alpha_j^{T/2}|$", "viridis", 0, np.percentile(difference, 99)),
    )
    for row, (values, times, title, cmap, vmin, vmax) in enumerate(panels):
        axis = figure.add_subplot(grid[row, 0:2])
        image = axis.imshow(
            values,
            origin="lower",
            aspect="auto",
            extent=(1, values.shape[1], times[0], times[-1]),
            cmap=cmap,
            vmin=vmin,
            vmax=vmax,
        )
        axis.set(ylabel=r"$Jt$", title=title)
        if row == 2:
            axis.set_xlabel("site $j$")
        figure.colorbar(image, ax=axis, fraction=0.026, pad=0.02)

    left = figure.add_subplot(grid[:, 2])
    right = figure.add_subplot(grid[:, 3])
    left.plot(data["chaos_phase50_t"], data["chaos_phase50_delayed"], color="#66c2a5", lw=0.25, alpha=0.55)
    right.plot(data["chaos_ph_phase50_t"], data["chaos_ph_phase50_delayed"], color="#66c2a5", lw=0.25, alpha=0.55)
    for axis, title in ((left, "(b.i) chaotic attractor"), (right, r"(b.ii) $\mathcal{PH}$ attractor")):
        axis.set(xlim=(0, 2 * np.pi), ylim=(0, 2 * np.pi), xlabel=r"$\phi_{50}(t)$", ylabel=r"$\phi_{50}(t+14/J)$", title=title)
        axis.set_xticks([0, np.pi, 2 * np.pi], ["0", r"$\pi$", r"$2\pi$"])
        axis.set_yticks([0, np.pi, 2 * np.pi], ["0", r"$\pi$", r"$2\pi$"])
    figure.suptitle("End Matter Fig. 6 — PH restoration and chaotic-attractor invariance", fontsize=11)
    save(figure, "main_fig6_ph_symmetry_independent")


def render_supplement() -> None:
    dynamics = np.load(DATA_DIR / "representative_dynamics.npz")
    edges = np.load(DATA_DIR / "phase_portraits_and_edge_cases.npz")
    chaotic = dynamics["phase_iv_chaotic_state"]
    chaotic_time = dynamics["phase_iv_chaotic_time"]
    phase = adjacent_phase(chaotic, zero_to_twopi=True)
    selection = (chaotic_time >= 250) & (chaotic_time <= 500)
    figure, axis = plt.subplots(figsize=(10.7, 3.4))
    image = axis.imshow(
        phase[selection],
        origin="lower",
        aspect="auto",
        extent=(1, phase.shape[1], 250, 500),
        cmap="twilight",
        vmin=0,
        vmax=2 * np.pi,
    )
    axis.set(xlabel="site $j$", ylabel=r"$Jt$", title="Supplemental Fig. S2(a) — chaotic adjacent-phase domains")
    colorbar = figure.colorbar(image, ax=axis, pad=0.02)
    colorbar.set_ticks([0, np.pi, 2 * np.pi], labels=["0", r"$\pi$", r"$2\pi$"])
    save(figure, "supp_fig_s2a_chaotic_domains_independent")

    cases = (
        ("s3a_phase_ii", "(a) Phase II"),
        ("s3b_phase_iii", "(b) Phase III"),
        ("s3c_chaotic_edge", "(c) Phase IV"),
        ("s3d_hn_ep", "(d) near HN EP"),
    )
    figure, axes = plt.subplots(1, 4, figsize=(12.0, 4.0), sharey=True)
    for axis, (key, title) in zip(axes, cases, strict=True):
        state = edges[f"{key}_state"]
        time = edges[f"{key}_time"]
        phase = adjacent_phase(state, zero_to_twopi=True)
        image = axis.imshow(
            phase[:, :60],
            origin="lower",
            aspect="auto",
            extent=(1, 60, time[0], time[-1]),
            cmap="twilight",
            vmin=0,
            vmax=2 * np.pi,
        )
        axis.set(xlabel="site $j$", title=title)
    axes[0].set_ylabel(r"$Jt$")
    colorbar = figure.colorbar(image, ax=axes, orientation="horizontal", fraction=0.07, pad=0.15)
    colorbar.set_ticks([0, np.pi, 2 * np.pi], labels=["0", r"$\pi$", r"$2\pi$"])
    figure.suptitle("Supplemental Fig. S3 — independent edge-dynamics cases", fontsize=11)
    save(figure, "supp_fig_s3_edge_behaviors_independent")


def main() -> None:
    render_fig3_de()
    render_fig4()
    render_fig5()
    render_fig6()
    render_supplement()


if __name__ == "__main__":
    main()
