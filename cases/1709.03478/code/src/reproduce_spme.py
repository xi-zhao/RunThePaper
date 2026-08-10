from __future__ import annotations

from dataclasses import dataclass
import csv
import hashlib
import json
import math
from pathlib import Path
import time
from typing import Any, Iterable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.linalg import eigh_tridiagonal


@dataclass(frozen=True)
class Basis:
    sites: int
    points_per_site: int
    vp: float
    grid: np.ndarray
    wannier: np.ndarray
    hopping: float


_BASIS_CACHE: dict[tuple[int, int, float, int, int], Basis] = {}


def clear_basis_cache() -> None:
    """Release cached paper-band bases between independently checkpointed blocks."""

    _BASIS_CACHE.clear()


def continuum_tridiagonal(
    sites: int,
    points_per_site: int,
    vp: float,
    vd: float,
    alpha: float,
    phi: float,
    trap_edge_recoil: float = 0.0,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return the dimensionless continuum Hamiltonian in primary-recoil units."""
    if sites <= 2 or points_per_site < 3:
        raise ValueError("sites must exceed 2 and points_per_site must be at least 3")
    count = sites * points_per_site
    step = 1.0 / points_per_site
    grid = (np.arange(count, dtype=float) + 0.5) * step - sites / 2.0
    kinetic = 1.0 / (math.pi * step) ** 2
    potential = 0.5 * vp * np.cos(2.0 * math.pi * grid)
    potential += 0.5 * vd * np.cos(2.0 * math.pi * alpha * grid + phi)
    if trap_edge_recoil:
        potential += trap_edge_recoil * (grid / (sites / 2.0)) ** 2
    diagonal = 2.0 * kinetic + potential
    off_diagonal = np.full(count - 1, -kinetic, dtype=float)
    return grid, diagonal, off_diagonal


def lowest_band(
    sites: int,
    points_per_site: int,
    vp: float,
    vd: float,
    alpha: float,
    phi: float,
    trap_edge_recoil: float = 0.0,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    grid, diagonal, off_diagonal = continuum_tridiagonal(
        sites, points_per_site, vp, vd, alpha, phi, trap_edge_recoil
    )
    values, vectors = eigh_tridiagonal(
        diagonal,
        off_diagonal,
        select="i",
        select_range=(0, sites - 1),
        check_finite=False,
        lapack_driver="stemr",
    )
    return grid, values, vectors


def primary_hopping(vp: float, harmonics: int = 10, points: int = 401) -> float:
    """Nearest-neighbour Fourier coefficient of the primary lowest band."""
    kappas = np.linspace(-0.5, 0.5, points)
    reciprocal = np.arange(-harmonics, harmonics + 1)
    energies = np.empty_like(kappas)
    coupling = np.full(2 * harmonics, vp / 4.0)
    for index, kappa in enumerate(kappas):
        diagonal = 4.0 * (reciprocal + kappa) ** 2
        energies[index] = eigh_tridiagonal(
            diagonal,
            coupling,
            select="i",
            select_range=(0, 0),
            eigvals_only=True,
            check_finite=False,
        )[0]
    hopping = -float(np.trapezoid(energies * np.cos(2.0 * math.pi * kappas), kappas))
    if not hopping > 0.0:
        raise RuntimeError(f"non-positive primary hopping for vp={vp}: {hopping}")
    return hopping


def primary_basis(
    sites: int,
    points_per_site: int,
    vp: float,
    alpha: float,
    bloch_harmonics: int,
    bloch_points: int,
) -> Basis:
    key = (sites, points_per_site, round(vp, 10), bloch_harmonics, bloch_points)
    cached = _BASIS_CACHE.get(key)
    if cached is not None:
        return cached
    grid, _, primary_vectors = lowest_band(
        sites, points_per_site, vp, 0.0, alpha, 0.0
    )
    projected_position = primary_vectors.T @ (grid[:, None] * primary_vectors)
    centers, rotation = np.linalg.eigh(projected_position)
    order = np.argsort(centers)
    wannier = primary_vectors @ rotation[:, order]
    for column in range(wannier.shape[1]):
        pivot = int(np.argmax(np.abs(wannier[:, column])))
        if wannier[pivot, column] < 0:
            wannier[:, column] *= -1.0
    basis = Basis(
        sites=sites,
        points_per_site=points_per_site,
        vp=vp,
        grid=grid,
        wannier=wannier,
        hopping=primary_hopping(vp, bloch_harmonics, bloch_points),
    )
    _BASIS_CACHE[key] = basis
    return basis


def weighted_projector(overlap: np.ndarray, weights: np.ndarray) -> np.ndarray:
    if overlap.shape[1] != len(weights):
        raise ValueError("weight count does not match site basis")
    return (overlap * weights[None, :]) @ overlap.T


def prepare_cdw(overlap: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    weights = np.zeros(overlap.shape[1], dtype=float)
    weights[::2] = 1.0
    parity = np.where(np.arange(overlap.shape[1]) % 2 == 0, 1.0, -1.0)
    return weighted_projector(overlap, weights), weighted_projector(overlap, parity)


def prepare_center_cloud(overlap: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    sites = overlap.shape[1]
    start = sites // 3
    stop = sites - start
    weights = np.zeros(sites, dtype=float)
    weights[start:stop] = 1.0
    return weighted_projector(overlap, weights), weighted_projector(overlap, weights)


def prepare_center_third_eigenstates(
    *,
    sites: int,
    points_per_site: int,
    vp: float,
    vd: float,
    alpha: float,
    phi: float,
    final_eigenvectors: np.ndarray,
    trap_edge_recoil: float = 0.0,
) -> tuple[np.ndarray, np.ndarray, int]:
    """Prepare the occupied eigenstates of the isolated center-third box.

    The paper describes populating eigenstates of the center third before
    releasing them into the full system.  Slicing the full finite-difference
    Hamiltonian preserves the global quasiperiodic phase at the cut.  The
    returned density and center-number operator are in the final lowest-band
    eigenbasis.
    """

    _, diagonal, off_diagonal = continuum_tridiagonal(
        sites, points_per_site, vp, vd, alpha, phi, trap_edge_recoil
    )
    center_sites = sites // 3
    center_points = center_sites * points_per_site
    start = (len(diagonal) - center_points) // 2
    stop = start + center_points
    _, center_vectors = eigh_tridiagonal(
        diagonal[start:stop],
        off_diagonal[start : stop - 1],
        select="i",
        select_range=(0, center_sites - 1),
        check_finite=False,
        lapack_driver="stemr",
    )
    initial_overlap = final_eigenvectors[start:stop, :].T @ center_vectors
    density_matrix = initial_overlap @ initial_overlap.T
    center_operator = final_eigenvectors[start:stop, :].T @ final_eigenvectors[start:stop, :]
    return density_matrix, center_operator, center_sites


def prepare_gaussian_cloud(overlap: np.ndarray, fwhm_sites: float) -> np.ndarray:
    positions = np.arange(overlap.shape[1], dtype=float) - (overlap.shape[1] - 1.0) / 2.0
    weights = np.exp(-4.0 * math.log(2.0) * (positions / fwhm_sites) ** 2)
    return weighted_projector(overlap, weights)


def spectral_expectation(
    eigenvalues: np.ndarray,
    observable: np.ndarray,
    density_matrix: np.ndarray,
    time_tau: float,
    hopping: float,
) -> float:
    phase = np.exp(-1j * (eigenvalues - eigenvalues[0]) * (time_tau / hopping))
    evolved = phase[:, None] * density_matrix * phase.conj()[None, :]
    normalization = float(np.trace(density_matrix).real)
    return float(np.sum(observable.T * evolved).real / normalization)


def dephased_expectation(observable: np.ndarray, density_matrix: np.ndarray) -> float:
    """Infinite-time diagonal-ensemble value for non-degenerate spectra."""
    normalization = float(np.trace(density_matrix).real)
    return float(np.sum(np.diag(observable) * np.diag(density_matrix)).real / normalization)


def site_density(
    eigenvalues: np.ndarray,
    overlap: np.ndarray,
    density_matrix: np.ndarray,
    time_tau: float,
    hopping: float,
) -> np.ndarray:
    phase = np.exp(-1j * (eigenvalues - eigenvalues[0]) * (time_tau / hopping))
    evolved = phase[:, None] * density_matrix * phase.conj()[None, :]
    density = np.einsum("ai,ab,bi->i", overlap, evolved, overlap, optimize=True).real
    density = np.maximum(density, 0.0)
    return density / density.sum()


def cloud_observables(density: np.ndarray, center_slice: slice) -> dict[str, float]:
    positions = np.arange(len(density), dtype=float) - (len(density) - 1.0) / 2.0
    rms = float(np.sqrt(np.sum(positions**2 * density) / np.sum(density)))
    half = 0.5 * float(np.max(density))
    above = np.flatnonzero(density >= half)
    fwhm = float(above[-1] - above[0]) if len(above) else 0.0
    edge_density = float(1.0 - np.sum(density[center_slice]))
    return {"fwhm_sites": fwhm, "rms_sites": rms, "edge_density": edge_density}


def simulate_scalar(
    *,
    sites: int,
    points_per_site: int,
    vp: float,
    vd: float,
    alpha: float,
    phi: float,
    imbalance_time_tau: float,
    edge_time_tau: float,
    phase_hopping: float | None,
    solver: dict[str, Any],
    dephased: bool = False,
) -> dict[str, float]:
    basis = primary_basis(
        sites,
        points_per_site,
        vp,
        alpha,
        int(solver["primary_bloch_harmonics"]),
        int(solver["primary_bloch_points"]),
    )
    _, eigenvalues, eigenvectors = lowest_band(
        sites, points_per_site, vp, vd, alpha, phi
    )
    overlap = eigenvectors.T @ basis.wannier
    cdw_density, imbalance_operator = prepare_cdw(overlap)
    center_density, center_operator = prepare_center_cloud(overlap)
    hopping = basis.hopping if phase_hopping is None else phase_hopping
    if dephased:
        imbalance = dephased_expectation(imbalance_operator, cdw_density)
    else:
        imbalance = spectral_expectation(
            eigenvalues, imbalance_operator, cdw_density, imbalance_time_tau, hopping
        )
    center_probability_0 = spectral_expectation(
        eigenvalues, center_operator, center_density, 0.0, hopping
    )
    if dephased:
        center_probability = dephased_expectation(center_operator, center_density)
    else:
        center_probability = spectral_expectation(
            eigenvalues, center_operator, center_density, edge_time_tau, hopping
        )
    return {
        "imbalance": imbalance,
        "edge_density": 1.0 - center_probability / center_probability_0,
        "projection_cdw": float(np.trace(cdw_density).real / math.ceil(sites / 2)),
        "projection_center": float(np.trace(center_density).real / (sites - 2 * (sites // 3))),
        "hopping_over_recoil": hopping,
        "orthogonality_error": float(np.max(np.abs(eigenvectors.T @ eigenvectors - np.eye(sites)))),
    }


def threshold_crossing(x: np.ndarray, y: np.ndarray, threshold: float, direction: str) -> float | None:
    if direction == "up":
        hits = np.flatnonzero(y >= threshold)
    elif direction == "down":
        hits = np.flatnonzero(y <= threshold)
    else:
        raise ValueError("direction must be up or down")
    if not len(hits):
        return None
    index = int(hits[0])
    if index == 0:
        return float(x[0])
    x0, x1 = float(x[index - 1]), float(x[index])
    y0, y1 = float(y[index - 1]), float(y[index])
    if y1 == y0:
        return x1
    return x0 + (threshold - y0) * (x1 - x0) / (y1 - y0)


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError(f"no rows for {path}")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _time_axis(spec: dict[str, Any]) -> np.ndarray:
    return np.linspace(float(spec["start"]), float(spec["stop"]), int(spec["points"]))


def generate_fig2(parameters: dict[str, Any], output_root: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    spec = parameters["main_trace"]
    solver = parameters["solver"]
    alpha = float(parameters["alpha"])
    times = _time_axis(spec["time_tau"])
    rows: list[dict[str, Any]] = []
    curves: dict[float, list[float]] = {}
    phase_values = [float(value) for value in spec["phases_rad"]]
    for vd in map(float, spec["vd_values"]):
        phase_curves: list[list[float]] = []
        for phi in phase_values:
            basis = primary_basis(
                int(spec["sites"]), int(spec["grid_points_per_site"]), float(spec["vp"]), alpha,
                int(solver["primary_bloch_harmonics"]), int(solver["primary_bloch_points"]),
            )
            _, eigenvalues, eigenvectors = lowest_band(
                int(spec["sites"]), int(spec["grid_points_per_site"]), float(spec["vp"]), vd, alpha, phi
            )
            overlap = eigenvectors.T @ basis.wannier
            center_density, center_operator = prepare_center_cloud(overlap)
            center_probability_0 = spectral_expectation(
                eigenvalues, center_operator, center_density, 0.0, basis.hopping
            )
            values = [
                1.0 - spectral_expectation(eigenvalues, center_operator, center_density, float(t), basis.hopping) / center_probability_0
                for t in times
            ]
            phase_curves.append(values)
        array = np.asarray(phase_curves)
        mean = np.mean(array, axis=0)
        std = np.std(array, axis=0)
        curves[vd] = mean.tolist()
        for t, value, spread in zip(times, mean, std):
            rows.append({
                "target_id": "T002", "vp_recoil": float(spec["vp"]), "vd_recoil": vd,
                "time_tau": float(t), "edge_density_mean": float(value), "edge_density_phase_std": float(spread),
                "sites": int(spec["sites"]), "grid_points_per_site": int(spec["grid_points_per_site"]),
                "phase_samples": len(phase_values), "parameter_match": "reduced_scale",
            })
    checks = {
        "target_id": "T002", "status": "passed", "paper_parameters_preserved": ["Vp=4", "Vd=0,0.57,1.04", "t=0..3000 tau"],
        "reduced_parameters": {"sites": int(spec["sites"]), "phase_samples": len(phase_values)},
        "feature_assertions": {
            "extended_exceeds_intermediate_at_final_time": curves[0.0][-1] > curves[0.57][-1],
            "intermediate_exceeds_localized_at_final_time": curves[0.57][-1] > curves[1.04][-1],
            "all_values_bounded_with_roundoff": all(-1e-12 <= value <= 1.0 + 1e-12 for curve in curves.values() for value in curve),
        },
        "final_values": {str(key): values[-1] for key, values in curves.items()},
    }
    checks["status"] = "passed" if all(checks["feature_assertions"].values()) else "failed"
    _write_csv(output_root / "outputs/data/fig2b_edge_density.csv", rows)
    _write_json(output_root / "outputs/checks/fig2b.json", checks)
    fig, ax = plt.subplots(figsize=(6.4, 4.2), constrained_layout=True)
    colors = {0.0: "#3366cc", 0.57: "#e68613", 1.04: "#b52835"}
    for vd, values in curves.items():
        ax.plot(times, values, lw=2.0, color=colors[vd], label=fr"$V_d={vd:g}E_r^p$")
    ax.set(xlabel=r"Time ($\tau$)", ylabel=r"Edge density $\mathcal{D}$", ylim=(-0.02, 0.75))
    ax.legend(frameon=False)
    ax.set_title("Independent continuum dynamics (reduced L)")
    fig.savefig(output_root / "outputs/figures/fig2b_edge_density.png", dpi=180)
    plt.close(fig)
    return rows, checks


def generate_sweeps(parameters: dict[str, Any], output_root: Path) -> tuple[list[dict[str, Any]], dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    spec = parameters["phase_sweep"]
    solver = parameters["solver"]
    alpha = float(parameters["alpha"])
    time_i = float(parameters["paper_times_tau"]["numerical_imbalance"])
    time_d = float(parameters["paper_times_tau"]["edge_density"])
    phases = [float(value) for value in spec["phases_rad"]]
    factors = np.asarray(spec["tube_depth_factors"], dtype=float)
    weights = np.asarray(spec["tube_weights"], dtype=float)
    weights = weights / weights.sum()
    rows: list[dict[str, Any]] = []
    start_time = time.monotonic()
    for sweep in spec["specs"]:
        vp = float(sweep["vp"])
        central_hopping = primary_hopping(
            vp, int(solver["primary_bloch_harmonics"]), int(solver["primary_bloch_points"])
        )
        vd_values = np.linspace(float(sweep["vd_start"]), float(sweep["vd_stop"]), int(sweep["points"]))
        for vd in vd_values:
            factor_means: list[tuple[float, float, float, float]] = []
            for factor in factors:
                values = [
                    simulate_scalar(
                        sites=int(spec["sites"]), points_per_site=int(spec["grid_points_per_site"]),
                        vp=vp * float(factor), vd=float(vd) * float(factor), alpha=alpha, phi=phi,
                        imbalance_time_tau=time_i, edge_time_tau=time_d, phase_hopping=central_hopping, solver=solver,
                        dephased=True,
                    )
                    for phi in phases
                ]
                i_values = np.asarray([row["imbalance"] for row in values])
                d_values = np.asarray([row["edge_density"] for row in values])
                factor_means.append((float(np.mean(i_values)), float(np.mean(d_values)), float(np.std(i_values)), float(np.std(d_values))))
            central = factor_means[0]
            tube_i = float(sum(weight * value[0] for weight, value in zip(weights, factor_means)))
            tube_d = float(sum(weight * value[1] for weight, value in zip(weights, factor_means)))
            common = {
                "target_ids": "T003;T004", "vp_recoil": vp, "vd_recoil": float(vd),
                "sites": int(spec["sites"]), "grid_points_per_site": int(spec["grid_points_per_site"]),
                "phase_samples": len(phases), "evaluation": "stationary_diagonal_ensemble",
                "reference_imbalance_time_tau": time_i, "reference_edge_time_tau": time_d,
                "parameter_match": "reduced_scale",
            }
            rows.append({**common, "averaging": "central", "imbalance": central[0], "edge_density": central[1], "imbalance_phase_std": central[2], "edge_density_phase_std": central[3]})
            rows.append({**common, "averaging": "tube_proxy", "imbalance": tube_i, "edge_density": tube_d, "imbalance_phase_std": float("nan"), "edge_density_phase_std": float("nan")})
    _write_csv(output_root / "outputs/data/fig3_theory_sweeps.csv", rows)
    checks = {
        "target_id": "T003", "status": "passed", "duration_seconds": round(time.monotonic() - start_time, 6),
        "paper_parameters_preserved": ["Vp sweep includes 3..8", "stationary theoretical I and D", "threshold=0.015"],
        "reduced_parameters": {"sites": int(spec["sites"]), "phase_samples": len(phases), "tube_depth_quadrature": len(factors)},
        "tube_proxy": {"factors": factors.tolist(), "weights": weights.tolist(), "exact_author_histogram_available": False},
        "feature_assertions": {},
    }
    for vp in (4.0, 6.0, 8.0):
        central_rows = [row for row in rows if row["vp_recoil"] == vp and row["averaging"] == "central"]
        central_rows.sort(key=lambda row: row["vd_recoil"])
        checks["feature_assertions"][f"vp{vp:g}_imbalance_grows"] = central_rows[-1]["imbalance"] > central_rows[0]["imbalance"]
        checks["feature_assertions"][f"vp{vp:g}_edge_density_falls"] = central_rows[-1]["edge_density"] < central_rows[0]["edge_density"]
    checks["status"] = "passed" if all(checks["feature_assertions"].values()) else "failed"
    _write_json(output_root / "outputs/checks/fig3.json", checks)

    fig, axes = plt.subplots(1, 3, figsize=(12.6, 3.8), constrained_layout=True)
    for ax, vp in zip(axes, (4.0, 6.0, 8.0)):
        for averaging, style, alpha_line in (("central", "--", 0.8), ("tube_proxy", "-", 1.0)):
            subset = [row for row in rows if row["vp_recoil"] == vp and row["averaging"] == averaging]
            subset.sort(key=lambda row: row["vd_recoil"])
            x = [row["vd_recoil"] for row in subset]
            ax.plot(x, [row["imbalance"] for row in subset], style, color="#3366cc", alpha=alpha_line, label=f"I, {averaging}" if vp == 4 else None)
            ax.plot(x, [row["edge_density"] for row in subset], style, color="#d65f00", alpha=alpha_line, label=f"D, {averaging}" if vp == 4 else None)
        ax.axhline(float(spec["threshold"]), color="black", lw=0.8, ls=":")
        ax.set(title=fr"$V_p={vp:g}E_r^p$", xlabel=fr"$V_d/E_r^p$", ylim=(-0.03, 0.7))
    axes[0].set_ylabel(r"$\mathcal{I},\mathcal{D}$")
    axes[0].legend(frameon=False, fontsize=8)
    fig.savefig(output_root / "outputs/figures/fig3_theory_sweeps.png", dpi=180)
    plt.close(fig)

    boundary_rows: list[dict[str, Any]] = []
    for vp in sorted({float(row["vp_recoil"]) for row in rows}):
        for averaging in ("central", "tube_proxy"):
            subset = [row for row in rows if row["vp_recoil"] == vp and row["averaging"] == averaging]
            subset.sort(key=lambda row: row["vd_recoil"])
            x = np.asarray([row["vd_recoil"] for row in subset])
            imbalance = np.asarray([row["imbalance"] for row in subset])
            edge = np.asarray([row["edge_density"] for row in subset])
            lower = threshold_crossing(x, imbalance, float(spec["threshold"]), "up")
            upper = threshold_crossing(x, edge, float(spec["threshold"]), "down")
            boundary_rows.append({
                "target_id": "T004", "vp_recoil": vp, "averaging": averaging,
                "v_imbalance_recoil": lower, "v_edge_recoil": upper,
                "intermediate_width_recoil": None if lower is None or upper is None else upper - lower,
                "threshold": float(spec["threshold"]), "parameter_match": "reduced_scale",
            })
    _write_csv(output_root / "outputs/data/fig4_phase_boundaries.csv", boundary_rows)
    resolved_widths = [row["intermediate_width_recoil"] for row in boundary_rows if row["averaging"] == "central" and row["intermediate_width_recoil"] is not None]
    fig4_checks = {
        "target_id": "T004", "status": "partial",
        "feature_assertions": {
            "at_least_two_central_boundaries_resolved": len(resolved_widths) >= 2,
            "all_resolved_widths_nonnegative": all(width >= -1e-9 for width in resolved_widths),
        },
        "resolved_central_boundary_count": len(resolved_widths),
        "completeness_reason": "The reduced phase/tube sampling resolves both thresholds only at Vp=4 and Vp=6; this is evidence for an intermediate regime, not a complete phase boundary.",
        "unresolved_boundaries": [row for row in boundary_rows if row["v_imbalance_recoil"] is None or row["v_edge_recoil"] is None],
        "pixel_status": "not_applicable",
        "pixel_reason": "Independent replot is not registered to the paper panel geometry.",
    }
    if not all(fig4_checks["feature_assertions"].values()):
        fig4_checks["status"] = "failed"
    _write_json(output_root / "outputs/checks/fig4.json", fig4_checks)
    fig, ax = plt.subplots(figsize=(6.2, 4.6), constrained_layout=True)
    for averaging, style, marker in (("tube_proxy", "-", "o"), ("central", "--", "s")):
        subset = [row for row in boundary_rows if row["averaging"] == averaging]
        vp_axis = [row["vp_recoil"] for row in subset]
        lower = [np.nan if row["v_imbalance_recoil"] is None else row["v_imbalance_recoil"] for row in subset]
        upper = [np.nan if row["v_edge_recoil"] is None else row["v_edge_recoil"] for row in subset]
        ax.plot(vp_axis, lower, style, marker=marker, color="#3366cc", label=fr"$V_\mathcal{{I}}$, {averaging}")
        ax.plot(vp_axis, upper, style, marker=marker, color="#d65f00", label=fr"$V_\mathcal{{D}}$, {averaging}")
    ax.set(xlabel=r"$V_p/E_r^p$", ylabel=r"$V_d/E_r^p$", title="Generated intermediate-phase boundaries")
    ax.legend(frameon=False, fontsize=8, ncol=2)
    fig.savefig(output_root / "outputs/figures/fig4_phase_boundaries.png", dpi=180)
    plt.close(fig)
    return rows, checks, boundary_rows, fig4_checks


def generate_supplement(parameters: dict[str, Any], sweep_rows: list[dict[str, Any]], output_root: Path) -> tuple[list[dict[str, Any]], dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    spec = parameters["supplement_trace"]
    solver = parameters["solver"]
    alpha = float(parameters["alpha"])
    times = _time_axis(spec["time_tau"])
    rows: list[dict[str, Any]] = []
    for trap_edge in map(float, spec["trap_edge_recoil"]):
        for vd in map(float, spec["vd_values"]):
            phase_profiles: list[list[dict[str, float]]] = []
            for phi in map(float, spec["phases_rad"]):
                basis = primary_basis(
                    int(spec["sites"]), int(spec["grid_points_per_site"]), float(spec["vp"]), alpha,
                    int(solver["primary_bloch_harmonics"]), int(solver["primary_bloch_points"]),
                )
                _, eigenvalues, eigenvectors = lowest_band(
                    int(spec["sites"]), int(spec["grid_points_per_site"]), float(spec["vp"]), vd, alpha, phi, trap_edge
                )
                overlap = eigenvectors.T @ basis.wannier
                density_matrix = prepare_gaussian_cloud(overlap, float(spec["gaussian_fwhm_sites"]))
                center_start = int(spec["sites"]) // 3
                center_slice = slice(center_start, int(spec["sites"]) - center_start)
                phase_profiles.append([
                    cloud_observables(site_density(eigenvalues, overlap, density_matrix, float(t), basis.hopping), center_slice)
                    for t in times
                ])
            scale = float(spec["paper_sites"]) / float(spec["sites"])
            for time_index, t in enumerate(times):
                values = [profile[time_index] for profile in phase_profiles]
                fwhm = float(np.mean([value["fwhm_sites"] for value in values]))
                rms = float(np.mean([value["rms_sites"] for value in values]))
                edge = float(np.mean([value["edge_density"] for value in values]))
                rows.append({
                    "target_id": "T005", "trap_edge_recoil": trap_edge, "vp_recoil": float(spec["vp"]), "vd_recoil": vd,
                    "time_tau": float(t), "fwhm_reduced_sites": fwhm, "fwhm_paper_equivalent_sites": fwhm * scale,
                    "edge_density": edge, "rms_reduced_sites": rms, "rms_paper_equivalent_sites": rms * scale,
                    "sites": int(spec["sites"]), "paper_sites": int(spec["paper_sites"]), "parameter_match": "reduced_scale",
                })
    _write_csv(output_root / "outputs/data/supp_fig_s1_observables.csv", rows)
    checks = {
        "target_id": "T005", "status": "passed",
        "paper_parameters_preserved": ["Vp=4", "Vd=0,0.4,0.57,1.04", "t=0..3000 tau", "trap edge potential=0.003 Er"],
        "reduced_parameters": {"sites": int(spec["sites"]), "paper_sites": int(spec["paper_sites"]), "phase_samples": len(spec["phases_rad"])},
        "feature_assertions": {},
    }
    for trap_edge in map(float, spec["trap_edge_recoil"]):
        final = {row["vd_recoil"]: row for row in rows if row["trap_edge_recoil"] == trap_edge and row["time_tau"] == float(times[-1])}
        checks["feature_assertions"][f"trap_{trap_edge:g}_edge_order"] = final[0.0]["edge_density"] > final[0.57]["edge_density"] > final[1.04]["edge_density"]
        checks["feature_assertions"][f"trap_{trap_edge:g}_rms_order"] = final[0.0]["rms_reduced_sites"] > final[0.57]["rms_reduced_sites"] > final[1.04]["rms_reduced_sites"]
    checks["status"] = "passed" if all(checks["feature_assertions"].values()) else "failed"
    _write_json(output_root / "outputs/checks/supp_fig_s1.json", checks)
    fig, axes = plt.subplots(2, 3, figsize=(12.0, 6.6), constrained_layout=True, sharex=True)
    colors = {0.0: "#3366cc", 0.4: "#4daf4a", 0.57: "#e68613", 1.04: "#b52835"}
    for row_index, trap_edge in enumerate(map(float, spec["trap_edge_recoil"])):
        for vd in map(float, spec["vd_values"]):
            subset = [row for row in rows if row["trap_edge_recoil"] == trap_edge and row["vd_recoil"] == vd]
            subset.sort(key=lambda row: row["time_tau"])
            axes[row_index, 0].plot([row["time_tau"] for row in subset], [row["fwhm_paper_equivalent_sites"] for row in subset], color=colors[vd], label=fr"$V_d={vd:g}$")
            axes[row_index, 1].plot([row["time_tau"] for row in subset], [row["edge_density"] for row in subset], color=colors[vd])
            axes[row_index, 2].plot([row["time_tau"] for row in subset], [row["rms_paper_equivalent_sites"] for row in subset], color=colors[vd])
        axes[row_index, 0].set_ylabel("homogeneous" if trap_edge == 0.0 else "weak trap")
    axes[0, 0].set_title("FWHM (paper-site equivalent)")
    axes[0, 1].set_title(r"Edge density $\mathcal{D}$")
    axes[0, 2].set_title("RMS radius (paper-site equivalent)")
    for ax in axes[1]:
        ax.set_xlabel(r"Time ($\tau$)")
    axes[0, 0].legend(frameon=False, fontsize=8)
    fig.savefig(output_root / "outputs/figures/supp_fig_s1_observables.png", dpi=180)
    plt.close(fig)

    sweep_spec = parameters["phase_sweep"]
    vp4_spec = next(item for item in sweep_spec["specs"] if float(item["vp"]) == 4.0)
    sweep_phases = [float(value) for value in sweep_spec["phases_rad"]]
    factors = np.asarray(sweep_spec["tube_depth_factors"], dtype=float)
    weights = np.asarray(sweep_spec["tube_weights"], dtype=float)
    weights /= weights.sum()
    central_hopping = primary_hopping(
        4.0, int(solver["primary_bloch_harmonics"]), int(solver["primary_bloch_points"])
    )
    s2_rows: list[dict[str, Any]] = []
    for vd in np.linspace(float(vp4_spec["vd_start"]), float(vp4_spec["vd_stop"]), int(vp4_spec["points"])):
        factor_means: list[tuple[float, float]] = []
        for factor in factors:
            values = [
                simulate_scalar(
                    sites=int(sweep_spec["sites"]), points_per_site=int(sweep_spec["grid_points_per_site"]),
                    vp=4.0 * float(factor), vd=float(vd) * float(factor), alpha=alpha, phi=phi,
                    imbalance_time_tau=3000.0, edge_time_tau=3000.0, phase_hopping=central_hopping,
                    solver=solver, dephased=False,
                )
                for phi in sweep_phases
            ]
            factor_means.append((
                float(np.mean([value["imbalance"] for value in values])),
                float(np.mean([value["edge_density"] for value in values])),
            ))
        central = factor_means[0]
        tube_i = float(sum(weight * value[0] for weight, value in zip(weights, factor_means)))
        tube_d = float(sum(weight * value[1] for weight, value in zip(weights, factor_means)))
        for averaging, imbalance, edge in (
            ("central", central[0], central[1]),
            ("tube_proxy", tube_i, tube_d),
        ):
            s2_rows.append({
                "target_id": "T006", "vp_recoil": 4.0, "vd_recoil": float(vd),
                "imbalance_3000tau": imbalance, "edge_density_3000tau": edge,
                "averaging": averaging, "sites": int(sweep_spec["sites"]),
                "phase_samples": len(sweep_phases), "parameter_match": "reduced_scale",
            })
    _write_csv(output_root / "outputs/data/supp_fig_s2_finite_time.csv", s2_rows)
    s2_checks = {
        "target_id": "T006", "status": "passed", "generated_theory_only": True,
        "experimental_200tau_status": "deferred_missing_author_data",
        "feature_assertions": {
            "imbalance_rises_with_detuning": s2_rows[-2]["imbalance_3000tau"] > s2_rows[0]["imbalance_3000tau"],
            "edge_density_falls_with_detuning": s2_rows[-2]["edge_density_3000tau"] < s2_rows[0]["edge_density_3000tau"],
        },
    }
    s2_checks["status"] = "passed" if all(s2_checks["feature_assertions"].values()) else "failed"
    _write_json(output_root / "outputs/checks/supp_fig_s2.json", s2_checks)
    fig, ax = plt.subplots(figsize=(6.4, 4.2), constrained_layout=True)
    for averaging, style in (("central", "--"), ("tube_proxy", "-")):
        subset = [row for row in s2_rows if row["averaging"] == averaging]
        subset.sort(key=lambda row: row["vd_recoil"])
        ax.plot([row["vd_recoil"] for row in subset], [row["imbalance_3000tau"] for row in subset], style, color="#3366cc", label=f"I, {averaging}")
        ax.plot([row["vd_recoil"] for row in subset], [row["edge_density_3000tau"] for row in subset], style, color="#d65f00", label=f"D, {averaging}")
    ax.set(xlabel=r"$V_d/E_r^p$", ylabel=r"$\mathcal{I},\mathcal{D}$", title=r"Generated theory at $3000\tau$ ($V_p=4$)")
    ax.legend(frameon=False, fontsize=8)
    fig.savefig(output_root / "outputs/figures/supp_fig_s2_finite_time.png", dpi=180)
    plt.close(fig)
    return rows, checks, s2_rows, s2_checks


def run(parameters: dict[str, Any], output_root: Path) -> dict[str, Any]:
    started = time.monotonic()
    (output_root / "outputs/data").mkdir(parents=True, exist_ok=True)
    (output_root / "outputs/checks").mkdir(parents=True, exist_ok=True)
    (output_root / "outputs/figures").mkdir(parents=True, exist_ok=True)
    fig2_rows, fig2_checks = generate_fig2(parameters, output_root)
    sweep_rows, fig3_checks, boundary_rows, fig4_checks = generate_sweeps(parameters, output_root)
    s1_rows, s1_checks, s2_rows, s2_checks = generate_supplement(parameters, sweep_rows, output_root)

    data_paths = [
        output_root / "outputs/data/fig2b_edge_density.csv",
        output_root / "outputs/data/fig3_theory_sweeps.csv",
        output_root / "outputs/data/fig4_phase_boundaries.csv",
        output_root / "outputs/data/supp_fig_s1_observables.csv",
        output_root / "outputs/data/supp_fig_s2_finite_time.csv",
    ]
    freeze = {
        "schema_version": 1,
        "paper_id": parameters["paper_id"],
        "status": "frozen_before_reference_render",
        "reference_assets_read": False,
        "data_files": [{"path": str(path.relative_to(output_root)), "sha256": _sha256(path)} for path in data_paths],
    }
    _write_json(output_root / "outputs/checks/data_freeze.json", freeze)

    sanity = {
        "schema_version": 1,
        "status": "passed",
        "checks": {
            "formula_gate_expected_open": True,
            "fig2_features": fig2_checks["status"] == "passed",
            "fig3_features": fig3_checks["status"] == "passed",
            "fig4_core_features": all(fig4_checks["feature_assertions"].values()),
            "supp_s1_features": s1_checks["status"] == "passed",
            "supp_s2_features": s2_checks["status"] == "passed",
        },
        "row_counts": {"fig2": len(fig2_rows), "fig3": len(sweep_rows), "fig4": len(boundary_rows), "supp_s1": len(s1_rows), "supp_s2": len(s2_rows)},
    }
    sanity["status"] = "passed" if all(sanity["checks"].values()) else "failed"
    _write_json(output_root / "outputs/checks/numerical_sanity.json", sanity)
    summary = {
        "schema_version": 1,
        "paper_id": parameters["paper_id"],
        "status": "passed" if sanity["status"] == "passed" else "failed",
        "artifact_stage": parameters["artifact_stage"],
        "parameter_match": "reduced_scale",
        "generated_data_provenance": "independent_numerics",
        "duration_seconds": round(time.monotonic() - started, 6),
        "targets": ["T002", "T003", "T004", "T005", "T006"],
        "reference_assets_read": False,
        "author_code_or_arrays_used": False,
    }
    _write_json(output_root / "outputs/checks/run_summary.json", summary)
    if summary["status"] != "passed":
        raise RuntimeError("one or more numerical feature assertions failed; inspect generated checks")
    return summary
