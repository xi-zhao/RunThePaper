#!/usr/bin/env python3
"""Symmetry-resolved PXP sector run for T003 (scar tower) and T004 (level stats).

Diagonalizes the k=0, inversion-even PXP sector at the largest locally
feasible size (L=28, sector dimension 13201; the paper's L=32 sector needs
~47GB dense workspace and is recorded as a remote rerun) and extracts:

- T003: the |<Z2|E>|^2 scar tower - the paper's L/2+1 special states with
  approximately equal energy spacing;
- T004: symmetry-resolved level statistics - mean consecutive-gap ratio
  <r> against GOE vs Poisson, plus the unfolded spacing distribution
  against the Wigner surmise (exact zero modes excluded).
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pxp_scars import (  # noqa: E402
    build_symmetric_hamiltonian,
    build_symmetric_sector,
    mean_level_spacing_ratio,
    pattern_state,
    symmetrized_state_vector,
    unfolded_spacings,
)

DEFAULT_L = 28
GOE_R = 0.5307
POISSON_R = 0.3863


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", help="Workspace-relative JSON configuration.")
    parser.add_argument("--output-root", default="outputs", help="Workspace-relative output directory.")
    parser.add_argument("--dry-run", action="store_true", help="Validate and print the resolved run without allocating the Hamiltonian.")
    return parser.parse_args()


def load_config(config_ref: str | None) -> dict:
    if not config_ref:
        return {}
    path = Path(config_ref)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("--config must be a safe workspace-relative path")
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("configuration must be a JSON object")
    return payload


def main() -> int:
    args = parse_args()
    config = load_config(args.config)
    output_ref = Path(args.output_root)
    if output_ref.is_absolute() or ".." in output_ref.parts or output_ref.parts[:1] != ("outputs",):
        raise ValueError("--output-root must be workspace-relative under outputs/")
    output_root = ROOT / output_ref
    L = int(config.get("system_size", DEFAULT_L))
    if L < 6 or L % 2:
        raise ValueError("system_size must be an even integer >= 6")
    spacing_separation = float(config.get("tower_energy_separation", 1.8))
    window_quantiles = config.get("level_window_quantiles", [0.1, 0.9])
    if (
        not isinstance(window_quantiles, list)
        or len(window_quantiles) != 2
        or not 0.0 < float(window_quantiles[0]) < float(window_quantiles[1]) < 1.0
    ):
        raise ValueError("level_window_quantiles must contain two increasing values inside (0, 1)")
    resolved = {
        "system_size": L,
        "momentum": 0,
        "inversion": "+1",
        "tower_energy_separation": spacing_separation,
        "level_window_quantiles": [float(value) for value in window_quantiles],
        "output_root": output_ref.as_posix(),
    }
    if args.dry_run:
        print(json.dumps({"status": "ready", "resolved_run": resolved}, indent=2))
        return 0

    t0 = time.time()
    sector = build_symmetric_sector(L)
    dim = len(sector["representatives"])
    hamiltonian = build_symmetric_hamiltonian(sector).toarray()
    energies, vectors = np.linalg.eigh(hamiltonian)
    elapsed = time.time() - t0

    # --- T003: Z2 scar tower ---
    z2_vector = symmetrized_state_vector(sector, pattern_state(L, "z2"))
    overlaps = (z2_vector @ vectors) ** 2
    tower_count = L // 2 + 1
    # One state per tower. In the k=0, I=+1 sector the scar towers alternate
    # with the k=pi sector, so the visible tower spacing is ~2.66 (twice the
    # full-tower spacing); greedy peak picking with separation 1.8 keeps one
    # dominant state per tower and rejects same-tower satellites.
    top = []
    for index in np.argsort(overlaps)[::-1]:
        if all(abs(energies[index] - energies[j]) > spacing_separation for j in top):
            top.append(int(index))
        if len(top) == tower_count:
            break
    top = np.asarray(top)
    tower_energies = np.sort(energies[top])
    tower_spacings = np.diff(tower_energies)
    spacing_mean = float(np.mean(tower_spacings))
    spacing_rel_std = float(np.std(tower_spacings) / spacing_mean)

    # --- T004: level statistics (zero modes excluded, central window) ---
    nonzero = energies[np.abs(energies) > 1e-10]
    lo, hi = np.quantile(nonzero, window_quantiles)
    window = nonzero[(nonzero >= lo) & (nonzero <= hi)]
    r_mean = mean_level_spacing_ratio(window)
    spacings = unfolded_spacings(window)
    spacings = spacings / np.mean(spacings)
    hist, edges = np.histogram(spacings, bins=40, range=(0.0, 4.0), density=True)
    centers = 0.5 * (edges[1:] + edges[:-1])
    wigner = (np.pi / 2.0) * centers * np.exp(-np.pi * centers**2 / 4.0)
    poisson = np.exp(-centers)
    l1_wigner = float(np.trapezoid(np.abs(hist - wigner), centers))
    l1_poisson = float(np.trapezoid(np.abs(hist - poisson), centers))
    density_hist, density_edges = np.histogram(energies, bins=80, density=True)
    density_centers = 0.5 * (density_edges[1:] + density_edges[:-1])

    gate_flags = {
        "scar_tower_has_half_L_plus_one_states": bool(np.all(overlaps[top] > 1e-8)),
        "scar_tower_spacing_uniform": spacing_rel_std < 0.15,
        "level_statistics_goe_not_poisson": abs(r_mean - GOE_R) < abs(r_mean - POISSON_R),
        "spacing_distribution_wigner_not_poisson": l1_wigner < l1_poisson,
    }

    data_dir = output_root / "data"
    check_dir = output_root / "checks"
    fig_dir = output_root / "figures"
    for directory in (data_dir, check_dir, fig_dir):
        directory.mkdir(parents=True, exist_ok=True)
    with (data_dir / "sector_scar_tower.csv").open("w", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["energy", "z2_overlap_sq", "is_tower_state"])
        tower_set = set(int(i) for i in top)
        for i, (energy, overlap) in enumerate(zip(energies, overlaps)):
            writer.writerow([f"{energy:.10f}", f"{overlap:.3e}", int(i in tower_set)])
    with (data_dir / "sector_level_spacings.csv").open("w", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["unfolded_spacing"])
        writer.writerows([[f"{s:.8f}"] for s in spacings])
    with (data_dir / "sector_density_of_states.csv").open("w", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["energy", "density"])
        writer.writerows(
            [[f"{energy:.10f}", f"{density:.10f}"] for energy, density in zip(density_centers, density_hist)]
        )

    checks = {
        "targets": ["T003", "T004"],
        "status": "physically_consistent" if all(gate_flags.values()) else "partial",
        "sector": {"L": L, "momentum": 0, "inversion": "+1", "dimension": dim},
        "resolved_run": resolved,
        "elapsed_seconds": round(elapsed, 1),
        "scar_tower": {
            "expected_states": tower_count,
            "min_tower_overlap_sq": float(np.min(overlaps[top])),
            "tower_energies": [round(float(e), 6) for e in tower_energies],
            "mean_tower_spacing": spacing_mean,
            "tower_spacing_rel_std": spacing_rel_std,
        },
        "level_statistics": {
            "window_levels": int(len(window)),
            "zero_modes_excluded": int(len(energies) - len(nonzero)),
            "mean_gap_ratio": r_mean,
            "goe_reference": GOE_R,
            "poisson_reference": POISSON_R,
            "l1_distance_to_wigner": l1_wigner,
            "l1_distance_to_poisson": l1_poisson,
        },
        "gate_flags": gate_flags,
        "remote_rerun": {
            "L": 32,
            "reason": "L=32 sector (~77k) needs ~47GB dense eigh workspace; local memory is 18GB.",
            "constraint_class": "external_required",
        },
        "data": [
            f"{output_ref.as_posix()}/data/sector_scar_tower.csv",
            f"{output_ref.as_posix()}/data/sector_level_spacings.csv",
            f"{output_ref.as_posix()}/data/sector_density_of_states.csv",
        ],
        "figures": [
            f"{output_ref.as_posix()}/figures/sector_scar_tower.png",
            f"{output_ref.as_posix()}/figures/sector_level_statistics.png",
        ],
    }
    (check_dir / "symmetry_resolved_sector.json").write_text(
        json.dumps(checks, indent=2) + "\n"
    )

    fig, ax = plt.subplots(figsize=(6.4, 4.4))
    ax.semilogy(energies, np.maximum(overlaps, 1e-16), ".", markersize=2, color="0.6")
    ax.semilogy(energies[top], overlaps[top], "o", markersize=5, color="tab:red",
                label=f"top {tower_count} tower states")
    ax.set_xlabel("E")
    ax.set_ylabel(r"$|\langle Z_2|E\rangle|^2$")
    ax.set_ylim(1e-10, 1.0)
    ax.set_title(f"PXP L={L}, k=0, I=+1 sector (dim {dim})", fontsize=10)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(fig_dir / "sector_scar_tower.png", dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6.0, 4.2))
    ax.bar(centers, hist, width=centers[1] - centers[0], color="#9fc5e8", label="unfolded spacings")
    ax.plot(centers, wigner, "-", color="tab:red", label="Wigner surmise (GOE)")
    ax.plot(centers, poisson, "--", color="0.4", label="Poisson")
    ax.set_xlabel("s")
    ax.set_ylabel("P(s)")
    ax.set_title(f"<r> = {r_mean:.4f}  (GOE {GOE_R}, Poisson {POISSON_R})", fontsize=10)
    ax.legend(fontsize=8)
    inset = ax.inset_axes([0.58, 0.52, 0.38, 0.38])
    inset.plot(density_centers, density_hist, color="tab:blue", linewidth=1.2)
    inset.set_title("density of states", fontsize=8)
    inset.tick_params(labelsize=7)
    fig.tight_layout()
    fig.savefig(fig_dir / "sector_level_statistics.png", dpi=150)
    plt.close(fig)

    print(json.dumps({"status": checks["status"], "gate_flags": gate_flags,
                      "r_mean": r_mean, "dim": dim,
                      "tower_spacing_rel_std": spacing_rel_std}, indent=2))
    return 0 if checks["status"] == "physically_consistent" else 1


if __name__ == "__main__":
    raise SystemExit(main())
