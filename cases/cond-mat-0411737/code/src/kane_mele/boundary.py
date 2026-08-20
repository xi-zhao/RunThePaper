"""Boundary-orientation, flat-band, and Rashba-sweep observables."""

from __future__ import annotations

from math import pi, sqrt

import numpy as np
from scipy.linalg import eigh

from .model import (
    RibbonGeometry,
    build_armchair_geometry,
    build_ribbon_geometry,
    edge_weights,
    ribbon_hamiltonian,
    spinful_ribbon_hamiltonian,
)
from .response import bulk_half_filling_gap_edges


def armchair_crossing_convergence(
    widths: list[int],
    *,
    hopping_t: float,
    spin_orbit_t2: float,
    edge_depth: int,
    distance_tolerance: float,
) -> list[dict[str, float | int]]:
    """Converge the armchair Kramers crossing at ``k=0`` with strip width."""

    if len(widths) < 3 or sorted(widths) != widths:
        raise ValueError("at least three increasing armchair widths are required")
    rows: list[dict[str, float | int]] = []
    for width in widths:
        geometry = build_armchair_geometry(width, distance_tolerance=distance_tolerance)
        matrix = spinful_ribbon_hamiltonian(
            geometry,
            0.0,
            hopping_t=hopping_t,
            spin_orbit_t2=spin_orbit_t2,
            rashba_lambda=0.0,
        )
        energies, vectors = np.linalg.eigh(matrix)
        central = np.argsort(np.abs(energies))[:4]
        total_edge, _bottom, _top = edge_weights(
            geometry, vectors, chain_depth=edge_depth
        )
        rows.append(
            {
                "width_chains": width,
                "matrix_dimension": int(matrix.shape[0]),
                "finite_width_half_gap_over_t": float(
                    np.max(np.abs(energies[central])) / hopping_t
                ),
                "central_min_edge_weight": float(np.min(total_edge[central])),
                "hermiticity_residual": float(np.max(np.abs(matrix - matrix.conj().T))),
            }
        )
    return rows


def _central_edge_states(
    geometry: RibbonGeometry,
    momentum: float,
    *,
    hopping_t: float,
    spin_orbit_t2: float,
    edge_depth: int,
) -> tuple[np.ndarray, np.ndarray]:
    matrix = ribbon_hamiltonian(
        geometry,
        momentum,
        hopping_t=hopping_t,
        spin_orbit_t2=spin_orbit_t2,
        spin=1,
    )
    energies, vectors = np.linalg.eigh(matrix)
    edge, _bottom, _top = edge_weights(geometry, vectors, chain_depth=edge_depth)
    central = np.argsort(np.abs(energies))[:2]
    return energies[central], edge[central]


