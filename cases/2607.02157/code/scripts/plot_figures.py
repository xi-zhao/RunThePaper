"""Render reproduction figures from the scan CSVs.

Independent re-plots (feature-level), not pixel-registered renders: layout and
styling follow the paper loosely so features are comparable panel by panel.

Usage: python scripts/plot_figures.py [--only fig2|figS1|figS2]
"""
from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from runtime_layout import CASE_ROOT  # noqa: E402

WS = CASE_ROOT
DATA = WS / "outputs" / "data"
FIGS = WS / "outputs" / "figures"


def scan_path(name: str) -> Path:
    """Prefer the A100 paper-exact dataset over the local reduced-scale one."""
    exact = DATA / name.replace(".csv", "_paper_exact.csv")
    return exact if exact.exists() else DATA / name


def read_csv(path: Path) -> list[dict]:
    with path.open() as fh:
        return [{k: float(v) if k not in ("model",) else v for k, v in row.items()}
                for row in csv.DictReader(fh)]


def aggregate(rows: list[dict]) -> dict[float, dict[str, tuple[float, float]]]:
    """param -> column -> (mean, sem) over realizations."""
    by_param: dict[float, list[dict]] = defaultdict(list)
    for row in rows:
        by_param[row["param"]].append(row)
    out = {}
    for p, group in sorted(by_param.items()):
        cols = {}
        for key in group[0]:
            if key in ("model", "param", "realization"):
                continue
            vals = np.array([g[key] for g in group])
            cols[key] = (float(vals.mean()), float(vals.std() / max(1, np.sqrt(len(vals) - 1))) if len(vals) > 1 else 0.0)
        out[p] = cols
    return out


def _series(agg: dict, key: str):
    params = np.array(sorted(agg))
    mean = np.array([agg[p][key][0] for p in params])
    sem = np.array([agg[p][key][1] for p in params])
    return params, mean, sem


def _plot_band(ax, x, y, s, color, label, ls="-"):
    ax.plot(x, y, ls, color=color, label=label, lw=1.6)
    if np.any(s > 0):
        ax.fill_between(x, y - s, y + s, color=color, alpha=0.2, lw=0)


def plot_fig2_row(axs, agg, nmse_agg, xlabel, log_x, nmse_scale):
    x, chi_m, s_m = _series(agg, "chi_m_tot")
    _, chi_p, s_p = _series(agg, "chi_p_tot")
    ax = axs[0]
    _plot_band(ax, x, chi_m, s_m, "firebrick", r"$\chi^{\rm m}_{\rm tot}$")
    _plot_band(ax, x, chi_p, s_p, "navy", r"$\chi^{\rm p}_{\rm tot}$", ls="-.")
    # Axis follows the capacities; the scaled NMSE exits the frame at the
    # extremes exactly as in the paper's panels.
    lo = min(chi_p.min(), chi_m.min())
    hi = max(chi_m.max(), chi_p.max())
    pad = 0.08 * (hi - lo)
    ax.set_ylim(lo - pad, hi + 3 * pad)
    if nmse_agg:
        xn, nm, sn = _series(nmse_agg, "nmse_h1")
        ax.plot(xn, nmse_scale * nm, "--", color="forestgreen", lw=1.4,
                label=rf"${nmse_scale:g}\times$NMSE")
    ax.set_ylabel("Holevo capacity")
    ax.legend(fontsize=7)

    ax = axs[1]
    _, wirr, s_w = _series(agg, "beta_W_irr_tot")
    _, chid, s_d = _series(agg, "chi_d_tot")
    _plot_band(ax, x, wirr, s_w, "firebrick", r"$\beta W^{\rm irr}_{\rm tot}$")
    _plot_band(ax, x, chid, s_d, "navy", r"$\chi^{\rm d}_{\rm tot}$", ls="-.")
    ax.fill_between(x, chid, wirr, color="gray", alpha=0.3, lw=0)
    ax.set_ylabel("Generalized Landauer bound")
    ax.legend(fontsize=7)

    ax = axs[2]
    _, C_m, s_cm = _series(agg, "C_m_tot")
    _, C_p, s_cp = _series(agg, "C_p_tot")
    _plot_band(ax, x, C_m, s_cm, "firebrick", r"$\mathcal{C}^{\rm m}_{\rm tot}$")
    _plot_band(ax, x, C_p, s_cp, "navy", r"$\mathcal{C}^{\rm p}_{\rm tot}$", ls="-.")
    ax.set_ylabel("Ensemble coherence")
    ax.legend(fontsize=7, loc="upper left")
    inset = ax.inset_axes([0.62, 0.55, 0.36, 0.42])
    _, I_m, _ = _series(agg, "I_m_tot")
    _, I_p, _ = _series(agg, "I_p_tot")
    inset.plot(x, I_m, color="hotpink", lw=1.1, label=r"$\mathcal{I}^{\rm m}$")
    inset.plot(x, I_p, "--", color="black", lw=1.0, label=r"$\mathcal{I}^{\rm p}$")
    inset.set_title("classical MI", fontsize=6)
    inset.tick_params(labelsize=5)
    if log_x:
        inset.set_xscale("log")

    for ax in axs:
        if log_x:
            ax.set_xscale("log")
        ax.set_xlabel(xlabel)


