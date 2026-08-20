"""Pauli-basis symmetry enumeration and a time-reversal-breaking mass path."""

from __future__ import annotations

from itertools import product
from math import pi
from typing import Any

import numpy as np
from scipy.optimize import differential_evolution

from .response import spinful_honeycomb_bulk_hamiltonian


def _pauli_basis() -> tuple[list[str], list[np.ndarray]]:
    identity = np.eye(2, dtype=np.complex128)
    sigma_x = np.asarray([[0, 1], [1, 0]], dtype=np.complex128)
    sigma_y = np.asarray([[0, -1j], [1j, 0]], dtype=np.complex128)
    sigma_z = np.asarray([[1, 0], [0, -1]], dtype=np.complex128)
    return ["I", "x", "y", "z"], [identity, sigma_x, sigma_y, sigma_z]


def _operator(indices: tuple[int, int, int]) -> np.ndarray:
    _names, matrices = _pauli_basis()
    return np.kron(
        np.kron(matrices[indices[0]], matrices[indices[1]]), matrices[indices[2]]
    )


def _is_close(first: np.ndarray, second: np.ndarray, tolerance: float = 1e-12) -> bool:
    return bool(np.max(np.abs(first - second)) <= tolerance)


def dirac_mass_symmetry_inventory() -> list[dict[str, bool | str]]:
    """Enumerate every Pauli product that anticommutes with both kinetic terms."""

    names, matrices = _pauli_basis()
    gamma_x = _operator((1, 3, 0))
    gamma_y = _operator((2, 0, 0))
    time_reversal = np.kron(np.kron(matrices[0], matrices[1]), 1j * matrices[2])
    inversion = np.kron(np.kron(matrices[1], matrices[1]), matrices[0])
    mirror_z = np.kron(np.kron(matrices[0], matrices[0]), 1j * matrices[3])
    rows: list[dict[str, bool | str]] = []
    for indices in product(range(4), repeat=3):
        candidate = _operator(indices)
        if not _is_close(gamma_x @ candidate + candidate @ gamma_x, 0.0 * candidate):
            continue
        if not _is_close(gamma_y @ candidate + candidate @ gamma_y, 0.0 * candidate):
            continue
        rows.append(
            {
                "pauli_product": "sigma_"
                + names[indices[0]]
                + " tau_"
                + names[indices[1]]
                + " s_"
                + names[indices[2]],
                "spin_dependent": indices[2] != 0,
                "time_reversal_even": _is_close(
                    time_reversal @ candidate.conj() @ time_reversal.conj().T,
                    candidate,
                ),
                "inversion_even": _is_close(
                    inversion @ candidate @ inversion.conj().T, candidate
                ),
                "mirror_z_even": _is_close(
                    mirror_z @ candidate @ mirror_z.conj().T, candidate
                ),
            }
        )
    return rows