def flat_zigzag_band_diagnostics(
    *,
    width: int,
    hopping_t: float,
    spin_orbit_t2: float,
    edge_depth: int,
    distance_tolerance: float,
    k_points: int = 121,
    dos_broadening: float = 0.01,
) -> tuple[list[dict[str, float]], dict[str, float]]:
    """Resolve the full ``t2 -> 0`` flat-band interval and DOS enhancement."""

    if k_points < 31 or dos_broadening <= 0:
        raise ValueError("flat-band grid and broadening must be resolved")
    geometry = build_ribbon_geometry(width, distance_tolerance=distance_tolerance)
    momenta = np.linspace(2.0 * pi / 3.0, 4.0 * pi / 3.0, k_points)
    rows: list[dict[str, float]] = []
    zero_dos = 0.0
    finite_dos = 0.0
    zero_interior_abs: list[float] = []
    zero_interior_edge: list[float] = []
    for momentum in momenta:
        zero_energies, zero_edges = _central_edge_states(
            geometry,
            float(momentum),
            hopping_t=hopping_t,
            spin_orbit_t2=0.0,
            edge_depth=edge_depth,
        )
        finite_energies, finite_edges = _central_edge_states(
            geometry,
            float(momentum),
            hopping_t=hopping_t,
            spin_orbit_t2=spin_orbit_t2,
            edge_depth=edge_depth,
        )
        decay_ratio = abs(2.0 * np.cos(momentum / 2.0))
        semi_infinite_outer_weight = max(0.0, 1.0 - decay_ratio**2)
        gaussian_normalization = sqrt(2.0 * pi) * dos_broadening
        zero_dos += float(
            np.sum(
                zero_edges
                * np.exp(-0.5 * (zero_energies / dos_broadening) ** 2)
                / gaussian_normalization
            )
        )
        finite_dos += float(
            np.sum(
                finite_edges
                * np.exp(-0.5 * (finite_energies / dos_broadening) ** 2)
                / gaussian_normalization
            )
        )
        if 0.8 * pi <= momentum <= 1.2 * pi:
            zero_interior_abs.extend(np.abs(zero_energies).tolist())
            zero_interior_edge.extend(zero_edges.tolist())
        rows.append(
            {
                "k_over_pi": float(momentum / pi),
                "analytic_decay_ratio": float(decay_ratio),
                "analytic_outer_chain_weight": float(semi_infinite_outer_weight),
                "zero_t2_max_abs_energy": float(np.max(np.abs(zero_energies))),
                "zero_t2_min_edge_weight": float(np.min(zero_edges)),
                "finite_t2_max_abs_energy": float(np.max(np.abs(finite_energies))),
                "finite_t2_min_edge_weight": float(np.min(finite_edges)),
            }
        )
    zero_dos /= k_points
    finite_dos /= k_points
    return rows, {
        "analytic_interval_left_over_pi": 2.0 / 3.0,
        "analytic_interval_right_over_pi": 4.0 / 3.0,
        "analytic_endpoint_decay_ratio": 1.0,
        "zero_t2_interior_max_abs_energy": float(max(zero_interior_abs)),
        "zero_t2_interior_min_edge_weight": float(min(zero_interior_edge)),
        "zero_t2_edge_weighted_dos_at_zero": zero_dos,
        "finite_t2_edge_weighted_dos_at_zero": finite_dos,
        "dos_enhancement_ratio": zero_dos / finite_dos,
    }