def make_fig2() -> None:
    rows_specs = [("tfim", "J", True, 100.0), ("cluster", r"$\alpha$", False, 700.0)]
    fig, axes = plt.subplots(2, 3, figsize=(12, 6.4))
    made_any = False
    row_scales = []
    for r, (model, xlabel, log_x, nmse_scale) in enumerate(rows_specs):
        scan = scan_path(f"fig2_{model}_scan.csv")
        if not scan.exists():
            for ax in axes[r]:
                ax.set_visible(False)
            continue
        scale_label = "paper-exact" if scan.name.endswith("_paper_exact.csv") else "reduced-scale"
        row_scales.append(f"{model} {scale_label}")
        agg = aggregate(read_csv(scan))
        nmse_path = scan_path(f"nmse_{model}_scan.csv")
        nmse_agg = aggregate(read_csv(nmse_path)) if nmse_path.exists() else None
        plot_fig2_row(axes[r], agg, nmse_agg, xlabel, log_x, nmse_scale)
        made_any = True
    if made_any:
        fig.suptitle(f"Fig. 2 reproduction (top: disordered TFIM, bottom: cluster model; {'; '.join(row_scales)})",
                     fontsize=9)
        fig.tight_layout()
        fig.savefig(FIGS / "fig2_reproduction.png", dpi=180)
    plt.close(fig)