def parallel_field_mass_path(
    *, gap_scale: float = 1.0, momentum_points: int = 81, path_points: int = 81
) -> dict[str, bool | float | int | str]:
    """Separate the uniform-field edge gap from an intervalley bulk proxy.

    ``C=sigma_x tau_x s_x`` gives a mathematically valid T-odd bridge, but its
    ``tau_x`` factor mixes valleys and therefore breaks primitive translation.
    A spatially uniform parallel field supplies the edge Zeeman mass ``s_x``;
    it does *not* by itself establish this bulk bridge.  Returning both facts
    prevents a generic symmetry-class interpolation from being misattributed
    to the experimental field.
    """

    if gap_scale <= 0 or momentum_points < 11 or path_points < 11:
        raise ValueError("positive gap and resolved momentum/path grids required")
    gamma_x = _operator((1, 3, 0))
    qsh_mass = _operator((3, 3, 3))
    trivial_mass = _operator((3, 0, 0))
    bridge_mass = _operator((1, 1, 1))
    momenta = np.linspace(-2.0 * gap_scale, 2.0 * gap_scale, momentum_points)
    angles = np.linspace(0.0, pi / 2.0, path_points)
    minimum_gap = float("inf")
    for start_mass, end_mass in (
        (qsh_mass, bridge_mass),
        (bridge_mass, trivial_mass),
    ):
        for angle in angles:
            mass = gap_scale * (np.cos(angle) * start_mass + np.sin(angle) * end_mass)
            for momentum in momenta:
                hamiltonian = momentum * gamma_x + mass
                energies = np.linalg.eigvalsh(hamiltonian)
                minimum_gap = min(minimum_gap, float(energies[4] - energies[3]))
    _names, matrices = _pauli_basis()
    time_reversal = np.kron(np.kron(matrices[0], matrices[1]), 1j * matrices[2])
    bridge_time_reversal_residual = float(
        np.max(
            np.abs(
                time_reversal @ bridge_mass.conj() @ time_reversal.conj().T
                - bridge_mass
            )
        )
    )
    valley_translation = np.kron(
        np.kron(
            matrices[0],
            np.diag([np.exp(2j * pi / 3.0), np.exp(-2j * pi / 3.0)]),
        ),
        matrices[0],
    )
    bridge_translation_residual = float(
        np.max(
            np.abs(
                valley_translation @ bridge_mass @ valley_translation.conj().T
                - bridge_mass
            )
        )
    )
    edge_momenta = np.linspace(-2.0 * gap_scale, 2.0 * gap_scale, momentum_points)
    edge_spin_z = matrices[3]
    edge_spin_x = matrices[1]
    edge_half_field = 0.2 * gap_scale
    edge_minimum_gap = min(
        float(
            np.ptp(np.linalg.eigvalsh(k * edge_spin_z + edge_half_field * edge_spin_x))
        )
        for k in edge_momenta
    )
    return {
        "mass_basis_count": len(dirac_mass_symmetry_inventory()),
        "path_segments": 2,
        "minimum_bulk_gap": minimum_gap,
        "expected_bulk_gap": 2.0 * gap_scale,
        "bridge_time_reversal_residual": bridge_time_reversal_residual,
        "bridge_translation_residual": bridge_translation_residual,
        "bridge_requires_intervalley_mixing": True,
        "uniform_parallel_field_supports_bulk_bridge": False,
        "bulk_path_evidence_role": "generic_T_broken_intervalley_proxy",
        "edge_parallel_field": edge_half_field,
        "minimum_edge_gap": edge_minimum_gap,
        "expected_edge_gap": 2.0 * edge_half_field,
    }


def _translation_preserving_path_parameters(
    *,
    spin_orbit_t2: float,
    bridge_rashba: float,
    bridge_zeeman: float,
    final_staggered_mass: float,
    path_points: int,
) -> list[dict[str, float | str]]:
    """Build the three-segment lattice path without duplicate endpoints."""

    parameters: list[dict[str, float | str]] = []
    segments = ("break_time_reversal", "rotate_bulk_mass", "remove_auxiliary_fields")
    for segment_index, segment in enumerate(segments):
        for local_index, fraction in enumerate(np.linspace(0.0, 1.0, path_points)):
            if segment_index and local_index == 0:
                continue
            parameters.append(
                _translation_preserving_path_point(
                    segment_index,
                    float(fraction),
                    spin_orbit_t2=spin_orbit_t2,
                    bridge_rashba=bridge_rashba,
                    bridge_zeeman=bridge_zeeman,
                    final_staggered_mass=final_staggered_mass,
                )
            )
    return parameters