def rashba_boundary_sweep(
    rashba_ratios: np.ndarray,
    *,
    zigzag_width: int,
    armchair_widths: list[int],
    hopping_t: float,
    spin_orbit_t2: float,
    zigzag_edge_depth: int,
    armchair_edge_depth: int,
    distance_tolerance: float,
    bulk_grid_size: int = 24,
    localization_enrichment_threshold: float = 0.05,
) -> list[dict[str, float | int | str | None]]:
    """Diagnose in-gap Kramers pairs over ``lambda_R/Delta_so``.

    Candidate states are selected inside the independently computed bulk gap,
    then tested against the exact uniform-state edge-weight baseline.  This is
    deliberately stricter than selecting the four eigenvalues closest to zero:
    Rashba coupling shifts an armchair crossing away from zero and that old
    selector could silently follow bulk states.
    """

    ratios = np.asarray(rashba_ratios, dtype=float)
    if ratios.ndim != 1 or len(ratios) < 4 or np.any(ratios < 0):
        raise ValueError("a nonnegative Rashba ratio sweep is required")
    if len(armchair_widths) < 3 or sorted(armchair_widths) != armchair_widths:
        raise ValueError("at least three increasing armchair widths are required")
    if localization_enrichment_threshold <= 0:
        raise ValueError("localization enrichment threshold must be positive")
    geometries = [
        (
            "zigzag",
            build_ribbon_geometry(zigzag_width, distance_tolerance=distance_tolerance),
            zigzag_edge_depth,
        ),
        *[
            (
                "armchair",
                build_armchair_geometry(width, distance_tolerance=distance_tolerance),
                armchair_edge_depth,
            )
            for width in armchair_widths
        ],
    ]
    continuum_delta = 3.0 * sqrt(3.0) * spin_orbit_t2
    rows: list[dict[str, float | int | str | None]] = []
    for ratio in ratios:
        lattice_rashba = 2.0 * ratio * continuum_delta / 3.0
        bulk_gap = bulk_half_filling_gap_edges(
            hopping_t=hopping_t,
            spin_orbit_t2=spin_orbit_t2,
            rashba_lambda=float(lattice_rashba),
            grid_size=bulk_grid_size,
        )
        for orientation, geometry, edge_depth in geometries:
            momentum = pi if orientation == "zigzag" else 0.0
            matrix = spinful_ribbon_hamiltonian(
                geometry,
                momentum,
                hopping_t=hopping_t,
                spin_orbit_t2=spin_orbit_t2,
                rashba_lambda=float(lattice_rashba),
            )
            energies, vectors = np.linalg.eigh(matrix)
            edge, _bottom, _top = edge_weights(
                geometry,
                vectors,
                chain_depth=edge_depth,
            )
            chains = np.repeat(
                np.asarray([site.chain for site in geometry.sites], dtype=int), 2
            )
            edge_mask = (chains < edge_depth) | (
                chains >= geometry.width_chains - edge_depth
            )
            uniform_edge_baseline = float(np.mean(edge_mask))
            valence_edge = float(bulk_gap["valence_maximum_over_t"] * hopping_t)
            conduction_edge = float(bulk_gap["conduction_minimum_over_t"] * hopping_t)
            candidate_pairs: list[tuple[float, int, int]] = []
            for lower_index in range(0, len(energies), 2):
                upper_index = lower_index + 1
                if upper_index >= len(energies):
                    break
                if (
                    energies[lower_index] > valence_edge + 1e-10
                    and energies[upper_index] < conduction_edge - 1e-10
                ):
                    enrichment = (
                        min(float(edge[lower_index]), float(edge[upper_index]))
                        - uniform_edge_baseline
                    )
                    candidate_pairs.append((enrichment, lower_index, upper_index))
            if candidate_pairs:
                enrichment, lower_index, upper_index = max(candidate_pairs)
                pair_residual = abs(
                    float(energies[upper_index] - energies[lower_index])
                )
                pair_energy = float(
                    0.5 * (energies[lower_index] + energies[upper_index]) / hopping_t
                )
                min_edge_weight = min(
                    float(edge[lower_index]), float(edge[upper_index])
                )
                status = (
                    "edge_pair_resolved"
                    if enrichment >= localization_enrichment_threshold
                    and pair_residual / hopping_t <= 1e-10
                    else "in_gap_pair_not_localized"
                )
            else:
                enrichment = None
                pair_residual = None
                pair_energy = None
                min_edge_weight = None
                status = "no_in_gap_kramers_pair"
            rows.append(
                {
                    "orientation": orientation,
                    "width_chains": geometry.width_chains,
                    "lambda_r_over_delta_so": float(ratio),
                    "lattice_rashba_over_t": float(lattice_rashba / hopping_t),
                    "trim_k_over_pi": float(momentum / pi),
                    "bulk_valence_maximum_over_t": bulk_gap["valence_maximum_over_t"],
                    "bulk_conduction_minimum_over_t": bulk_gap[
                        "conduction_minimum_over_t"
                    ],
                    "bulk_indirect_gap_over_t": bulk_gap["indirect_gap_over_t"],
                    "in_gap_kramers_pair_count": len(candidate_pairs),
                    "selected_pair_energy_over_t": pair_energy,
                    "kramers_pair_residual_over_t": (
                        None if pair_residual is None else pair_residual / hopping_t
                    ),
                    "selected_pair_min_edge_weight": min_edge_weight,
                    "uniform_edge_weight_baseline": uniform_edge_baseline,
                    "edge_weight_enrichment": enrichment,
                    "classification": status,
                    "hermiticity_residual": float(
                        np.max(np.abs(matrix - matrix.conj().T))
                    ),
                }
            )
    return rows


