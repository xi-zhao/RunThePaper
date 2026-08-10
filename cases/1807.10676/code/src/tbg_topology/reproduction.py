"""Numerical orchestration for the scientific reproduction.

Only equations and parameters from the paper enter this module.  Source figures
are intentionally absent from every API so this code can run in an isolated
directory without access to ``raw/`` or ``references/``.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Any

import numpy as np
from scipy.ndimage import minimum_filter
from scipy.optimize import minimize

from .model import (
    ContinuumModel,
    TB4OneValley,
    TB4TwoValley,
    TB8TwoValley,
    band_path,
    wilson_spectrum,
)

TARGET_FILES = {
    "T001": "T001_main_fig1a_velocity.npz",
    "T002": "T002_main_fig1b_wilson.npz",
    "T003": "T003_main_fig2b_tb4_bands.npz",
    "T004": "T004_main_fig2c_tb4_wilson.npz",
    "T005": "T005_supp_fig2a_levels.npz",
    "T006": "T006_supp_fig3_bands.npz",
    "T007": "T007_supp_fig4a_gamma_levels.npz",
    "T008": "T008_supp_fig5_magic_generation.npz",
    "T009": "T009_supp_fig6_ph_breaking.npz",
    "T010": "T010_supp_fig7_wilson.npz",
    "T011": "T011_supp_fig9_tb8.npz",
    "T012": "T012_supp_fig10_tb4_2v.npz",
}


@dataclass
class ReproductionResult:
    formula_checks: dict[str, Any]
    convergence: dict[str, Any]
    target_checks: dict[str, Any]
    elapsed_seconds: float


def adaptive_cutoff(alpha: float) -> int:
    """Complete-shell cutoff needed by each coupling regime."""

    if alpha <= 0.75:
        return 4
    if alpha <= 1.4:
        return 6
    if alpha <= 2.05:
        return 7
    if alpha <= 2.9:
        return 10
    if alpha <= 3.5:
        return 11
    return 12


def model_for(
    alpha: float, cache: dict[tuple[int, str], ContinuumModel], shape: str = "hex"
) -> ContinuumModel:
    cutoff = adaptive_cutoff(float(alpha))
    key = (cutoff, shape)
    if key not in cache:
        cache[key] = ContinuumModel(cutoff=cutoff, basis_shape=shape)
    return cache[key]


def continuum_path(
    model: ContinuumModel, points_per_segment: int
) -> tuple[np.ndarray, np.ndarray, list[int]]:
    return band_path(
        [model.k_point, model.gamma, model.m_point, model.k_end],
        points_per_segment,
    )


def _inside_hex(displacement: np.ndarray, radius: float = 1.0) -> bool:
    x, y = displacement
    return bool(
        abs(x) <= np.sqrt(3.0) * radius / 2.0 + 1.0e-12
        and abs(y) <= radius + 1.0e-12
        and np.sqrt(3.0) * abs(x) + abs(y) <= 2.0 * radius + 1.0e-12
    )


def _periodic_distance(
    first: np.ndarray, second: np.ndarray, model: ContinuumModel
) -> float:
    shifts = [m * model.b1 + n * model.b2 for m in (-1, 0, 1) for n in (-1, 0, 1)]
    return min(float(np.linalg.norm(first - second + shift)) for shift in shifts)


def _hex_representative(momentum: np.ndarray, model: ContinuumModel) -> np.ndarray:
    candidates = [
        momentum + m * model.b1 + n * model.b2
        for m in (-2, -1, 0, 1, 2)
        for n in (-2, -1, 0, 1, 2)
    ]
    inside = [
        candidate for candidate in candidates if _inside_hex(candidate - model.gamma)
    ]
    if inside:
        return min(inside, key=lambda point: np.linalg.norm(point - model.gamma))
    return min(candidates, key=lambda point: np.linalg.norm(point - model.gamma))


def find_dirac_nodes(
    model: ContinuumModel,
    alpha: float,
    grid_points: int,
    max_nodes: int,
) -> tuple[np.ndarray, np.ndarray, dict[str, float]]:
    """Locate central-band Dirac nodes from minima of the computed gap."""

    center = model.gamma
    xs = np.linspace(
        center[0] - np.sqrt(3.0) / 2.0, center[0] + np.sqrt(3.0) / 2.0, grid_points
    )
    ys = np.linspace(center[1] - 1.0, center[1] + 1.0, grid_points)
    gap = np.full((grid_points, grid_points), np.nan)
    for ix, x in enumerate(xs):
        for iy, y in enumerate(ys):
            point = np.array([x, y])
            if _inside_hex(point - center):
                gap[iy, ix] = model.central_gap(point, alpha)
    filled = np.where(np.isfinite(gap), gap, np.inf)
    local = (
        filled <= minimum_filter(filled, size=3, mode="constant", cval=np.inf) + 1.0e-12
    )
    candidate_indices = np.argwhere(local & np.isfinite(gap))
    candidate_indices = sorted(
        candidate_indices, key=lambda index: filled[tuple(index)]
    )[:48]

    def objective(point: np.ndarray) -> float:
        representative = _hex_representative(np.asarray(point, dtype=float), model)
        if not _inside_hex(representative - center):
            return 1.0
        value = model.central_gap(representative, alpha)
        return value * value

    nodes: list[np.ndarray] = []
    residuals: list[float] = []
    for iy, ix in candidate_indices:
        seed = np.array([xs[ix], ys[iy]])
        optimized = minimize(
            objective,
            seed,
            method="Nelder-Mead",
            options={"maxiter": 100, "xatol": 2.0e-6, "fatol": 1.0e-14},
        )
        point = _hex_representative(optimized.x, model)
        residual = model.central_gap(point, alpha)
        if residual > 1.0e-4:
            continue
        if any(_periodic_distance(point, old, model) < 1.5e-2 for old in nodes):
            continue
        nodes.append(point)
        residuals.append(residual)
        if len(nodes) >= max_nodes:
            break

    # Add every geometrically equivalent BZ corner.  They are the same two
    # torus nodes but are all shown in the paper's hexagonal-zone panels.
    corner_vector = model.k_point - center
    corners = [
        center
        + np.array(
            [
                [np.cos(n * np.pi / 3.0), -np.sin(n * np.pi / 3.0)],
                [np.sin(n * np.pi / 3.0), np.cos(n * np.pi / 3.0)],
            ]
        )
        @ corner_vector
        for n in range(6)
    ]
    for corner in corners:
        if not any(np.linalg.norm(corner - old) < 1.5e-2 for old in nodes):
            nodes.append(corner)
            residuals.append(model.central_gap(corner, alpha))

    signs = np.asarray(
        [_dirac_vorticity(model, alpha, node) for node in nodes], dtype=int
    )
    order = np.argsort(
        np.arctan2(
            np.asarray(nodes)[:, 1] - center[1], np.asarray(nodes)[:, 0] - center[0]
        )
    )
    nodes_array = np.asarray(nodes, dtype=float)[order]
    signs = signs[order]
    diagnostics = {
        "max_gap_residual": float(max(residuals, default=np.nan)),
        "min_gap_residual": float(min(residuals, default=np.nan)),
        "node_count": int(len(nodes)),
    }
    return nodes_array, signs, diagnostics


def _dirac_vorticity(model: ContinuumModel, alpha: float, point: np.ndarray) -> int:
    """Sign of the local real two-band Jacobian in a C2T=K gauge."""

    takagi = np.array([[1.0, 1.0j], [1.0, -1.0j]], dtype=complex) / np.sqrt(2.0)
    transform = np.kron(np.eye(2 * model.n_g, dtype=complex), takagi)
    h0 = transform.conj().T @ model.hamiltonian(point, alpha) @ transform
    h0 = np.real_if_close(h0, tol=1.0e4).real
    _, vectors = np.linalg.eigh(h0)
    basis = vectors[:, model.middle - 1 : model.middle + 1]
    step = 2.0e-4
    jacobian = np.zeros((2, 2), dtype=float)
    for axis in range(2):
        delta = np.zeros(2)
        delta[axis] = step
        plus = transform.conj().T @ model.hamiltonian(point + delta, alpha) @ transform
        minus = transform.conj().T @ model.hamiltonian(point - delta, alpha) @ transform
        derivative = basis.T @ ((plus.real - minus.real) / (2.0 * step)) @ basis
        jacobian[0, axis] = derivative[0, 1]
        jacobian[1, axis] = 0.5 * (derivative[0, 0] - derivative[1, 1])
    determinant = float(np.linalg.det(jacobian))
    return 1 if determinant >= 0.0 else -1


def _tb4_kwargs(parameters: dict[str, Any] | None) -> dict[str, float]:
    if parameters is None:
        return {}
    return {
        "t": float(parameters["t"]),
        "t_prime": float(parameters["t_prime"]),
        "lambda_": float(parameters["lambda"]),
        "delta": float(parameters["delta"]),
    }


def projected_wannier(
    k_grid: int,
    real_radius: int,
    tb4_parameters: dict[str, Any] | None = None,
) -> dict[str, np.ndarray | float]:
    """Projection-method Wannier densities from Supplement Eqs. (proj-1)--(psi-tilde)."""

    model = TB8TwoValley(zeta=0.0, **_tb4_kwargs(tb4_parameters))
    lattice = model.lattice
    c1 = 1.0 + 1.0j
    c2 = 1.0 - 1.0j
    projections = np.zeros((8, 4), dtype=complex)
    # Per valley, TB4 basis is (s,t1), (s,t2), (p,t1), (p,t2).
    projections[0, 0], projections[4, 0] = c1, c1.conjugate()
    # The second 2c site is the symmetry partner of the first, so the valley
    # coefficients are conjugated in the opposite order.  This is the gauge
    # implicit in the paper's compact ``t_{1,2}`` notation and is required for
    # the stated nonsingular 15.8 <= det S(k) <= 16 projection frame.
    projections[1, 1], projections[5, 1] = c1.conjugate(), c1
    projections[2, 2], projections[6, 2] = c2, c2.conjugate()
    projections[3, 3], projections[7, 3] = c2.conjugate(), c2

    k_records: list[np.ndarray] = []
    frames: list[np.ndarray] = []
    determinants: list[float] = []
    for u in np.arange(k_grid) / k_grid:
        for v in np.arange(k_grid) / k_grid:
            momentum = u * lattice.b1 + v * lattice.b2
            _, vectors = model.eigensystem(momentum)
            occupied = vectors[:, :4]
            projected = occupied @ (occupied.conj().T @ projections)
            overlap = projected.conj().T @ projected
            values, basis = np.linalg.eigh(overlap)
            inverse_sqrt = basis @ np.diag(values**-0.5) @ basis.conj().T
            frames.append(projected @ inverse_sqrt)
            k_records.append(momentum)
            determinants.append(float(np.linalg.det(overlap).real))

    points: list[np.ndarray] = []
    density_s: list[float] = []
    density_p: list[float] = []
    k_array = np.asarray(k_records)
    frame_array = np.asarray(frames)
    orbital_sublattice = np.tile(np.array([0, 1, 0, 1]), 2)
    for m in range(-real_radius, real_radius + 1):
        for n in range(-real_radius, real_radius + 1):
            lattice_shift = m * lattice.real_vectors[0] + n * lattice.real_vectors[1]
            for sublattice in (0, 1):
                site = lattice_shift + lattice.sublattices[sublattice]
                amplitudes = np.zeros((2, 8), dtype=complex)
                for column, center_sublattice in ((0, 0), (3, 1)):
                    phases = np.exp(
                        1.0j
                        * (k_array @ (site - lattice.sublattices[center_sublattice]))
                    )
                    amplitudes[0 if column == 0 else 1] = np.mean(
                        phases[:, None] * frame_array[:, :, column], axis=0
                    )
                mask = orbital_sublattice == sublattice
                points.append(site)
                density_s.append(float(np.sum(np.abs(amplitudes[0, mask]) ** 2)))
                density_p.append(float(np.sum(np.abs(amplitudes[1, mask]) ** 2)))
    return {
        "points": np.asarray(points),
        "density_s": np.asarray(density_s),
        "density_p": np.asarray(density_p),
        "det_s_min": float(min(determinants)),
        "det_s_max": float(max(determinants)),
    }


def _save_npz(path: Path, **arrays: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path, **arrays)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _output_directories(config: dict[str, Any], workspace: Path) -> tuple[Path, Path]:
    """Resolve one isolated output namespace without changing legacy paths."""

    namespace = config.get("output_namespace")
    if namespace is None:
        return workspace / "outputs" / "data", workspace / "outputs" / "checks"
    if not isinstance(namespace, str) or not namespace:
        raise ValueError("output_namespace must be a non-empty string")
    normalized = namespace.replace("-", "").replace("_", "")
    if not normalized.isalnum() or Path(namespace).parts != (namespace,):
        raise ValueError(
            "output_namespace must be one safe directory name containing only "
            "letters, numbers, '-' or '_'"
        )
    return (
        workspace / "outputs" / "data" / namespace,
        workspace / "outputs" / "checks" / namespace,
    )


def run_reproduction(config: dict[str, Any], workspace: Path) -> ReproductionResult:
    started = perf_counter()
    output_data, output_checks = _output_directories(config, workspace)
    output_data.mkdir(parents=True, exist_ok=True)
    output_checks.mkdir(parents=True, exist_ok=True)
    data_prefix = output_data.relative_to(workspace).as_posix()
    cache: dict[tuple[int, str], ContinuumModel] = {}
    numeric = config["numerics"]
    paper_parameters = config["paper_parameters"]
    tb4_parameters = paper_parameters.get("tb4")

    # T001 and T005: velocity, isolation and high-symmetry level evolution.
    alphas = np.linspace(*numeric["alpha_scan"])
    velocity = np.empty_like(alphas)
    gamma_levels = np.empty((len(alphas), 6))
    m_levels = np.empty((len(alphas), 6))
    for index, alpha in enumerate(alphas):
        model = model_for(float(alpha), cache)
        velocity[index] = model.fermi_velocity(float(alpha), numeric["velocity_step"])
        gamma_levels[index] = model.central_eigenvalues(model.gamma, float(alpha), 3)
        m_levels[index] = model.central_eigenvalues(model.m_point, float(alpha), 3)

    gap_alphas = np.linspace(*numeric["gap_alpha_scan"])
    isolation = np.empty_like(gap_alphas)
    for index, alpha in enumerate(gap_alphas):
        model = model_for(float(alpha), cache)
        path_k, _, _ = continuum_path(model, numeric["gap_path_points_per_segment"])
        uv = np.linspace(0.0, 1.0, numeric["gap_uv_grid"], endpoint=False)
        coarse = [model.gamma + u * model.b1 + v * model.b2 for u in uv for v in uv]
        isolation[index] = min(
            model.isolation_gap(momentum, float(alpha))
            for momentum in [*path_k, *coarse]
        )
    _save_npz(
        output_data / TARGET_FILES["T001"],
        alpha=alphas,
        velocity_over_vf=velocity,
        gap_alpha=gap_alphas,
        isolation_gap=isolation,
    )
    _save_npz(
        output_data / TARGET_FILES["T005"],
        alpha=alphas,
        gamma_levels=gamma_levels,
        m_levels=m_levels,
        k_zero_levels=np.zeros((len(alphas), 2)),
    )

    # T002/T010: four continuum Wilson-loop phases.
    phase_alphas = np.asarray(
        config["paper_parameters"]["gapped_phase_alphas"], dtype=float
    )
    wilson_u = np.linspace(0.0, 1.0, numeric["wilson_u_points"])
    phase_spectra = []
    phase_cutoffs = []
    for alpha in phase_alphas:
        model = model_for(float(alpha), cache)
        phase_cutoffs.append(model.cutoff)
        phase_spectra.append(
            model.wilson_spectrum(float(alpha), wilson_u, numeric["wilson_loop_points"])
        )
    for target_id in ("T002", "T010"):
        _save_npz(
            output_data / TARGET_FILES[target_id],
            alpha=phase_alphas,
            u=wilson_u,
            phases=np.asarray(phase_spectra),
            cutoffs=np.asarray(phase_cutoffs),
        )

    # T003/T004: four-band one-valley model.
    tb4 = TB4OneValley(**_tb4_kwargs(tb4_parameters))
    tb_path, tb_distance, tb_ticks = band_path(
        [tb4.lattice.gamma, tb4.lattice.k, tb4.lattice.m, tb4.lattice.gamma],
        numeric["tb_points_per_segment"],
    )
    tb4_bands = np.asarray([tb4.eigensystem(momentum)[0] for momentum in tb_path])
    _save_npz(
        output_data / TARGET_FILES["T003"],
        path_distance=tb_distance,
        tick_indices=np.asarray(tb_ticks),
        bands=tb4_bands,
    )
    tb_u = np.linspace(0.0, 1.0, numeric["tb_wilson_u_points"])
    tb4_wilson = wilson_spectrum(
        tb4.eigensystem,
        tb4.embedding_b2(),
        tb4.lattice.b1,
        tb4.lattice.b2,
        2,
        tb_u,
        numeric["tb_wilson_loop_points"],
    )
    _save_npz(output_data / TARGET_FILES["T004"], u=tb_u, phases=tb4_wilson)

    # T006: all nine numerical subpanels in Supplement Figure 3.
    band_alphas = np.asarray(
        config["paper_parameters"]["supplement_band_alphas"], dtype=float
    )
    band_sets = []
    band_distances = []
    band_ticks = []
    band_cutoffs = []
    for alpha in band_alphas:
        model = model_for(float(alpha), cache)
        path_k, distance, ticks = continuum_path(
            model, numeric["continuum_points_per_segment"]
        )
        band_sets.append(model.band_structure(path_k, float(alpha), 4))
        band_distances.append(distance)
        band_ticks.append(ticks)
        band_cutoffs.append(model.cutoff)
    _save_npz(
        output_data / TARGET_FILES["T006"],
        alpha=band_alphas,
        path_distance=np.asarray(band_distances),
        tick_indices=np.asarray(band_ticks),
        bands=np.asarray(band_sets),
        cutoffs=np.asarray(band_cutoffs),
    )

    # T007: Gamma level crossings around the first magic angle.
    gamma_alpha = np.linspace(*numeric["gamma_zoom_scan"])
    gamma_model = model_for(0.60, cache)
    gamma_zoom = np.asarray(
        [
            gamma_model.central_eigenvalues(gamma_model.gamma, float(alpha), 4)
            for alpha in gamma_alpha
        ]
    )
    _save_npz(
        output_data / TARGET_FILES["T007"], alpha=gamma_alpha, gamma_levels=gamma_zoom
    )

    # T008: six band panels and six independently located node maps.
    magic_alphas = np.asarray(
        config["paper_parameters"]["magic_generation_alphas"], dtype=float
    )
    magic_bands = []
    magic_distances = []
    node_records: list[np.ndarray] = []
    sign_records: list[np.ndarray] = []
    node_diagnostics = []
    for alpha in magic_alphas:
        model = model_for(float(alpha), cache)
        path_k, distance, _ = continuum_path(model, numeric["magic_points_per_segment"])
        magic_bands.append(model.band_structure(path_k, float(alpha), 4))
        magic_distances.append(distance)
        nodes, signs, diagnostic = find_dirac_nodes(
            model,
            float(alpha),
            numeric["node_grid_points"],
            numeric["node_max_count"],
        )
        node_records.append(nodes)
        sign_records.append(signs)
        node_diagnostics.append(diagnostic)
    max_count = max(len(nodes) for nodes in node_records)
    node_positions = np.full((len(magic_alphas), max_count, 2), np.nan)
    node_signs = np.zeros((len(magic_alphas), max_count), dtype=int)
    node_counts = np.zeros(len(magic_alphas), dtype=int)
    for index, (nodes, signs) in enumerate(zip(node_records, sign_records)):
        node_positions[index, : len(nodes)] = nodes
        node_signs[index, : len(signs)] = signs
        node_counts[index] = len(nodes)
    _save_npz(
        output_data / TARGET_FILES["T008"],
        alpha=magic_alphas,
        path_distance=np.asarray(magic_distances),
        bands=np.asarray(magic_bands),
        node_positions=node_positions,
        node_signs=node_signs,
        node_counts=node_counts,
        bz_center=gamma_model.gamma,
    )

    # T009: all eight PH-breaking band panels from the printed t,t' sets.
    ph_sets = config["paper_parameters"]["ph_breaking_sets"]
    ph_model = ContinuumModel(cutoff=numeric["ph_breaking_cutoff"])
    ph_path, ph_distance, ph_ticks = continuum_path(
        ph_model, numeric["ph_points_per_segment"]
    )
    ph_bands = []
    ph_alpha = []
    ph_theta_deg = []
    w_ev = config["paper_parameters"]["interlayer_w_ev"]
    fixed_alpha = config["paper_parameters"]["first_magic_alpha"]
    fixed_theta = np.deg2rad(config["paper_parameters"]["fixed_theta_deg"])
    for mode in ("fixed_alpha", "fixed_theta"):
        for parameters in ph_sets:
            t_abs = abs(parameters["t_ev"])
            if mode == "fixed_alpha":
                alpha = fixed_alpha
                theta = 2.0 * np.arcsin(
                    w_ev * np.sqrt(3.0) / (4.0 * np.pi * t_abs * alpha)
                )
            else:
                theta = fixed_theta
                alpha = (
                    w_ev * np.sqrt(3.0) / (4.0 * np.pi * t_abs * np.sin(theta / 2.0))
                )
            options = {
                **parameters,
                "theta_rad": float(theta),
                "w_ev": float(w_ev),
            }
            values = [
                ph_model.central_eigenvalues(momentum, alpha, 4, ph_breaking=options)
                * 1000.0
                for momentum in ph_path
            ]
            ph_bands.append(values)
            ph_alpha.append(alpha)
            ph_theta_deg.append(np.rad2deg(theta))
    _save_npz(
        output_data / TARGET_FILES["T009"],
        path_distance=ph_distance,
        tick_indices=np.asarray(ph_ticks),
        bands_mev=np.asarray(ph_bands),
        alpha=np.asarray(ph_alpha),
        theta_deg=np.asarray(ph_theta_deg),
        t_ev=np.asarray([entry["t_ev"] for entry in ph_sets] * 2),
        t_prime_ev=np.asarray([entry["t_prime_ev"] for entry in ph_sets] * 2),
    )

    # T011: two-valley band structure and four-band Wilson spectrum.
    tb8 = TB8TwoValley(
        zeta=paper_parameters["intervalley_zeta"],
        **_tb4_kwargs(tb4_parameters),
    )
    tb8_bands = np.asarray([tb8.eigensystem(momentum)[0] for momentum in tb_path])
    tb8_wilson = wilson_spectrum(
        tb8.eigensystem,
        tb8.embedding_b2(),
        tb8.lattice.b1,
        tb8.lattice.b2,
        4,
        tb_u,
        numeric["tb_wilson_loop_points"],
    )
    _save_npz(
        output_data / TARGET_FILES["T011"],
        path_distance=tb_distance,
        tick_indices=np.asarray(tb_ticks),
        bands=tb8_bands,
        u=tb_u,
        phases=tb8_wilson,
    )

    # T012: projection-method Wannier density and the tuned TB4-2V bands.
    wannier = projected_wannier(
        numeric["wannier_k_grid"],
        numeric["wannier_real_radius"],
        tb4_parameters,
    )
    tb4_two_parameters = paper_parameters.get("tb4_two_valley", {})
    tb4_two = TB4TwoValley(
        delta_minus=float(tb4_two_parameters.get("delta_minus", 0.1174)),
        t_minus=float(tb4_two_parameters.get("t_minus", 0.011)),
        t_prime_minus=float(tb4_two_parameters.get("t_prime_minus", -0.011)),
        lambda_1=float(tb4_two_parameters.get("lambda_1", 0.01842)),
        lambda_2=float(tb4_two_parameters.get("lambda_2", 0.00509)),
    )
    tb4_two_bands = np.asarray(
        [tb4_two.eigensystem(momentum)[0] for momentum in tb_path]
    )
    _save_npz(
        output_data / TARGET_FILES["T012"],
        path_distance=tb_distance,
        tick_indices=np.asarray(tb_ticks),
        bands=tb4_two_bands,
        **wannier,
    )

    # Formula and numerical gates.
    magic_reported = np.asarray(config["paper_parameters"]["reported_magic_alphas"])
    magic_velocity = np.asarray(
        [
            model_for(float(alpha), cache).fermi_velocity(
                float(alpha), numeric["velocity_step"]
            )
            for alpha in magic_reported
        ]
    )
    tb4_gamma = tb4.eigensystem(tb4.lattice.gamma)[0]
    tb4_expected_gamma = np.sort(
        np.array(
            [
                tb4.delta_energy + 3.0 * (tb4.t + tb4.t_prime),
                tb4.delta_energy - 3.0 * (tb4.t + tb4.t_prime),
                -tb4.delta_energy + 3.0 * (tb4.t + tb4.t_prime),
                -tb4.delta_energy - 3.0 * (tb4.t + tb4.t_prime),
            ]
        )
    )
    formula_checks = {
        "schema_version": 1,
        "all_passed": bool(
            np.max(magic_velocity) < 0.012
            and np.max(np.abs(tb4_gamma - tb4_expected_gamma)) < 1.0e-10
            and abs(wannier["det_s_min"] - 15.8) < 0.5
            and abs(wannier["det_s_max"] - 16.0) < 0.5
        ),
        "checks": {
            "reported_magic_velocities": {
                "alphas": magic_reported.tolist(),
                "velocity_over_vf": magic_velocity.tolist(),
                "threshold": 0.012,
                "passed": bool(np.max(magic_velocity) < 0.012),
            },
            "tb4_gamma_analytic": {
                "computed": tb4_gamma.tolist(),
                "expected": tb4_expected_gamma.tolist(),
                "max_abs_error": float(np.max(np.abs(tb4_gamma - tb4_expected_gamma))),
                "passed": bool(
                    np.max(np.abs(tb4_gamma - tb4_expected_gamma)) < 1.0e-10
                ),
            },
            "wannier_projection_overlap": {
                "det_s_min": float(wannier["det_s_min"]),
                "det_s_max": float(wannier["det_s_max"]),
                "paper_interval": [15.8, 16.0],
                "passed": bool(
                    abs(wannier["det_s_min"] - 15.8) < 0.5
                    and abs(wannier["det_s_max"] - 16.0) < 0.5
                ),
            },
            "ph_breaking_labels": {
                "top_theta_deg": np.asarray(ph_theta_deg[:4]).tolist(),
                "bottom_alpha": np.asarray(ph_alpha[4:]).tolist(),
                "passed": bool(
                    np.allclose(
                        ph_theta_deg[:4], [0.967, 1.039, 0.983, 0.994], atol=0.015
                    )
                    and np.allclose(
                        ph_alpha[4:], [0.539, 0.574, 0.548, 0.554], atol=0.006
                    )
                ),
            },
        },
        "node_diagnostics": node_diagnostics,
    }
    formula_checks["all_passed"] = bool(
        formula_checks["all_passed"]
        and formula_checks["checks"]["ph_breaking_labels"]["passed"]
    )

    convergence_entries = []
    for alpha in magic_reported:
        base_cutoff = adaptive_cutoff(float(alpha))
        base = ContinuumModel(base_cutoff).fermi_velocity(
            float(alpha), numeric["velocity_step"]
        )
        refined = ContinuumModel(base_cutoff + 1).fermi_velocity(
            float(alpha), numeric["velocity_step"]
        )
        convergence_entries.append(
            {
                "alpha": float(alpha),
                "base_cutoff": base_cutoff,
                "refined_cutoff": base_cutoff + 1,
                "base_velocity": base,
                "refined_velocity": refined,
                "absolute_delta": abs(refined - base),
            }
        )
    convergence = {
        "schema_version": 1,
        "status": "passed",
        "criterion": "absolute velocity delta below 0.01 at all reported magic alphas",
        "entries": convergence_entries,
        "max_absolute_delta": max(
            entry["absolute_delta"] for entry in convergence_entries
        ),
    }
    if convergence["max_absolute_delta"] >= 0.01:
        convergence["status"] = "failed"

    target_checks = {
        "schema_version": 1,
        "all_passed": bool(
            formula_checks["all_passed"] and convergence["status"] == "passed"
        ),
        "targets": [
            {
                "target_id": target_id,
                "data_path": f"{data_prefix}/{filename}",
                "status": "passed" if (output_data / filename).exists() else "missing",
            }
            for target_id, filename in TARGET_FILES.items()
        ],
    }
    elapsed = perf_counter() - started
    formula_checks["elapsed_seconds"] = elapsed
    (output_checks / "scientific_formula_checks.json").write_text(
        json.dumps(formula_checks, indent=2) + "\n", encoding="utf-8"
    )
    (output_checks / "convergence.json").write_text(
        json.dumps(convergence, indent=2) + "\n", encoding="utf-8"
    )
    (output_checks / "target_checks.json").write_text(
        json.dumps(target_checks, indent=2) + "\n", encoding="utf-8"
    )
    manifest = {
        "schema_version": 1,
        "frozen": True,
        "generated_data_provenance": "independent_numerics",
        "files": [
            {
                "target_id": target_id,
                "path": f"{data_prefix}/{filename}",
                "sha256": _sha256(output_data / filename),
                "bytes": (output_data / filename).stat().st_size,
            }
            for target_id, filename in TARGET_FILES.items()
        ],
    }
    manifest_payload = json.dumps(
        manifest, sort_keys=True, separators=(",", ":")
    ).encode()
    manifest["manifest_sha256"] = hashlib.sha256(manifest_payload).hexdigest()
    (output_checks / "generated_data_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    return ReproductionResult(formula_checks, convergence, target_checks, elapsed)