def _translation_preserving_path_point(
    segment_index: int,
    fraction: float,
    *,
    spin_orbit_t2: float,
    bridge_rashba: float,
    bridge_zeeman: float,
    final_staggered_mass: float,
) -> dict[str, float | str]:
    segments = ("break_time_reversal", "rotate_bulk_mass", "remove_auxiliary_fields")
    if segment_index not in range(len(segments)) or not 0.0 <= fraction <= 1.0:
        raise ValueError("invalid lattice-path coordinate")
    segment = segments[segment_index]
    if segment == "break_time_reversal":
        current_spin_orbit = spin_orbit_t2
        current_rashba = fraction * bridge_rashba
        current_zeeman = fraction * bridge_zeeman
        current_staggered = 0.0
    elif segment == "rotate_bulk_mass":
        current_spin_orbit = (1.0 - fraction) * spin_orbit_t2
        current_rashba = bridge_rashba
        current_zeeman = bridge_zeeman
        current_staggered = fraction * final_staggered_mass
    else:
        current_spin_orbit = 0.0
        current_rashba = (1.0 - fraction) * bridge_rashba
        current_zeeman = (1.0 - fraction) * bridge_zeeman
        current_staggered = final_staggered_mass
    return {
        "segment": segment,
        "path_coordinate": segment_index + fraction,
        "spin_orbit_t2": current_spin_orbit,
        "rashba_lambda": current_rashba,
        "in_plane_zeeman": current_zeeman,
        "staggered_sublattice_mass": current_staggered,
    }


def _scan_translation_preserving_path(
    *,
    hopping_t: float,
    spin_orbit_t2: float,
    bridge_rashba: float,
    bridge_zeeman: float,
    final_staggered_mass: float,
    grid_size: int,
    path_points: int,
) -> list[dict[str, float | int | str]]:
    path_parameters = _translation_preserving_path_parameters(
        spin_orbit_t2=spin_orbit_t2,
        bridge_rashba=bridge_rashba,
        bridge_zeeman=bridge_zeeman,
        final_staggered_mass=final_staggered_mass,
        path_points=path_points,
    )
    rows: list[dict[str, float | int | str]] = []
    for path_index, parameters in enumerate(path_parameters):
        valence_maximum = -float("inf")
        conduction_minimum = float("inf")
        minimum_direct_gap = float("inf")
        for first in range(grid_size):
            for second in range(grid_size):
                matrix = spinful_honeycomb_bulk_hamiltonian(
                    first / grid_size,
                    second / grid_size,
                    hopping_t=hopping_t,
                    spin_orbit_t2=float(parameters["spin_orbit_t2"]),
                    rashba_lambda=float(parameters["rashba_lambda"]),
                    staggered_sublattice_mass=float(
                        parameters["staggered_sublattice_mass"]
                    ),
                    in_plane_zeeman=float(parameters["in_plane_zeeman"]),
                )
                energies = np.linalg.eigvalsh(matrix)
                valence_maximum = max(valence_maximum, float(energies[1]))
                conduction_minimum = min(conduction_minimum, float(energies[2]))
                minimum_direct_gap = min(
                    minimum_direct_gap, float(energies[2] - energies[1])
                )
        rows.append(
            {
                "path_index": path_index,
                "path_coordinate": float(parameters["path_coordinate"]),
                "segment": str(parameters["segment"]),
                "grid_size": grid_size,
                "spin_orbit_t2_over_t": float(parameters["spin_orbit_t2"]) / hopping_t,
                "rashba_lambda_over_t": float(parameters["rashba_lambda"]) / hopping_t,
                "in_plane_zeeman_over_t": float(parameters["in_plane_zeeman"])
                / hopping_t,
                "staggered_sublattice_mass_over_t": float(
                    parameters["staggered_sublattice_mass"]
                )
                / hopping_t,
                "valence_maximum_over_t": valence_maximum / hopping_t,
                "conduction_minimum_over_t": conduction_minimum / hopping_t,
                "minimum_direct_gap_over_t": minimum_direct_gap / hopping_t,
                "indirect_gap_over_t": (conduction_minimum - valence_maximum)
                / hopping_t,
            }
        )
    return rows