def _rashba_edge_flow_on_grid(
    geometry: RibbonGeometry,
    *,
    ratio: float,
    hopping_t: float,
    spin_orbit_t2: float,
    edge_depth: int,
    bulk_grid_size: int,
    k_points: int,
    localization_enrichment_threshold: float,
) -> tuple[list[dict[str, float | int | str]], dict[str, float | int | bool]]:
    """Resolve all bulk-gap edge states on one periodic momentum grid."""

    continuum_delta = 3.0 * sqrt(3.0) * spin_orbit_t2
    lattice_rashba = 2.0 * ratio * continuum_delta / 3.0
    bulk_gap = bulk_half_filling_gap_edges(
        hopping_t=hopping_t,
        spin_orbit_t2=spin_orbit_t2,
        rashba_lambda=float(lattice_rashba),
        grid_size=bulk_grid_size,
    )
    valence_edge = float(bulk_gap["valence_maximum_over_t"] * hopping_t)
    conduction_edge = float(bulk_gap["conduction_minimum_over_t"] * hopping_t)
    bulk_midgap = 0.5 * (valence_edge + conduction_edge)
    bulk_gap_width = conduction_edge - valence_edge
    if bulk_gap_width <= 0.0:
        raise ValueError("subcritical Rashba edge flow requires a positive bulk gap")

    chains = np.repeat(
        np.asarray([site.chain for site in geometry.sites], dtype=int), 2
    )
    bottom_baseline = float(np.mean(chains < edge_depth))
    top_baseline = float(np.mean(chains >= geometry.width_chains - edge_depth))
    total_baseline = bottom_baseline + top_baseline
    momenta = np.linspace(0.0, 2.0 * pi, k_points, endpoint=False)
    rows: list[dict[str, float | int | str]] = []
    localized_energies: list[float] = []
    bottom_enrichments: list[float] = []
    top_enrichments: list[float] = []
    nearest_midgap_distance = float("inf")
    hermiticity_residual = 0.0

    for momentum_index, momentum in enumerate(momenta):
        matrix = spinful_ribbon_hamiltonian(
            geometry,
            float(momentum),
            hopping_t=hopping_t,
            spin_orbit_t2=spin_orbit_t2,
            rashba_lambda=float(lattice_rashba),
        )
        hermiticity_residual = max(
            hermiticity_residual,
            float(np.max(np.abs(matrix - matrix.conj().T))),
        )
        energies, vectors = eigh(
            matrix,
            subset_by_value=(valence_edge + 1e-10, conduction_edge - 1e-10),
            driver="evr",
        )
        if energies.size:
            total_edge, bottom_edge, top_edge = edge_weights(
                geometry,
                np.asarray(vectors, dtype=np.complex128),
                chain_depth=edge_depth,
            )
            total_enrichment = total_edge - total_baseline
            localized = total_enrichment >= localization_enrichment_threshold
        else:
            total_edge = np.empty(0, dtype=float)
            bottom_edge = np.empty(0, dtype=float)
            top_edge = np.empty(0, dtype=float)
            localized = np.empty(0, dtype=bool)

        selected_energies = np.asarray(energies[localized], dtype=float)
        selected_bottom = np.asarray(bottom_edge[localized], dtype=float)
        selected_top = np.asarray(top_edge[localized], dtype=float)
        localized_energies.extend(selected_energies.tolist())
        bottom_enrichments.extend((selected_bottom - bottom_baseline).tolist())
        top_enrichments.extend((selected_top - top_baseline).tolist())
        if selected_energies.size:
            nearest_index = int(np.argmin(np.abs(selected_energies - bulk_midgap)))
            nearest_energy = float(selected_energies[nearest_index])
            nearest_midgap_distance = min(
                nearest_midgap_distance, abs(nearest_energy - bulk_midgap)
            )
            energy_minimum = float(np.min(selected_energies) / hopping_t)
            energy_maximum = float(np.max(selected_energies) / hopping_t)
            nearest_energy_over_t = nearest_energy / hopping_t
            maximum_bottom_enrichment = float(np.max(selected_bottom - bottom_baseline))
            maximum_top_enrichment = float(np.max(selected_top - top_baseline))
            classification = "localized_in_gap_state"
        else:
            energy_minimum = float("nan")
            energy_maximum = float("nan")
            nearest_energy_over_t = float("nan")
            maximum_bottom_enrichment = 0.0
            maximum_top_enrichment = 0.0
            classification = "no_localized_in_gap_state"
        rows.append(
            {
                "orientation": geometry.edge_orientation,
                "width_chains": geometry.width_chains,
                "lambda_r_over_delta_so": ratio,
                "lattice_rashba_over_t": lattice_rashba / hopping_t,
                "k_index": momentum_index,
                "k_over_pi": float(momentum / pi),
                "k_points": k_points,
                "bulk_valence_maximum_over_t": valence_edge / hopping_t,
                "bulk_conduction_minimum_over_t": conduction_edge / hopping_t,
                "bulk_midgap_over_t": bulk_midgap / hopping_t,
                "in_gap_state_count": int(energies.size),
                "localized_state_count": int(np.count_nonzero(localized)),
                "localized_energy_min_over_t": energy_minimum,
                "localized_energy_max_over_t": energy_maximum,
                "nearest_midgap_energy_over_t": nearest_energy_over_t,
                "maximum_bottom_edge_enrichment": maximum_bottom_enrichment,
                "maximum_top_edge_enrichment": maximum_top_enrichment,
                "uniform_total_edge_weight_baseline": total_baseline,
                "classification": classification,
            }
        )

    energy_minimum = min(localized_energies, default=float("inf"))
    energy_maximum = max(localized_energies, default=-float("inf"))
    midgap_bracketed = energy_minimum <= bulk_midgap <= energy_maximum
    bottom_resolved = max(bottom_enrichments, default=0.0) >= (
        localization_enrichment_threshold / 2.0
    )
    top_resolved = max(top_enrichments, default=0.0) >= (
        localization_enrichment_threshold / 2.0
    )
    resolved = bool(midgap_bracketed and bottom_resolved and top_resolved)
    summary: dict[str, float | int | bool] = {
        "width_chains": geometry.width_chains,
        "lambda_r_over_delta_so": ratio,
        "k_points": k_points,
        "bulk_valence_maximum_over_t": valence_edge / hopping_t,
        "bulk_conduction_minimum_over_t": conduction_edge / hopping_t,
        "bulk_indirect_gap_over_t": bulk_gap_width / hopping_t,
        "localized_state_samples": len(localized_energies),
        "localized_energy_min_over_t": energy_minimum / hopping_t,
        "localized_energy_max_over_t": energy_maximum / hopping_t,
        "nearest_midgap_distance_over_gap": nearest_midgap_distance / bulk_gap_width,
        "maximum_bottom_edge_enrichment": max(bottom_enrichments, default=0.0),
        "maximum_top_edge_enrichment": max(top_enrichments, default=0.0),
        "midgap_bracketed": midgap_bracketed,
        "bottom_edge_resolved": bottom_resolved,
        "top_edge_resolved": top_resolved,
        "resolved": resolved,
        "hermiticity_residual": hermiticity_residual,
    }
    return rows, summary