def make_figS2() -> None:
    rows_specs = [("tfim", "J", True), ("cluster", r"$\alpha$", False)]
    fig, axes = plt.subplots(2, 3, figsize=(12, 6.4))
    made_any = False
    for r, (model, xlabel, log_x) in enumerate(rows_specs):
        scan = scan_path(f"fig2_{model}_scan.csv")
        if not scan.exists():
            for ax in axes[r]:
                ax.set_visible(False)
            continue
        agg = aggregate(read_csv(scan))
        x, chi_m, _ = _series(agg, "chi_m_tot")
        ax = axes[r][0]
        ax.plot(x, chi_m, color="firebrick", lw=1.6, label=r"$\tau=0$")
        for tau, style in ((1, "-."), (2, "--")):
            _, v, _ = _series(agg, f"chi_m_tau{tau}_tot")
            ax.plot(x, v, style, lw=1.3, label=rf"$\tau={tau}$")
        ax.set_ylabel(r"$\chi^{\rm m}_{\rm tot}(\tau)$")
        ax.legend(fontsize=7)

        ax = axes[r][1]
        _, chi_p, _ = _series(agg, "chi_p_tot")
        ax.plot(x, chi_p, color="firebrick", lw=1.6, label=r"$h=1$")
        for h, style in ((2, "-."), (3, "--")):
            _, v, _ = _series(agg, f"chi_p_h{h}_tot")
            ax.plot(x, v, style, lw=1.3, label=rf"$h={h}$")
        ax.set_ylabel(r"$\chi^{\rm p}_{\rm tot}(h)$")
        ax.legend(fontsize=7)

        ax = axes[r][2]
        nmse_path = scan_path(f"nmse_{model}_scan.csv")
        if nmse_path.exists():
            nmse_agg = aggregate(read_csv(nmse_path))
            for h, style in ((1, "-"), (2, "-."), (3, "--")):
                xn, v, _ = _series(nmse_agg, f"nmse_h{h}")
                ax.plot(xn, v, style, lw=1.3, label=rf"$h={h}$")
            ax.set_yscale("log")
            ax.set_ylabel("NMSE")
            ax.legend(fontsize=7)
        for ax in axes[r]:
            if log_x:
                ax.set_xscale("log")
            ax.set_xlabel(xlabel)
        made_any = True
    if made_any:
        fig.suptitle(
            "Fig. S2 reproduction (paper-scale capacities and full-Pauli NMSE)",
            fontsize=9,
        )
        fig.tight_layout()
        fig.savefig(FIGS / "figS2_reproduction.png", dpi=180)
    plt.close(fig)


def make_figS1() -> None:
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.6))
    g = read_csv(DATA / "figS1a_g_factor.csv")
    spec = read_csv(DATA / "figS1a_mg_spectrum.csv")
    ax = axes[0]
    ax.plot([r["omega"] for r in g], [r["G"] for r in g], color="firebrick", lw=1.6, label=r"$G(\omega)$")
    om = np.array([r["omega"] for r in spec])
    F = np.array([r["power"] for r in spec])
    mask = (om > 0) & (om <= 3.0)
    ax.plot(om[mask], 50 * F[mask], color="navy", lw=1.2, label=r"$F(\omega)\times 50$")
    ax.set_xlabel(r"$\omega$")
    ax.legend(fontsize=8)

    ax = axes[1]
    with (DATA / "figS1b_tfim_spectrum.csv").open() as fh:
        rows = list(csv.reader(fh))
    Js = np.array([float(r[0]) for r in rows[1:]])
    levels = np.array([[float(v) for v in r[1:]] for r in rows[1:]])
    for k in range(levels.shape[1]):
        ax.plot(Js, levels[:, k], color="black", lw=0.4, alpha=0.5)
    ax.set_xscale("log")
    ax.set_xlabel("J")
    ax.set_ylabel("Normalized Energy")

    ax = axes[2]
    with (DATA / "figS1c_cluster_spectrum.csv").open() as fh:
        rows = list(csv.reader(fh))
    alphas = np.array([float(r[0]) for r in rows[1:]])
    levels = np.array([[float(v) for v in r[1:]] for r in rows[1:]])
    for k in range(levels.shape[1]):
        ax.plot(alphas, levels[:, k], color="black", lw=0.4, alpha=0.5)
    ax.set_xlabel(r"$\alpha$")
    ax.set_ylabel("Energy")

    fig.suptitle(
        "Fig. S1 exploratory reproduction "
        "(reduced statistical ensembles; spectral features only)",
        fontsize=9,
    )
    fig.tight_layout()
    fig.savefig(FIGS / "figS1_reproduction.png", dpi=180)
    plt.close(fig)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", choices=["fig2", "figS1", "figS2"], default=None)
    args = parser.parse_args()
    FIGS.mkdir(parents=True, exist_ok=True)
    if args.only in (None, "fig2"):
        make_fig2()
    if args.only in (None, "figS1"):
        make_figS1()
    if args.only in (None, "figS2"):
        make_figS2()
    print("figures written to", FIGS)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