def translation_preserving_parallel_field_path(
    *,
    hopping_t: float,
    spin_orbit_t2: float,
    bridge_rashba: float,
    bridge_zeeman: float,
    final_staggered_mass: float,
    coarse_grid_size: int = 24,
    fine_grid_size: int = 48,
    coarse_path_points: int = 21,
    fine_path_points: int = 41,
    optimizer_seed: int = 41737,
    optimizer_max_iterations: int = 200,
) -> tuple[list[dict[str, float | int | str]], dict[str, Any]]:
    """Falsify a minimal primitive-translation-preserving path candidate.

    The uniform parallel Zeeman field breaks time reversal and the mirror that
    protected the original distinction.  The paper does not print the extra
    terms that allegedly form its continuously gapped path.  We therefore test
    the minimal published-term candidate: lattice Rashba plus a uniform field
    while the intrinsic mass is exchanged for a staggered mass.  A continuous
    Brillouin-zone optimizer actively searches for a missed closing; finding
    one makes the publication claim underspecified rather than silently
    promoting this convenient interpolation to paper support.
    """

    if hopping_t <= 0 or spin_orbit_t2 <= 0:
        raise ValueError("positive hopping and intrinsic spin orbit required")
    if min(bridge_rashba, bridge_zeeman, final_staggered_mass) <= 0:
        raise ValueError("all bridge fields must be positive")
    for grid_size in (coarse_grid_size, fine_grid_size):
        if grid_size < 12 or grid_size % 3:
            raise ValueError("bulk grids must include K/K' and be divisible by 3")
    if fine_grid_size <= coarse_grid_size:
        raise ValueError("fine bulk grid must exceed coarse grid")
    if coarse_path_points < 11 or fine_path_points <= coarse_path_points:
        raise ValueError("path requires increasing coarse/fine resolution")
    if optimizer_max_iterations < 50:
        raise ValueError("continuous gap falsification requires a resolved optimizer")

    coarse_rows = _scan_translation_preserving_path(
        hopping_t=hopping_t,
        spin_orbit_t2=spin_orbit_t2,
        bridge_rashba=bridge_rashba,
        bridge_zeeman=bridge_zeeman,
        final_staggered_mass=final_staggered_mass,
        grid_size=coarse_grid_size,
        path_points=coarse_path_points,
    )
    fine_rows = _scan_translation_preserving_path(
        hopping_t=hopping_t,
        spin_orbit_t2=spin_orbit_t2,
        bridge_rashba=bridge_rashba,
        bridge_zeeman=bridge_zeeman,
        final_staggered_mass=final_staggered_mass,
        grid_size=fine_grid_size,
        path_points=fine_path_points,
    )
    coarse_minimum = min(float(row["indirect_gap_over_t"]) for row in coarse_rows)
    fine_minimum = min(float(row["indirect_gap_over_t"]) for row in fine_rows)

    periodicity_residual = 0.0
    for reciprocal_u, reciprocal_v in ((0.137, 0.271), (0.421, 0.619)):
        for parameters in _translation_preserving_path_parameters(
            spin_orbit_t2=spin_orbit_t2,
            bridge_rashba=bridge_rashba,
            bridge_zeeman=bridge_zeeman,
            final_staggered_mass=final_staggered_mass,
            path_points=3,
        ):
            spectra = []
            for shifted_u, shifted_v in (
                (reciprocal_u, reciprocal_v),
                (reciprocal_u + 1.0, reciprocal_v),
                (reciprocal_u, reciprocal_v + 1.0),
            ):
                spectra.append(
                    np.linalg.eigvalsh(
                        spinful_honeycomb_bulk_hamiltonian(
                            shifted_u,
                            shifted_v,
                            hopping_t=hopping_t,
                            spin_orbit_t2=float(parameters["spin_orbit_t2"]),
                            rashba_lambda=float(parameters["rashba_lambda"]),
                            staggered_sublattice_mass=float(
                                parameters["staggered_sublattice_mass"]
                            ),
                            in_plane_zeeman=float(parameters["in_plane_zeeman"]),
                        )
                    )
                )
            periodicity_residual = max(
                periodicity_residual,
                float(np.max(np.abs(spectra[0] - spectra[1]))),
                float(np.max(np.abs(spectra[0] - spectra[2]))),
            )

    optimized_closures: list[dict[str, float | int | bool | str]] = []
    for segment_index in range(3):

        def direct_gap(coordinate: np.ndarray) -> float:
            fraction, reciprocal_u, reciprocal_v = map(float, coordinate)
            parameters = _translation_preserving_path_point(
                segment_index,
                fraction,
                spin_orbit_t2=spin_orbit_t2,
                bridge_rashba=bridge_rashba,
                bridge_zeeman=bridge_zeeman,
                final_staggered_mass=final_staggered_mass,
            )
            energies = np.linalg.eigvalsh(
                spinful_honeycomb_bulk_hamiltonian(
                    reciprocal_u,
                    reciprocal_v,
                    hopping_t=hopping_t,
                    spin_orbit_t2=float(parameters["spin_orbit_t2"]),
                    rashba_lambda=float(parameters["rashba_lambda"]),
                    staggered_sublattice_mass=float(
                        parameters["staggered_sublattice_mass"]
                    ),
                    in_plane_zeeman=float(parameters["in_plane_zeeman"]),
                )
            )
            return float((energies[2] - energies[1]) / hopping_t)

        optimized = differential_evolution(
            direct_gap,
            [(0.0, 1.0), (0.0, 1.0), (0.0, 1.0)],
            seed=optimizer_seed + segment_index,
            maxiter=optimizer_max_iterations,
            popsize=15,
            tol=1e-10,
            polish=True,
            workers=1,
        )
        optimized_closures.append(
            {
                "segment_index": segment_index,
                "segment": str(
                    _translation_preserving_path_point(
                        segment_index,
                        float(optimized.x[0]),
                        spin_orbit_t2=spin_orbit_t2,
                        bridge_rashba=bridge_rashba,
                        bridge_zeeman=bridge_zeeman,
                        final_staggered_mass=final_staggered_mass,
                    )["segment"]
                ),
                "fraction": float(optimized.x[0]),
                "reciprocal_u": float(optimized.x[1]),
                "reciprocal_v": float(optimized.x[2]),
                "minimum_direct_gap_over_t": float(optimized.fun),
                "optimizer_success": bool(optimized.success),
                "optimizer_evaluations": int(optimized.nfev),
            }
        )
    optimized_minimum = min(
        optimized_closures,
        key=lambda row: float(row["minimum_direct_gap_over_t"]),
    )

    summary: dict[str, Any] = {
        "coarse_grid_size": coarse_grid_size,
        "fine_grid_size": fine_grid_size,
        "coarse_path_points_per_segment": coarse_path_points,
        "fine_path_points_per_segment": fine_path_points,
        "coarse_minimum_indirect_gap_over_t": coarse_minimum,
        "fine_minimum_indirect_gap_over_t": fine_minimum,
        "coarse_fine_gap_delta_over_t": abs(coarse_minimum - fine_minimum),
        "initial_indirect_gap_over_t": float(fine_rows[0]["indirect_gap_over_t"]),
        "final_indirect_gap_over_t": float(fine_rows[-1]["indirect_gap_over_t"]),
        "reciprocal_spectrum_periodicity_residual": periodicity_residual,
        "primitive_translation_preserved": periodicity_residual <= 1e-10,
        "intervalley_mixing_used": False,
        "uniform_parallel_field_used": True,
        "uniform_parallel_field_alone_sufficient": False,
        "path_terms": "intrinsic_SO + lattice_Rashba + uniform_s_x + staggered_sigma_z",
        "continuous_optimizer_minimum_direct_gap_over_t": float(
            optimized_minimum["minimum_direct_gap_over_t"]
        ),
        "continuous_optimizer_closing_segment": str(optimized_minimum["segment"]),
        "continuous_optimizer_all_segments_successful": all(
            bool(row["optimizer_success"]) for row in optimized_closures
        ),
        "continuous_optimizer_results": optimized_closures,
        "minimal_published_term_path_status": "falsified_by_bulk_gap_closure",
        "paper_connecting_terms_status": "publication_underspecified",
        "evidence_role": "active_falsification_of_minimal_translation_preserving_path",
    }
    return fine_rows, summary