def rashba_edge_spectral_flow(
    rashba_ratios: np.ndarray,
    *,
    zigzag_widths: list[int],
    armchair_widths: list[int],
    hopping_t: float,
    spin_orbit_t2: float,
    zigzag_edge_depth: int,
    armchair_edge_depth: int,
    distance_tolerance: float,
    bulk_grid_size: int = 24,
    initial_k_points: int = 48,
    maximum_k_points: int = 768,
    localization_enrichment_threshold: float = 0.01,
    grid_convergence_tolerance: float = 0.05,
) -> tuple[
    list[dict[str, float | int | str]],
    list[dict[str, float | int | str | bool]],
]:
    """Track subcritical finite-Rashba edge branches over the full Brillouin zone.

    Every orientation, coupling and width is sampled adaptively until two
    successive momentum grids both resolve edge-localized states connecting
    the lower and upper halves of the independently computed bulk gap.  This
    tests spectral flow; it does not assume the crossing remains at a TRIM or
    near zero energy.
    """

    ratios = np.asarray(rashba_ratios, dtype=float)
    if ratios.ndim != 1 or not len(ratios) or np.any(ratios < 0) or np.any(ratios >= 1):
        raise ValueError("full edge flow requires subcritical 0 <= lambda_R/Delta < 1")
    for widths in (zigzag_widths, armchair_widths):
        if (
            len(widths) < 3
            or sorted(widths) != widths
            or len(set(widths)) != len(widths)
        ):
            raise ValueError("each orientation requires three increasing widths")
    if (
        initial_k_points < 24
        or initial_k_points % 2
        or maximum_k_points < 2 * initial_k_points
        or maximum_k_points % initial_k_points
    ):
        raise ValueError("momentum grids must be even nested doublings")
    if localization_enrichment_threshold <= 0 or grid_convergence_tolerance <= 0:
        raise ValueError("positive localization and convergence thresholds required")

    geometries = [
        *[
            (
                build_ribbon_geometry(width, distance_tolerance=distance_tolerance),
                zigzag_edge_depth,
            )
            for width in zigzag_widths
        ],
        *[
            (
                build_armchair_geometry(width, distance_tolerance=distance_tolerance),
                armchair_edge_depth,
            )
            for width in armchair_widths
        ],
    ]
    final_rows: list[dict[str, float | int | str]] = []
    summaries: list[dict[str, float | int | str | bool]] = []
    for ratio in ratios:
        for geometry, edge_depth in geometries:
            previous: dict[str, float | int | bool] | None = None
            k_points = initial_k_points
            while True:
                rows, current = _rashba_edge_flow_on_grid(
                    geometry,
                    ratio=float(ratio),
                    hopping_t=hopping_t,
                    spin_orbit_t2=spin_orbit_t2,
                    edge_depth=edge_depth,
                    bulk_grid_size=bulk_grid_size,
                    k_points=k_points,
                    localization_enrichment_threshold=localization_enrichment_threshold,
                )
                extrema_converged = False
                midgap_distance_converged = False
                if previous is not None:
                    gap = float(current["bulk_indirect_gap_over_t"])
                    extrema_delta = max(
                        abs(
                            float(current["localized_energy_min_over_t"])
                            - float(previous["localized_energy_min_over_t"])
                        ),
                        abs(
                            float(current["localized_energy_max_over_t"])
                            - float(previous["localized_energy_max_over_t"])
                        ),
                    )
                    extrema_converged = (
                        extrema_delta / gap <= grid_convergence_tolerance
                    )
                    midgap_distance_converged = (
                        abs(
                            float(current["nearest_midgap_distance_over_gap"])
                            - float(previous["nearest_midgap_distance_over_gap"])
                        )
                        <= grid_convergence_tolerance
                    )
                grid_converged = bool(
                    previous is not None
                    and bool(previous["resolved"])
                    and bool(current["resolved"])
                    and extrema_converged
                    and midgap_distance_converged
                )
                if grid_converged or k_points >= maximum_k_points:
                    final_rows.extend(rows)
                    summaries.append(
                        {
                            "orientation": geometry.edge_orientation,
                            **current,
                            "previous_k_points": (
                                0 if previous is None else int(previous["k_points"])
                            ),
                            "previous_grid_resolved": bool(
                                previous is not None and previous["resolved"]
                            ),
                            "extrema_grid_converged": extrema_converged,
                            "midgap_distance_grid_converged": midgap_distance_converged,
                            "grid_converged": grid_converged,
                            "classification": (
                                "full_k_edge_spectral_flow_resolved"
                                if grid_converged
                                else "full_k_edge_spectral_flow_unresolved"
                            ),
                        }
                    )
                    break
                previous = current
                k_points *= 2
    return final_rows, summaries
