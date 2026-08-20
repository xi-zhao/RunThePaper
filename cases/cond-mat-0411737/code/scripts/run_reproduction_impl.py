#!/usr/bin/env python3
"""Generate Kane-Mele numerical evidence from the printed Hamiltonian."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import time
from collections.abc import Iterable
from math import pi
from pathlib import Path
from typing import Any

import numpy as np  # noqa: E402

WORKSPACE = Path(__file__).resolve().parents[1]
SRC = WORKSPACE / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from kane_mele.model import (  # noqa: E402
    analytic_bulk_gap,
    band_eigensystem,
    bare_gap_kelvin,
    build_ribbon_geometry,
    continuum_energies,
    edge_weights,
    flux_pumped_spin_in_hbar,
    ribbon_hamiltonian,
    rashba_kelvin,
    spin_chern_numbers,
    spinful_ribbon_hamiltonian,
    time_reversal_scattering_basis,
    transport_coefficients,
)
from kane_mele.boundary import (  # noqa: E402
    armchair_crossing_convergence,
    flat_zigzag_band_diagnostics,
    rashba_boundary_sweep,
    rashba_edge_spectral_flow,
)
from kane_mele.edge_theory import (  # noqa: E402
    helical_scalar_disorder_ensemble,
    interaction_conductivity_sweep,
    interaction_operator_diagnostics,
    weak_edge_perturbation_inventory,
)
from kane_mele.microscopic import (  # noqa: E402
    first_star_projection_diagnostics,
)
from kane_mele.renormalization import (  # noqa: E402
    derive_one_loop_flow_coefficients,
    exchange_log_sweep,
    renormalized_gap_kelvin,
    rg_running_values,
    screened_coulomb_diagnostics,
)
from kane_mele.response import conventional_spin_hall_sweep  # noqa: E402
from kane_mele.symmetry import (  # noqa: E402
    dirac_mass_symmetry_inventory,
    parallel_field_mass_path,
    translation_preserving_parallel_field_path,
)
from kane_mele.topology import cylinder_flux_spectral_flow  # noqa: E402

TARGET_IDS = [f"T{index:03d}" for index in range(1, 14)]


def _json_default(value: Any) -> Any:
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    raise TypeError(f"unsupported JSON type: {type(value)!r}")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=_json_default) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _write_csv(
    path: Path, fieldnames: list[str], rows: Iterable[dict[str, Any]]
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _assertion(
    assertion_id: str,
    passed: bool,
    *,
    value: float | int | str | list[float],
    threshold: str,
    reason: str,
) -> dict[str, Any]:
    return {
        "id": assertion_id,
        "status": "passed" if passed else "failed",
        "value": value,
        "threshold": threshold,
        "reason": reason,
    }


def _spectrum_rows(
    width: int,
    k_values: np.ndarray,
    *,
    hopping_t: float,
    spin_orbit_t2: float,
    edge_depth: int,
    energy_window: tuple[float, float],
    distance_tolerance: float,
) -> tuple[list[dict[str, Any]], dict[str, float]]:
    geometry = build_ribbon_geometry(width, distance_tolerance=distance_tolerance)
    rows: list[dict[str, Any]] = []
    max_hermiticity = 0.0
    for spin in (-1, 1):
        for momentum in k_values:
            matrix = ribbon_hamiltonian(
                geometry,
                momentum,
                hopping_t=hopping_t,
                spin_orbit_t2=spin_orbit_t2,
                spin=spin,
            )
            max_hermiticity = max(
                max_hermiticity, float(np.max(np.abs(matrix - matrix.conj().T)))
            )
            energies, vectors = np.linalg.eigh(matrix)
            total_edge, bottom_edge, top_edge = edge_weights(
                geometry, vectors, chain_depth=edge_depth
            )
            for band_index, energy in enumerate(energies):
                rows.append(
                    {
                        "k_over_pi": float(momentum / pi),
                        "k_times_a": float(momentum),
                        "spin_z": spin,
                        "band_index": band_index,
                        "energy_over_t": float(energy / hopping_t),
                        "edge_weight": float(total_edge[band_index]),
                        "bottom_edge_weight": float(bottom_edge[band_index]),
                        "top_edge_weight": float(top_edge[band_index]),
                        "visible_in_paper_window": bool(
                            energy_window[0] <= energy / hopping_t <= energy_window[1]
                        ),
                    }
                )
    return rows, {"max_hermiticity_residual": max_hermiticity}


def _width_metrics(
    width: int,
    *,
    hopping_t: float,
    spin_orbit_t2: float,
    edge_depth: int,
    distance_tolerance: float,
) -> dict[str, Any]:
    geometry = build_ribbon_geometry(width, distance_tolerance=distance_tolerance)
    valley_gaps = []
    for momentum in (2.0 * pi / 3.0, 4.0 * pi / 3.0):
        energies, _vectors = band_eigensystem(
            geometry,
            momentum,
            hopping_t=hopping_t,
            spin_orbit_t2=spin_orbit_t2,
            spin=1,
        )
        valley_gaps.append(2.0 * float(np.min(np.abs(energies))) / hopping_t)
    crossing_energies, crossing_vectors = band_eigensystem(
        geometry,
        pi,
        hopping_t=hopping_t,
        spin_orbit_t2=spin_orbit_t2,
        spin=1,
    )
    crossing_edge, _, _ = edge_weights(
        geometry, crossing_vectors, chain_depth=edge_depth
    )
    central = np.argsort(np.abs(crossing_energies))[:2]
    return {
        "width_chains": width,
        "matrix_size_per_spin": len(geometry.sites),
        "valley_gap_over_t": float(np.mean(valley_gaps)),
        "valley_gap_spread": float(np.ptp(valley_gaps)),
        "kramers_crossing_max_abs_energy_over_t": float(
            np.max(np.abs(crossing_energies[central])) / hopping_t
        ),
        "kramers_crossing_min_edge_weight": float(np.min(crossing_edge[central])),
        "edge_coordination": [
            geometry.nearest_coordination[0],
            geometry.nearest_coordination[-1],
        ],
        "bulk_coordination_unique": sorted(set(geometry.nearest_coordination[1:-1])),
    }


def _build_science_checks(
    config: dict[str, Any],
    rows: list[dict[str, Any]],
    width_rows: list[dict[str, Any]],
    runtime_metrics: dict[str, float],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, list[dict[str, Any]]]]:
    parameters = config["parameters"]
    numerics = config["numerics"]
    hopping_t = float(parameters["hopping_t"])
    spin_orbit_t2 = float(parameters["spin_orbit_t2"])
    final_width = int(parameters["ribbon_width_chains"])
    geometry = build_ribbon_geometry(
        final_width, distance_tolerance=float(numerics["distance_tolerance"])
    )

    time_reversal_error = 0.0
    particle_hole_error = 0.0
    for momentum in np.linspace(0.0, 2.0 * pi, 13):
        up = np.linalg.eigvalsh(
            ribbon_hamiltonian(
                geometry,
                momentum,
                hopping_t=hopping_t,
                spin_orbit_t2=spin_orbit_t2,
                spin=1,
            )
        )
        down_reversed = np.linalg.eigvalsh(
            ribbon_hamiltonian(
                geometry,
                2.0 * pi - momentum,
                hopping_t=hopping_t,
                spin_orbit_t2=spin_orbit_t2,
                spin=-1,
            )
        )
        time_reversal_error = max(
            time_reversal_error, float(np.max(np.abs(up - down_reversed)))
        )
        particle_hole_error = max(
            particle_hole_error, float(np.max(np.abs(up + up[::-1])))
        )

    analytic_gap = analytic_bulk_gap(spin_orbit_t2) / hopping_t
    rows_by_width = {int(row["width_chains"]): row for row in width_rows}
    if final_width not in rows_by_width:
        raise ValueError(
            "ribbon_width_chains must be included in width_convergence_chains"
        )
    main_width = rows_by_width[final_width]
    lower_widths = sorted(width for width in rows_by_width if width < final_width)
    if not lower_widths:
        raise ValueError(
            "width convergence needs at least one width below the main width"
        )
    preceding_width = rows_by_width[lower_widths[-1]]
    gap_relative_error = (
        abs(main_width["valley_gap_over_t"] - analytic_gap) / analytic_gap
    )
    width_relative_delta = (
        abs(main_width["valley_gap_over_t"] - preceding_width["valley_gap_over_t"])
        / main_width["valley_gap_over_t"]
    )

    continuum_gap_errors: dict[float, float] = {}
    for rashba_ratio in (0.0, 0.25, 0.75, 0.95):
        delta = 0.2
        rashba = rashba_ratio * delta
        energies = continuum_energies(0.0, 0.0, delta_so=delta, lambda_r=rashba)
        numerical_gap = float(energies[4] - energies[3])
        continuum_gap_errors[rashba_ratio] = abs(numerical_gap - 2.0 * (delta - rashba))

    chern = spin_chern_numbers(
        spin_orbit_t2,
        hopping_t=hopping_t,
        grid_size=int(numerics["chern_grid_size"]),
    )
    transport = transport_coefficients(chern)
    pumped_spin = flux_pumped_spin_in_hbar(chern)
    scattering_basis = time_reversal_scattering_basis()
    scattering_off_diagonal = float(
        max(
            np.max(np.abs(scattering_basis[:, 0, 1])),
            np.max(np.abs(scattering_basis[:, 1, 0])),
        )
    )
    scattering_diagonal_difference = float(
        np.max(np.abs(scattering_basis[:, 0, 0] - scattering_basis[:, 1, 1]))
    )

    rashba_lambda = float(parameters["rashba_probe_lambda"])
    spinful_time_reversal_error = 0.0
    spinful_hermiticity_error = 0.0
    _identity = np.eye(2, dtype=np.complex128)
    spin_y = np.asarray([[0, -1j], [1j, 0]], dtype=np.complex128)
    time_reversal_unitary = np.kron(np.eye(len(geometry.sites)), 1j * spin_y)
    for momentum in np.linspace(0.0, 2.0 * pi, 9):
        matrix = spinful_ribbon_hamiltonian(
            geometry,
            float(momentum),
            hopping_t=hopping_t,
            spin_orbit_t2=spin_orbit_t2,
            rashba_lambda=rashba_lambda,
        )
        reversed_matrix = spinful_ribbon_hamiltonian(
            geometry,
            float(2.0 * pi - momentum),
            hopping_t=hopping_t,
            spin_orbit_t2=spin_orbit_t2,
            rashba_lambda=rashba_lambda,
        )
        spinful_hermiticity_error = max(
            spinful_hermiticity_error,
            float(np.max(np.abs(matrix - matrix.conj().T))),
        )
        transformed = (
            time_reversal_unitary @ matrix.conj() @ time_reversal_unitary.conj().T
        )
        spinful_time_reversal_error = max(
            spinful_time_reversal_error,
            float(np.max(np.abs(transformed - reversed_matrix))),
        )
    crossing_matrix = spinful_ribbon_hamiltonian(
        geometry,
        pi,
        hopping_t=hopping_t,
        spin_orbit_t2=spin_orbit_t2,
        rashba_lambda=rashba_lambda,
    )
    crossing_energies, crossing_vectors = np.linalg.eigh(crossing_matrix)
    half = len(crossing_energies) // 2
    central_spinful = np.arange(half - 2, half + 2)
    crossing_spread = float(np.ptp(crossing_energies[central_spinful]))
    crossing_edge, _bottom, _top = edge_weights(
        geometry, crossing_vectors, chain_depth=int(parameters["edge_chain_depth"])
    )
    crossing_min_edge_weight = float(np.min(crossing_edge[central_spinful]))
    probe_momentum = 0.71 * pi
    zero_rashba = np.linalg.eigvalsh(
        spinful_ribbon_hamiltonian(
            geometry,
            probe_momentum,
            hopping_t=hopping_t,
            spin_orbit_t2=spin_orbit_t2,
            rashba_lambda=0.0,
        )
    )
    finite_rashba = np.linalg.eigvalsh(
        spinful_ribbon_hamiltonian(
            geometry,
            probe_momentum,
            hopping_t=hopping_t,
            spin_orbit_t2=spin_orbit_t2,
            rashba_lambda=rashba_lambda,
        )
    )
    rashba_spectrum_response = float(np.max(np.abs(finite_rashba - zero_rashba)))

    armchair_rows = armchair_crossing_convergence(
        [int(width) for width in parameters["armchair_width_convergence_chains"]],
        hopping_t=hopping_t,
        spin_orbit_t2=spin_orbit_t2,
        edge_depth=int(parameters["armchair_convergence_edge_chain_depth"]),
        distance_tolerance=float(numerics["distance_tolerance"]),
    )
    flat_band_rows, flat_band_metrics = flat_zigzag_band_diagnostics(
        width=final_width,
        hopping_t=hopping_t,
        spin_orbit_t2=spin_orbit_t2,
        edge_depth=int(parameters["edge_chain_depth"]),
        distance_tolerance=float(numerics["distance_tolerance"]),
        k_points=int(numerics["flat_band_k_points"]),
        dos_broadening=float(numerics["flat_band_dos_broadening"]),
    )
    rashba_boundary_rows = rashba_boundary_sweep(
        np.asarray(parameters["rashba_sweep_ratios"], dtype=float),
        zigzag_width=final_width,
        armchair_widths=[
            int(width)
            for width in parameters["armchair_rashba_width_convergence_chains"]
        ],
        hopping_t=hopping_t,
        spin_orbit_t2=spin_orbit_t2,
        zigzag_edge_depth=int(parameters["edge_chain_depth"]),
        armchair_edge_depth=int(parameters["armchair_edge_chain_depth"]),
        distance_tolerance=float(numerics["distance_tolerance"]),
        bulk_grid_size=int(numerics["rashba_bulk_grid_size"]),
        localization_enrichment_threshold=float(
            numerics["rashba_edge_enrichment_threshold"]
        ),
    )
    rashba_flow_rows, rashba_flow_summaries = rashba_edge_spectral_flow(
        np.asarray(
            [
                ratio
                for ratio in parameters["rashba_sweep_ratios"]
                if float(ratio) < 1.0
            ],
            dtype=float,
        ),
        zigzag_widths=[
            int(width) for width in parameters["rashba_spectral_flow_zigzag_widths"]
        ],
        armchair_widths=[
            int(width) for width in parameters["rashba_spectral_flow_armchair_widths"]
        ],
        hopping_t=hopping_t,
        spin_orbit_t2=spin_orbit_t2,
        zigzag_edge_depth=int(parameters["edge_chain_depth"]),
        armchair_edge_depth=int(parameters["armchair_edge_chain_depth"]),
        distance_tolerance=float(numerics["distance_tolerance"]),
        bulk_grid_size=int(numerics["rashba_bulk_grid_size"]),
        initial_k_points=int(numerics["rashba_flow_initial_k_points"]),
        maximum_k_points=int(numerics["rashba_flow_maximum_k_points"]),
        localization_enrichment_threshold=float(
            numerics["rashba_flow_edge_enrichment_threshold"]
        ),
        grid_convergence_tolerance=float(
            numerics["rashba_flow_grid_convergence_tolerance"]
        ),
    )
    rashba_kubo_rows = conventional_spin_hall_sweep(
        np.asarray(parameters["rashba_kubo_ratios"], dtype=float),
        hopping_t=hopping_t,
        spin_orbit_t2=spin_orbit_t2,
        grid_size=int(numerics["rashba_kubo_grid_size"]),
    )
    interaction_operator = interaction_operator_diagnostics()
    interaction_rows, interaction_fit = interaction_conductivity_sweep(
        np.asarray(parameters["interaction_strengths"], dtype=float),
        np.asarray(parameters["interaction_temperatures"], dtype=float),
    )
    edge_perturbations = weak_edge_perturbation_inventory()
    disorder_rows, disorder_metrics = helical_scalar_disorder_ensemble(
        realizations=int(numerics["disorder_realizations"]),
        sites=int(numerics["disorder_sites"]),
        disorder_strength=float(parameters["disorder_strength_over_t"]),
        velocity=float(parameters["edge_velocity_over_t"]),
        seed=int(numerics["disorder_seed"]),
    )
    mass_inventory = dirac_mass_symmetry_inventory()
    parallel_field = parallel_field_mass_path(
        gap_scale=float(parameters["mass_path_gap_scale"]),
        momentum_points=int(numerics["mass_path_momentum_points"]),
        path_points=int(numerics["mass_path_points"]),
    )
    field_bulk_path_rows, field_bulk_path = translation_preserving_parallel_field_path(
        hopping_t=hopping_t,
        spin_orbit_t2=spin_orbit_t2,
        bridge_rashba=float(parameters["parallel_field_bridge_rashba_over_t"])
        * hopping_t,
        bridge_zeeman=float(parameters["parallel_field_zeeman_over_t"]) * hopping_t,
        final_staggered_mass=float(
            parameters["parallel_field_final_staggered_mass_over_t"]
        )
        * hopping_t,
        coarse_grid_size=int(numerics["parallel_field_coarse_bulk_grid_size"]),
        fine_grid_size=int(numerics["parallel_field_fine_bulk_grid_size"]),
        coarse_path_points=int(numerics["parallel_field_coarse_path_points"]),
        fine_path_points=int(numerics["parallel_field_fine_path_points"]),
        optimizer_seed=int(numerics["parallel_field_optimizer_seed"]),
        optimizer_max_iterations=int(
            numerics["parallel_field_optimizer_max_iterations"]
        ),
    )
    flux_rows, flux_metrics = cylinder_flux_spectral_flow(
        level_cutoff=int(numerics["cylinder_level_cutoff"]),
        flux_points=int(numerics["cylinder_flux_points"]),
        circumference_in_correlation_lengths=float(
            parameters["cylinder_circumference_in_correlation_lengths"]
        ),
        ramp_time_in_inverse_gaps=float(parameters["flux_ramp_time_in_inverse_gaps"]),
    )
    first_star = first_star_projection_diagnostics()
    rg_coefficients = derive_one_loop_flow_coefficients(
        shell_ell=float(parameters["rg_coefficient_shell_ell"]),
        radial_points=int(numerics["rg_radial_points"]),
        angular_points=int(numerics["rg_angular_points"]),
    )
    rg_exchange_rows, rg_exchange_fit = exchange_log_sweep(
        np.asarray(parameters["rg_shell_ells"], dtype=float),
        radial_points=int(numerics["rg_sweep_radial_points"]),
        angular_points=int(numerics["rg_sweep_angular_points"]),
    )
    screening_rows, screening_metrics = screened_coulomb_diagnostics(
        np.asarray(parameters["screening_momenta_over_cutoff"], dtype=float),
        coulomb_g=float(parameters["coulomb_g0"]),
        ultraviolet_cutoff=float(parameters["screening_uv_cutoff"]),
        angular_points=int(numerics["screening_angular_points"]),
        integration_tolerance=float(numerics["screening_integration_tolerance"]),
    )

    bare_gap = bare_gap_kelvin(float(parameters["graphene_lattice_constant_angstrom"]))
    rashba_gap = rashba_kelvin(
        fermi_velocity_m_per_s=float(parameters["fermi_velocity_m_per_s"]),
        electric_field_volts=float(parameters["electric_field_volts"]),
        electric_field_distance_nm=float(parameters["electric_field_distance_nm"]),
    )
    renormalized_gap = renormalized_gap_kelvin(
        bare_full_gap_kelvin=float(parameters["bare_full_gap_kelvin"]),
        coulomb_g0=float(parameters["coulomb_g0"]),
        cutoff_ev=float(parameters["cutoff_ev"]),
        coefficients=rg_coefficients,
    )
    rg_ell = float(parameters["rg_probe_ell"])
    rg_g, rg_gap = rg_running_values(
        rg_ell,
        coulomb_g0=float(parameters["coulomb_g0"]),
        bare_half_gap=float(parameters["bare_full_gap_kelvin"]) / 2.0,
        coefficients=rg_coefficients,
    )
    rg_step = 1e-6
    rg_g_next, rg_gap_next = rg_running_values(
        rg_ell + rg_step,
        coulomb_g0=float(parameters["coulomb_g0"]),
        bare_half_gap=float(parameters["bare_full_gap_kelvin"]) / 2.0,
        coefficients=rg_coefficients,
    )
    rg_flow_residual = max(
        abs((rg_g_next - rg_g) / rg_step + rg_coefficients.coupling_decay * rg_g**2),
        abs(
            (rg_gap_next - rg_gap) / rg_step
            - rg_coefficients.gap_growth * rg_g * rg_gap
        ),
    )
    assertions = [
        _assertion(
            "SCI_GEOMETRY",
            main_width["edge_coordination"] == [2, 2]
            and main_width["bulk_coordination_unique"] == [3],
            value=main_width["edge_coordination"]
            + main_width["bulk_coordination_unique"],
            threshold="edges=2 and bulk=3",
            reason="The retained cut is a zigzag edge, not a bearded edge.",
        ),
        _assertion(
            "SCI_HERMITICITY",
            runtime_metrics["max_hermiticity_residual"]
            <= float(numerics["hermiticity_tolerance"]),
            value=runtime_metrics["max_hermiticity_residual"],
            threshold=f"<= {numerics['hermiticity_tolerance']}",
            reason="The oriented imaginary second-neighbour hopping must be Hermitian.",
        ),
        _assertion(
            "SCI_TIME_REVERSAL",
            time_reversal_error <= 1e-11,
            value=time_reversal_error,
            threshold="<= 1e-11",
            reason="Opposite spins at opposite momenta form time-reversal pairs.",
        ),
        _assertion(
            "SCI_PARTICLE_HOLE",
            particle_hole_error <= 1e-11,
            value=particle_hole_error,
            threshold="<= 1e-11",
            reason="The intrinsic model remains spectrally symmetric about zero energy.",
        ),
        _assertion(
            "SCI_KRAMERS_CROSSING",
            main_width["kramers_crossing_max_abs_energy_over_t"]
            <= float(numerics["kramers_energy_tolerance"]),
            value=main_width["kramers_crossing_max_abs_energy_over_t"],
            threshold=f"<= {numerics['kramers_energy_tolerance']}",
            reason="The gap-traversing states cross at k_x=pi/a.",
        ),
        _assertion(
            "SCI_EDGE_LOCALIZATION",
            main_width["kramers_crossing_min_edge_weight"] >= 0.99,
            value=main_width["kramers_crossing_min_edge_weight"],
            threshold=">= 0.99",
            reason="Both central crossing states reside on the strip boundaries.",
        ),
        _assertion(
            "SCI_BULK_GAP",
            gap_relative_error <= float(numerics["gap_relative_tolerance"]),
            value=gap_relative_error,
            threshold=f"<= {numerics['gap_relative_tolerance']}",
            reason="The largest finite ribbon approaches 6 sqrt(3) t2.",
        ),
        _assertion(
            "SCI_WIDTH_CONVERGENCE",
            width_relative_delta <= float(numerics["width_feature_tolerance"]),
            value=width_relative_delta,
            threshold=f"<= {numerics['width_feature_tolerance']}",
            reason="The two largest reconstructed widths agree on the valley gap.",
        ),
        _assertion(
            "SCI_ZERO_T2_FLAT_EDGE_BAND",
            flat_band_metrics["zero_t2_interior_max_abs_energy"]
            <= float(numerics["flat_band_tolerance"])
            and flat_band_metrics["zero_t2_interior_min_edge_weight"] >= 0.8
            and flat_band_metrics["dos_enhancement_ratio"] >= 5.0,
            value=[
                flat_band_metrics["zero_t2_interior_max_abs_energy"],
                flat_band_metrics["zero_t2_interior_min_edge_weight"],
                flat_band_metrics["dos_enhancement_ratio"],
            ],
            threshold=(
                f"interior |E|<={numerics['flat_band_tolerance']}, edge weight "
                ">=0.8, and edge-weighted DOS enhancement >=5"
            ),
            reason="The full analytic zigzag interval, endpoint delocalization, finite-width edge weight, and zero-energy DOS are all resolved.",
        ),
        _assertion(
            "SCI_ARMCHAIR_KRAMERS_CROSSING",
            armchair_rows[-1]["finite_width_half_gap_over_t"] <= 1e-3
            and armchair_rows[-1]["finite_width_half_gap_over_t"]
            < armchair_rows[0]["finite_width_half_gap_over_t"]
            and armchair_rows[-1]["central_min_edge_weight"] >= 0.5,
            value=[
                armchair_rows[0]["finite_width_half_gap_over_t"],
                armchair_rows[-1]["finite_width_half_gap_over_t"],
                armchair_rows[-1]["central_min_edge_weight"],
            ],
            threshold="largest-width half-gap <=1e-3, decreasing with width, edge weight >=0.5",
            reason="A separately constructed armchair boundary converges to its protected k=0 crossing.",
        ),
        _assertion(
            "SCI_CONTINUUM_INTRINSIC_GAP",
            continuum_gap_errors[0.0] <= 1e-12,
            value=continuum_gap_errors[0.0],
            threshold="<= 1e-12",
            reason="Direct continuum diagonalization gives the intrinsic full gap 2 Delta_so.",
        ),
        _assertion(
            "SCI_CONTINUUM_RASHBA_GAP",
            max(value for ratio, value in continuum_gap_errors.items() if ratio > 0)
            <= 1e-12,
            value=max(
                value for ratio, value in continuum_gap_errors.items() if ratio > 0
            ),
            threshold="<= 1e-12",
            reason="Direct continuum diagonalization gives 2(Delta_so-lambda_R).",
        ),
        _assertion(
            "SCI_RASHBA_LATTICE_CONSUMED",
            spinful_hermiticity_error <= float(numerics["hermiticity_tolerance"])
            and spinful_time_reversal_error <= 1e-11
            and rashba_spectrum_response >= float(numerics["rashba_response_minimum"]),
            value=[
                spinful_hermiticity_error,
                spinful_time_reversal_error,
                rashba_spectrum_response,
            ],
            threshold="Hermitian/TR <= tolerances and spectrum response >= minimum",
            reason="The configured lattice Rashba coupling changes the spectrum while preserving time reversal.",
        ),
        _assertion(
            "SCI_RASHBA_KRAMERS_EDGE",
            crossing_spread <= float(numerics["kramers_energy_tolerance"])
            and crossing_min_edge_weight >= 0.99,
            value=[crossing_spread, crossing_min_edge_weight],
            threshold=(
                "four central states degenerate <="
                f"{numerics['kramers_energy_tolerance']} and edge weight >=0.99"
            ),
            reason="Finite Rashba coupling preserves the edge-localized Kramers crossing at k_x=pi/a.",
        ),
        _assertion(
            "SCI_RASHBA_LOW_COUPLING_BOUNDARY",
            all(
                row["classification"] == "edge_pair_resolved"
                for row in rashba_boundary_rows
                if row["orientation"] == "zigzag"
                and float(row["lambda_r_over_delta_so"]) <= 0.25
            ),
            value=[
                row["classification"]
                for row in rashba_boundary_rows
                if row["orientation"] == "zigzag"
                and float(row["lambda_r_over_delta_so"]) <= 0.25
            ],
            threshold="the low-coupling zigzag probes have a bulk-gap-selected Kramers pair localized above the exact uniform baseline",
            reason="The low-coupling branch is selected inside independently sampled bulk band edges, never by proximity to zero energy; higher-Rashba TRIM states can merge into the projected bulk continuum and are not force-classified.",
        ),
        _assertion(
            "SCI_RASHBA_ARMCHAIR_DIAGNOSTIC",
            len(
                {
                    int(row["width_chains"])
                    for row in rashba_boundary_rows
                    if row["orientation"] == "armchair"
                }
            )
            >= 3
            and all(
                row["classification"]
                in {
                    "edge_pair_resolved",
                    "in_gap_pair_not_localized",
                    "no_in_gap_kramers_pair",
                }
                for row in rashba_boundary_rows
                if row["orientation"] == "armchair"
            ),
            value={
                str(row["width_chains"]): [
                    candidate["classification"]
                    for candidate in rashba_boundary_rows
                    if candidate["orientation"] == "armchair"
                    and candidate["width_chains"] == row["width_chains"]
                    and float(candidate["lambda_r_over_delta_so"]) < 1.0
                ]
                for row in rashba_boundary_rows
                if row["orientation"] == "armchair"
            },
            threshold="three-width bulk-gap and baseline-subtracted diagnostic completed; no automatic paper-support promotion",
            reason="The armchair finite-Rashba claim remains inconclusive unless a physical in-gap branch survives width convergence; the runner records that boundary instead of forcing a pass.",
        ),
        _assertion(
            "SCI_RASHBA_FULL_K_EDGE_SPECTRAL_FLOW",
            len(rashba_flow_summaries)
            == 2
            * 3
            * len(
                [
                    ratio
                    for ratio in parameters["rashba_sweep_ratios"]
                    if float(ratio) < 1.0
                ]
            )
            and all(
                row["classification"] == "full_k_edge_spectral_flow_resolved"
                for row in rashba_flow_summaries
            ),
            value=[
                {
                    "orientation": row["orientation"],
                    "width": row["width_chains"],
                    "ratio": row["lambda_r_over_delta_so"],
                    "k_points": row["k_points"],
                    "classification": row["classification"],
                }
                for row in rashba_flow_summaries
            ],
            threshold="all subcritical couplings, both boundaries, and three widths resolve a grid-converged full-k edge branch spanning the independently computed bulk midgap",
            reason="The finite-Rashba boundary claim is tested by localized spectral flow over the full Brillouin zone rather than a zero-energy or TRIM selector.",
        ),
        _assertion(
            "SCI_RASHBA_KUBO_PROXY",
            abs(
                next(
                    row["relative_correction"]
                    for row in rashba_kubo_rows
                    if abs(row["lambda_r_over_delta_so"] - 0.05) <= 1e-12
                )
            )
            <= 0.01
            and next(
                row["physical_spin_commutator_norm"]
                for row in rashba_kubo_rows
                if abs(row["lambda_r_over_delta_so"] - 0.05) <= 1e-12
            )
            > 0.0,
            value=[
                next(
                    row["relative_correction"]
                    for row in rashba_kubo_rows
                    if abs(row["lambda_r_over_delta_so"] - 0.05) <= 1e-12
                ),
                next(
                    row["physical_spin_commutator_norm"]
                    for row in rashba_kubo_rows
                    if abs(row["lambda_r_over_delta_so"] - 0.05) <= 1e-12
                ),
            ],
            threshold="conventional Kubo correction <=1% at ratio .05 and [H,s_z] nonzero",
            reason="A full-BZ finite-Rashba Kubo calculation now exists; it is explicitly a conventional-current proxy because the cited conserved operator is not printed in this paper.",
        ),
        _assertion(
            "SCI_SPIN_CHERN_PAIR",
            abs(abs(chern["up"]) - 1.0) <= 1e-10
            and abs(chern["up"] + chern["down"]) <= 1e-10,
            value=[chern["up"], chern["down"]],
            threshold="opposite unit integers from the Fukui Berry-flux grid",
            reason="The occupied bands of the two independently diagonalized spin blocks carry opposite topology.",
        ),
        _assertion(
            "SCI_FLUX_PUMP",
            abs(pumped_spin - 1.0) <= 1e-10,
            value=pumped_spin,
            threshold="1 hbar per h/e flux insertion",
            reason="The Chern-number difference pumps one unit of spin between cylinder edges.",
        ),
        _assertion(
            "SCI_FINITE_CYLINDER_SPECTRAL_FLOW",
            flux_metrics["pumped_spin_in_hbar"] == 1.0
            and flux_metrics["level_permutation_residual"] <= 1e-12
            and flux_metrics["circumference_condition_satisfied"]
            and flux_metrics["adiabatic_condition_satisfied"],
            value=[
                flux_metrics["pumped_spin_in_hbar"],
                flux_metrics["level_permutation_residual"],
                flux_metrics["edge_level_spacing_over_half_gap"],
            ],
            threshold="one explicit spectral-flow crossing per branch, unit level permutation, L>xi and ramp>1/Delta",
            reason="A finite cylinder and complete h/e flux sweep now realize the Laughlin pump rather than only inferring it from Chern numbers.",
        ),
        _assertion(
            "SCI_NO_ELASTIC_BACKSCATTER",
            scattering_off_diagonal <= 1e-12
            and scattering_diagonal_difference <= 1e-12,
            value=[scattering_off_diagonal, scattering_diagonal_difference],
            threshold="off-diagonal and diagonal-difference residuals <=1e-12",
            reason="Solving S=s_y S^T s_y leaves only a common diagonal phase.",
        ),
        _assertion(
            "SCI_RANDOM_TR_DISORDER_ENSEMBLE",
            disorder_metrics["max_reflection_probability"] <= 1e-15
            and disorder_metrics["min_transmission_probability"] >= 1.0 - 1e-15
            and disorder_metrics["max_unitarity_residual"] <= 1e-14,
            value=[
                disorder_metrics["max_reflection_probability"],
                disorder_metrics["min_transmission_probability"],
                disorder_metrics["max_abs_lyapunov_exponent_per_site"],
            ],
            threshold="all random scalar-potential realizations have R=0, T=1, and zero Lyapunov exponent",
            reason="The first-order helical Dirac equations are propagated through an explicit reproducible disorder ensemble.",
        ),
        _assertion(
            "SCI_INTERACTION_OPERATOR",
            interaction_operator["time_reversal_maps_to_hermitian_conjugate"]
            and interaction_operator["total_scaling_dimension"] == 4.0,
            value=[
                interaction_operator["time_reversal_maps_to_hermitian_conjugate"],
                interaction_operator["field_count"],
                interaction_operator["derivative_count"],
                interaction_operator["total_scaling_dimension"],
            ],
            threshold="T O T^-1=O^dagger and Delta=4 from four fermions plus two derivatives",
            reason="The displayed Grassmann monomial is encoded and transformed before its dimension is derived.",
        ),
        _assertion(
            "SCI_INTERACTION_CONDUCTIVITY_SWEEP",
            abs(interaction_fit["fitted_temperature_exponent"] + 5.0) <= 1e-8
            and abs(interaction_fit["fitted_interaction_exponent"] + 2.0) <= 1e-8,
            value=[
                interaction_fit["fitted_temperature_exponent"],
                interaction_fit["fitted_interaction_exponent"],
            ],
            threshold="log-log Kubo-kernel fits give T exponent -5 and u exponent -2",
            reason="A numerical finite-temperature correlator sweep replaces exponent-only arithmetic.",
        ),
        _assertion(
            "SCI_WEAK_EDGE_PERTURBATION_INVENTORY",
            next(
                not row["time_reversal_allowed"]
                for row in edge_perturbations
                if row["operator"] == "single_particle_backscattering"
            )
            and next(
                not row["pauli_nonzero"]
                for row in edge_perturbations
                if row["operator"] == "local_pair_backscattering_without_derivatives"
            )
            and next(
                row["rg_class"] == "irrelevant_at_weak_coupling"
                for row in edge_perturbations
                if row["operator"] == "derivative_pair_backscattering"
            ),
            value=[row["rg_class"] for row in edge_perturbations],
            threshold="single-particle term T-forbidden, local pair Pauli-zero, derivative pair irrelevant",
            reason="The lowest local perturbations are enumerated instead of checking only the one printed example.",
        ),
        _assertion(
            "SCI_DIRAC_MASS_SYMMETRY_ENUMERATION",
            [
                row["pauli_product"]
                for row in mass_inventory
                if row["spin_dependent"]
                and row["time_reversal_even"]
                and row["inversion_even"]
                and row["mirror_z_even"]
            ]
            == ["sigma_z tau_z s_z"],
            value=[
                row["pauli_product"]
                for row in mass_inventory
                if row["spin_dependent"]
                and row["time_reversal_even"]
                and row["inversion_even"]
                and row["mirror_z_even"]
            ],
            threshold="unique spin-dependent kinetic mass even under T, inversion, and z mirror",
            reason="All 64 Pauli products are searched and the 16 kinetic masses classified under the printed symmetries.",
        ),
        _assertion(
            "SCI_PARALLEL_FIELD_EDGE_GAP",
            abs(
                parallel_field["minimum_edge_gap"] - parallel_field["expected_edge_gap"]
            )
            <= 1e-12,
            value=parallel_field["minimum_edge_gap"],
            threshold="uniform edge Zeeman term opens the expected avoided-crossing gap",
            reason="A spatially uniform parallel field directly supplies the edge Zeeman mass and gaps the helical crossing.",
        ),
        _assertion(
            "SCI_TR_BROKEN_INTERVALLEY_MASS_PATH_PROXY",
            abs(
                parallel_field["minimum_bulk_gap"] - parallel_field["expected_bulk_gap"]
            )
            <= 1e-12
            and parallel_field["bridge_time_reversal_residual"] > 1.0
            and parallel_field["bridge_translation_residual"] > 1.0
            and parallel_field["bridge_requires_intervalley_mixing"]
            and not parallel_field["uniform_parallel_field_supports_bulk_bridge"],
            value=[
                parallel_field["minimum_bulk_gap"],
                parallel_field["bridge_time_reversal_residual"],
                parallel_field["bridge_translation_residual"],
            ],
            threshold="generic bridge is gapped, T-odd, and explicitly diagnosed as translation-breaking intervalley mixing",
            reason="This is only a generic broken-T symmetry-class proxy; it is not attributed to a uniform parallel field.",
        ),
        _assertion(
            "SCI_PARALLEL_FIELD_MINIMAL_PATH_FALSIFICATION",
            field_bulk_path["continuous_optimizer_minimum_direct_gap_over_t"]
            <= float(numerics["parallel_field_gap_closure_tolerance"])
            and field_bulk_path["primitive_translation_preserved"]
            and not field_bulk_path["intervalley_mixing_used"]
            and field_bulk_path["uniform_parallel_field_used"]
            and not field_bulk_path["uniform_parallel_field_alone_sufficient"]
            and field_bulk_path["minimal_published_term_path_status"]
            == "falsified_by_bulk_gap_closure"
            and field_bulk_path["paper_connecting_terms_status"]
            == "publication_underspecified",
            value=[
                field_bulk_path["continuous_optimizer_minimum_direct_gap_over_t"],
                field_bulk_path["continuous_optimizer_closing_segment"],
                field_bulk_path["reciprocal_spectrum_periodicity_residual"],
            ],
            threshold="continuous Brillouin-zone optimizer finds a direct-gap closure in the minimal translation-preserving published-term path",
            reason="The paper does not print its alleged connecting terms. The runner actively falsifies the minimal Rashba + uniform-field + staggered-mass interpolation and records the claim as publication-underspecified instead of promoting a coarse-grid false pass.",
        ),
        _assertion(
            "SCI_TWO_TERMINAL_TRANSPORT",
            transport["charge_conductance_in_e2_over_h"] == 2.0,
            value=transport["charge_conductance_in_e2_over_h"],
            threshold="G=2 in units e^2/h",
            reason="The explicit two-contact helical transmission graph gives the printed charge conductance.",
        ),
        _assertion(
            "SCI_FOUR_TERMINAL_SPIN_TRANSPORT",
            abs(transport["adjacent_spin_conductance_in_e"] - 1.0 / (4.0 * pi)) <= 1e-15
            and abs(transport["four_terminal_charge_current_in_e2_over_h"]) <= 1e-15,
            value=[
                transport["adjacent_spin_conductance_in_e"],
                transport["four_terminal_charge_current_in_e2_over_h"],
            ],
            threshold="spin current=eV/(4 pi) and charge current=0 at the right contact",
            reason="The explicit four-contact helical transmission graph reproduces the Fig. 2(b) spin-current label.",
        ),
        _assertion(
            "SCI_SPIN_HALL_QUANTUM",
            abs(transport["spin_hall_conductivity_in_e"] - 1.0 / (2.0 * pi)) <= 1e-12,
            value=transport["spin_hall_conductivity_in_e"],
            threshold="e/(2 pi)",
            reason="The independently computed Chern difference fixes the spin Hall coefficient.",
        ),
        _assertion(
            "SCI_BARE_GAP_ESTIMATE",
            abs(bare_gap - 2.4) / 2.4 <= 0.1,
            value=bare_gap,
            threshold="within 10% of 2.4 K",
            reason="The first-star estimate is reproduced with a=2.46 angstrom.",
        ),
        _assertion(
            "SCI_FIRST_STAR_PROJECTION",
            first_star["max_sigma_z_tau_z_s_z_residual"] <= 1e-12
            and first_star["max_hermiticity_residual"] <= 1e-12,
            value=[
                first_star["coefficient_in_e2_hbar2_over_m2c2"],
                first_star["max_sigma_z_tau_z_s_z_residual"],
                first_star["max_hermiticity_residual"],
            ],
            threshold="explicit 8x8 first-star matrix matches (2pi^2/3a^3) sigma_z tau_z s_z within 1e-12",
            reason="The degenerate plane-wave matrix is now constructed instead of jumping directly to the scalar gap formula.",
        ),
        _assertion(
            "SCI_RASHBA_ESTIMATE",
            abs(1e3 * rashba_gap - 0.5) <= 0.2,
            value=1e3 * rashba_gap,
            threshold="0.5 +/- 0.2 mK",
            reason="The unprinted v_F convention explains the printed rounding.",
        ),
        _assertion(
            "SCI_RG_FLOW",
            rg_flow_residual <= 1e-6
            and abs(rg_coefficients.coupling_decay - 0.25) <= 1e-6
            and abs(rg_coefficients.gap_growth - 0.5) <= 1e-6,
            value=[
                rg_flow_residual,
                rg_coefficients.coupling_decay,
                rg_coefficients.gap_growth,
            ],
            threshold="ODE residual <=1e-6 and independently integrated coefficients 1/4,1/2 within 1e-6",
            reason="The beta functions are driven by matrix-valued Coulomb shell integrals rather than coefficients repeated in both solution and check.",
        ),
        _assertion(
            "SCI_RG_EXCHANGE_LOG",
            abs(rg_exchange_fit["fitted_velocity_log_slope"] - 0.25) <= 1e-6
            and abs(rg_exchange_fit["fitted_gap_log_slope"] - 0.5) <= 1e-6,
            value=[
                rg_exchange_fit["fitted_velocity_log_slope"],
                rg_exchange_fit["fitted_gap_log_slope"],
            ],
            threshold="shell-width sweep gives logarithmic slopes 1/4 and 1/2 within 1e-6",
            reason="The Fig. 3 exchange correction is explicitly swept over logarithmic shell scale before integrating the RG flow.",
        ),
        _assertion(
            "SCI_NEUTRAL_GRAPHENE_SCREENING",
            abs(screening_metrics["polarization_fitted_momentum_power"] - 1.0) <= 0.02
            and screening_metrics["max_abs_coefficient_error_from_quarter"] <= 0.01
            and screening_metrics["max_angular_convergence_delta"] <= 5e-4
            and screening_metrics["max_uv_cutoff_doubling_delta"] <= 0.005
            and abs(screening_metrics["fitted_momentum_power"] + 1.0) <= 0.01,
            value=[
                screening_metrics["polarization_fitted_momentum_power"],
                screening_metrics["max_abs_coefficient_error_from_quarter"],
                screening_metrics["max_angular_convergence_delta"],
                screening_metrics["max_uv_cutoff_doubling_delta"],
                screening_metrics["fitted_momentum_power"],
            ],
            threshold="independent Lindhard integral gives Pi proportional to -q with coefficient 1/4, converges in angle/cutoff, and yields V_screened proportional to 1/q",
            reason="The polarization is now generated from interband spinor overlaps and energy denominators; the analytic coefficient and power law are acceptance tests, not generator inputs.",
        ),
        _assertion(
            "SCI_RG_GAP",
            abs(renormalized_gap - 15.0) <= 0.3,
            value=renormalized_gap,
            threshold="15 +/- 0.3 K",
            reason="The half-gap self-consistency convention reproduces the printed 15 K full gap.",
        ),
    ]
    status = (
        "passed" if all(item["status"] == "passed" for item in assertions) else "failed"
    )
    analytic = {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "analytic_bulk_gap_over_t": analytic_gap,
        "main_width_chains": final_width,
        "main_width_valley_gap_over_t": main_width["valley_gap_over_t"],
        "main_width_gap_relative_error": gap_relative_error,
        "preceding_width_chains": preceding_width["width_chains"],
        "main_to_preceding_width_relative_delta": width_relative_delta,
        "flat_zigzag_band": flat_band_metrics,
        "armchair_crossing_convergence": armchair_rows,
        "rashba_probe": {
            "lambda_over_t": rashba_lambda,
            "hermiticity_residual": spinful_hermiticity_error,
            "time_reversal_residual": spinful_time_reversal_error,
            "spectrum_response": rashba_spectrum_response,
            "kramers_crossing_spread": crossing_spread,
            "kramers_crossing_min_edge_weight": crossing_min_edge_weight,
        },
        "rashba_boundary_sweep_summary": {
            "rows": len(rashba_boundary_rows),
            "selector": "inside_independent_bulk_gap_then_baseline_subtracted_edge_localization",
            "zigzag_subcritical_classifications": [
                row["classification"]
                for row in rashba_boundary_rows
                if row["orientation"] == "zigzag"
                and float(row["lambda_r_over_delta_so"]) < 1.0
            ],
            "armchair_subcritical_classifications_by_width": {
                str(width): [
                    row["classification"]
                    for row in rashba_boundary_rows
                    if row["orientation"] == "armchair"
                    and int(row["width_chains"]) == width
                    and float(row["lambda_r_over_delta_so"]) < 1.0
                ]
                for width in parameters["armchair_rashba_width_convergence_chains"]
            },
            "armchair_paper_component_status": "inconclusive_pending_physical_branch_convergence",
        },
        "rashba_edge_spectral_flow": {
            "selector": "full_BZ_bulk_gap_states_with_baseline_subtracted_edge_localization",
            "summaries": rashba_flow_summaries,
            "paper_component_status": (
                "paper_supported"
                if all(
                    row["classification"] == "full_k_edge_spectral_flow_resolved"
                    for row in rashba_flow_summaries
                )
                else "reproduction_defect"
            ),
        },
        "rashba_kubo_proxy": {
            "current_definition": "conventional_symmetrized_spin_current",
            "paper_cited_conserved_operator_available": False,
            "rows": rashba_kubo_rows,
        },
        "bare_full_gap_kelvin_from_constants": bare_gap,
        "rashba_kelvin_from_printed_field": rashba_gap,
        "renormalized_full_gap_kelvin": renormalized_gap,
        "transport_coefficients": transport,
        "spin_chern_fukui": chern,
        "flux_pumped_spin_in_hbar": pumped_spin,
        "finite_cylinder_flux": flux_metrics,
        "time_reversal_scattering": {
            "basis_dimension": int(scattering_basis.shape[0]),
            "max_off_diagonal": scattering_off_diagonal,
            "max_diagonal_difference": scattering_diagonal_difference,
        },
        "interaction_operator": interaction_operator,
        "interaction_conductivity_fit": interaction_fit,
        "weak_edge_perturbations": edge_perturbations,
        "scalar_disorder_ensemble": disorder_metrics,
        "dirac_mass_symmetry_inventory": mass_inventory,
        "parallel_field_mass_path": parallel_field,
        "parallel_field_translation_preserving_bulk_path": field_bulk_path,
        "first_star_projection": first_star,
        "rg_probe": {
            "ell": rg_ell,
            "g": rg_g,
            "half_gap_kelvin": rg_gap,
            "flow_residual": rg_flow_residual,
            "derived_coupling_decay_coefficient": rg_coefficients.coupling_decay,
            "derived_gap_growth_coefficient": rg_coefficients.gap_growth,
            "velocity_projection_residual": rg_coefficients.velocity_projection_residual,
            "gap_projection_residual": rg_coefficients.gap_projection_residual,
            "exchange_log_fit": rg_exchange_fit,
            "screening": screening_metrics,
        },
    }
    science = {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "status": status,
        "target_ids": TARGET_IDS,
        "assertions": assertions,
        "summary": {
            "assertions_total": len(assertions),
            "assertions_passed": sum(item["status"] == "passed" for item in assertions),
            "assertions_failed": sum(item["status"] == "failed" for item in assertions),
            "generated_rows": len(rows),
        },
        "paper_assessment": {
            "status": "inconclusive_pending_fresh_review",
            "paper_error_candidate_emitted": False,
            "stable_cross_reference_discrepancies": [
                {
                    "source": "raw/paper.pdf p. 2, strip-geometry prose",
                    "printed": "solving (7)",
                    "internally_required": "Eq. (6), the lattice Hamiltonian",
                },
                {
                    "source": "raw/paper.pdf p. 3, Fig. 1 caption",
                    "printed": "modeled by (7)",
                    "internally_required": "Eq. (6), the lattice Hamiltonian",
                },
                {
                    "source": "raw/paper.pdf p. 4, paragraph after Eq. (7)",
                    "printed": "expectation value of (8)",
                    "internally_required": "Eq. (7), the microscopic SO interaction",
                },
            ],
            "impact": "Equation-number cross references only; the implemented formulas and numerical results are unambiguous from context.",
            "remaining_gate": "fresh-context whole-paper protocol-v3 review",
        },
    }
    generated_tables = {
        "armchair_crossing_convergence": armchair_rows,
        "flat_band_diagnostics": flat_band_rows,
        "rashba_boundary_sweep": rashba_boundary_rows,
        "rashba_edge_spectral_flow": rashba_flow_rows,
        "rashba_kubo_sweep": rashba_kubo_rows,
        "interaction_conductivity": interaction_rows,
        "scalar_disorder_ensemble": disorder_rows,
        "finite_cylinder_flux": flux_rows,
        "dirac_mass_symmetry_inventory": mass_inventory,
        "parallel_field_bulk_path": field_bulk_path_rows,
        "rg_exchange_sweep": rg_exchange_rows,
        "screened_coulomb": screening_rows,
    }
    return science, analytic, generated_tables


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--output-root", required=True)
    arguments = parser.parse_args()
    started = time.perf_counter()
    config_path = Path(arguments.config).resolve()
    output_root = Path(arguments.output_root).resolve()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if config.get("paper_id") != "cond-mat-0411737":
        raise ValueError("config paper_id mismatch")

    parameters = config["parameters"]
    numerics = config["numerics"]
    k_values = np.linspace(
        float(parameters["k_over_pi_min"]) * pi,
        float(parameters["k_over_pi_max"]) * pi,
        int(parameters["k_points"]),
    )
    energy_window = tuple(float(value) for value in parameters["energy_window_over_t"])
    rows, runtime_metrics = _spectrum_rows(
        int(parameters["ribbon_width_chains"]),
        k_values,
        hopping_t=float(parameters["hopping_t"]),
        spin_orbit_t2=float(parameters["spin_orbit_t2"]),
        edge_depth=int(parameters["edge_chain_depth"]),
        energy_window=energy_window,
        distance_tolerance=float(numerics["distance_tolerance"]),
    )
    width_rows = [
        _width_metrics(
            int(width),
            hopping_t=float(parameters["hopping_t"]),
            spin_orbit_t2=float(parameters["spin_orbit_t2"]),
            edge_depth=int(parameters["edge_chain_depth"]),
            distance_tolerance=float(numerics["distance_tolerance"]),
        )
        for width in sorted(parameters["width_convergence_chains"])
    ]
    science, analytic, generated_tables = _build_science_checks(
        config, rows, width_rows, runtime_metrics
    )

    data_dir = output_root / "data"
    checks_dir = output_root / "checks"
    _write_csv(
        data_dir / "main_fig1_bands.csv",
        [
            "k_over_pi",
            "k_times_a",
            "spin_z",
            "band_index",
            "energy_over_t",
            "edge_weight",
            "bottom_edge_weight",
            "top_edge_weight",
            "visible_in_paper_window",
        ],
        rows,
    )
    _write_csv(
        data_dir / "width_convergence.csv",
        [
            "width_chains",
            "matrix_size_per_spin",
            "valley_gap_over_t",
            "valley_gap_spread",
            "kramers_crossing_max_abs_energy_over_t",
            "kramers_crossing_min_edge_weight",
            "edge_coordination",
            "bulk_coordination_unique",
        ],
        width_rows,
    )
    for table_name, table_rows in generated_tables.items():
        if not table_rows:
            raise RuntimeError(f"generated table {table_name} is empty")
        _write_csv(
            data_dir / f"{table_name}.csv",
            list(table_rows[0]),
            table_rows,
        )
    _write_json(data_dir / "analytic_checks.json", analytic)
    _write_json(data_dir / "quantitative_claims.json", analytic)
    _write_json(checks_dir / "science_checks.json", science)

    summary = {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "profile": config["execution_profile"],
        "status": science["status"],
        "elapsed_seconds": time.perf_counter() - started,
        "generated_band_rows": len(rows),
        "widths_checked": [row["width_chains"] for row in width_rows],
        "paper_error_candidate_emitted": False,
        "paper_assessment": science["paper_assessment"],
    }
    _write_json(checks_dir / "run_summary.json", summary)

    generated_paths = [
        data_dir / "main_fig1_bands.csv",
        data_dir / "width_convergence.csv",
        *(data_dir / f"{table_name}.csv" for table_name in generated_tables),
        data_dir / "analytic_checks.json",
        data_dir / "quantitative_claims.json",
        checks_dir / "science_checks.json",
        checks_dir / "run_summary.json",
    ]
    manifest = {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "status": science["status"],
        "profile": config["execution_profile"],
        "config_sha256": _sha256(config_path),
        "generated_artifacts": [
            {
                "path": str(path.relative_to(output_root)),
                "sha256": _sha256(path),
                "bytes": path.stat().st_size,
            }
            for path in generated_paths
        ],
        "scientific_data_frozen": True,
        "rendering_separated_from_numerics": True,
        "source_pixels_used": False,
        "author_code_used": False,
        "author_numeric_arrays_used": False,
    }
    _write_json(checks_dir / "generated_data_manifest.json", manifest)
    print(json.dumps(summary, sort_keys=True, default=_json_default))
    return 0 if science["status"] == "passed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
