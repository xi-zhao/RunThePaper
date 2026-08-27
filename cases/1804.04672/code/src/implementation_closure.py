"""Unified reduced campaign for the 35 previously non-ready items.

Only equation-derived kernels and frozen JSON parameters are consumed.  The
campaign is an implementation attestation: reduced grids, reconstructed
geometry choices, and unpublished paper inputs never become scientific
coverage merely because the code ran.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any, Iterable

import numpy as np
import scipy.sparse as sp

from nonhermitian_chern import (
    CylinderParams,
    DiskParams,
    SquareParams,
    disk_gap_square,
    fig2_square_parameter_sets,
    fig_s2_gap_scaling_parameter_sets,
    fit_gap_scaling_by_mass,
    generate_cylinder_spectrum_rows,
    generate_disk_gap_scaling_rows,
    generate_square_spectrum_rows,
    open_boundary_bloch_phase_boundaries,
    open_boundary_non_bloch_phase_boundary,
    pauli_matrices,
    square_gap_square,
    square_wavepacket_snapshots,
)
from supplemental_campaign import (
    exact_cylinder_phase_rows,
    exact_cylinder_spectrum_arrays,
    s4_finite_size_scan,
    s4_parameter_rows,
    similarity_transform_residual,
)


ITEMS_BY_TARGET = {
    "T001": ["PFIG-003-B-BULK-SPECTRUM", "PFIG-003-B-CHIRAL-EDGE"],
    "T003": ["PFIG-001-BLOCH-MINUS", "PFIG-001-BLOCH-PLUS", "PFIG-001-NONBLOCH", "PFIG-001-OBC-NUMERICAL"],
    "T004": [
        "PFIG-002-A-DENSITY-T000",
        "PFIG-002-A-DENSITY-T005",
        "PFIG-002-A-DENSITY-T020",
        "PFIG-002-A-SPECTRUM",
        "PFIG-002-B-DENSITY-T005",
        "PFIG-002-B-DENSITY-T020",
        "PFIG-002-B-SPECTRUM",
    ],
    "T005": [
        "PFIG-S02-A-GAP-DATA",
        "PFIG-S02-A-GAP-FIT",
        "PFIG-S02-B-GAP-DATA",
        "PFIG-S02-B-GAP-FIT",
        "PFIG-S02-C-GAP-DATA",
        "PFIG-S02-C-GAP-FIT",
    ],
    "T006": ["PFIG-S03-DISK-NUMERICAL"],
    "T007": [
        "PFIG-S04-LOWER-BLOCH-MINUS",
        "PFIG-S04-LOWER-BLOCH-PLUS",
        "PFIG-S04-LOWER-NONBLOCH",
        "PFIG-S04-LOWER-NUMERICAL",
        "PFIG-S04-UPPER-BLOCH-MINUS",
        "PFIG-S04-UPPER-BLOCH-PLUS",
        "PFIG-S04-UPPER-NONBLOCH",
        "PFIG-S04-UPPER-NUMERICAL",
    ],
    "T011": [
        "PFIG-S09-A-BLOCH-MINUS",
        "PFIG-S09-A-BLOCH-PLUS",
        "PFIG-S09-A-CYLINDER-MINUS",
        "PFIG-S09-A-CYLINDER-PLUS",
        "PFIG-S09-B-BULK-SPECTRUM",
        "PFIG-S09-B-CHIRAL-EDGE",
    ],
    "T012": ["PCLM-TRIANGLE-GEOMETRY-INDEPENDENCE"],
}


def _finite_size_boundary(
    *,
    geometry: str,
    gamma: float,
    sizes: Iterable[int],
    m_offsets: Iterable[float],
) -> dict[str, Any]:
    """Run a reduced, explicit finite-size gap scan without source curves."""

    theory = open_boundary_non_bloch_phase_boundary(gamma)
    sizes = tuple(int(value) for value in sizes)
    rows = []
    for offset in m_offsets:
        mass = theory + float(offset)
        gaps = []
        for size in sizes:
            if geometry == "square":
                gap = square_gap_square(SquareParams(L=size, m=mass, gamma_x=gamma, gamma_y=gamma), eigen_count=6)
            elif geometry == "disk":
                gap = disk_gap_square(DiskParams(radius=size, m=mass, gamma_x=gamma, gamma_y=gamma), eigen_count=6)
            else:
                raise ValueError(f"unknown geometry: {geometry}")
            gaps.append(float(gap))
        slope, intercept = np.polyfit(1.0 / np.asarray(sizes, dtype=float) ** 2, np.asarray(gaps), 1)
        rows.append({"m": mass, "offset": float(offset), "gaps": gaps, "intercept": float(intercept), "slope": float(slope)})
    selected = min(rows, key=lambda row: abs(float(row["intercept"])))
    return {"geometry": geometry, "gamma": gamma, "theory_boundary": theory, "candidate_rows": rows, "reduced_numerical_boundary": selected["m"]}


def _generic_open_geometry_hamiltonian(sites: tuple[tuple[int, int], ...], params: SquareParams) -> sp.csr_matrix:
    """Build the paper Hamiltonian on any declared nearest-neighbour site set."""

    if not sites:
        raise ValueError("geometry must contain at least one site")
    index = {site: position for position, site in enumerate(sites)}
    sx, sy, sz = pauli_matrices()
    onsite = params.m * sz + 1j * params.gamma_x * sx + 1j * params.gamma_y * sy + 1j * params.gamma_z * sz
    x_hopping = -0.5 * params.t_x * sz - 0.5j * params.v_x * sx
    y_hopping = -0.5 * params.t_y * sz - 0.5j * params.v_y * sy
    rows: list[int] = []
    columns: list[int] = []
    values: list[complex] = []

    def add(row_site: tuple[int, int], column_site: tuple[int, int], block: np.ndarray) -> None:
        row_start = 2 * index[row_site]
        column_start = 2 * index[column_site]
        for local_row in range(2):
            for local_column in range(2):
                value = complex(block[local_row, local_column])
                if value != 0.0:
                    rows.append(row_start + local_row)
                    columns.append(column_start + local_column)
                    values.append(value)

    for site in sites:
        add(site, site, onsite)
        for displacement, hopping in (((1, 0), x_hopping), ((0, 1), y_hopping)):
            neighbour = (site[0] + displacement[0], site[1] + displacement[1])
            if neighbour in index:
                add(site, neighbour, hopping)
                add(neighbour, site, hopping.conj().T)
    dimension = 2 * len(sites)
    return sp.csr_matrix((values, (rows, columns)), shape=(dimension, dimension))


def _triangle_witness(parameters: dict[str, Any]) -> dict[str, Any]:
    extent = int(parameters["attestation_extent"])
    sites = tuple((x, y) for y in range(extent) for x in range(extent - y))
    gaps = []
    for mass in parameters["masses"]:
        matrix = _generic_open_geometry_hamiltonian(
            sites,
            SquareParams(
                L=extent,
                m=float(mass),
                gamma_x=float(parameters["gamma"]),
                gamma_y=float(parameters["gamma"]),
                target_id="T012",
            ),
        ).toarray()
        values = np.linalg.eigvals(matrix)
        gaps.append({"m": float(mass), "minimum_abs_energy": float(np.min(np.abs(values)))})
    return {
        "attestation_geometry": "right_isosceles_integer_site_triangle",
        "site_count": len(sites),
        "gap_scan": gaps,
        "paper_exact_status": "input_blocked",
        "blocked_input_schema": parameters["blocked_input_schema"],
        "passed": bool(len(sites) > 0 and all(np.isfinite(row["minimum_abs_energy"]) for row in gaps)),
    }


def run_campaign(config: dict[str, Any]) -> dict[str, Any]:
    parameters = config["parameters"]
    checks: dict[str, dict[str, Any]] = {}

    cylinder = parameters["cylinder_spectrum"]
    cylinder_params = CylinderParams(
        gamma_x=float(cylinder["gamma"]),
        gamma_y=float(cylinder["gamma"]),
        m=float(cylinder["m"]),
        L_y=int(cylinder["length_y"]),
        target_id="T001",
    )
    kx = np.linspace(-np.pi, np.pi, int(cylinder["kx_points"]), endpoint=False)
    cylinder_rows = generate_cylinder_spectrum_rows(kx, cylinder_params)
    edge_rows = [row for row in cylinder_rows if row["edge_label"] != "bulk"]
    checks["T001"] = {
        "row_count": len(cylinder_rows),
        "edge_candidate_count": len(edge_rows),
        "paper_grid": {"length_y": 40, "kx_points": 180},
        "attestation_grid": {"length_y": cylinder_params.L_y, "kx_points": len(kx)},
        "passed": bool(cylinder_rows and all(np.isfinite([row["energy_real"], row["energy_imag"]]).all() for row in cylinder_rows)),
    }

    phase = parameters["phase_boundaries"]
    gamma_values = [float(value) for value in phase["gamma_values"]]
    analytic_rows = []
    numerical_rows = []
    for gamma in gamma_values:
        lower, upper = open_boundary_bloch_phase_boundaries(gamma)
        analytic_rows.append({"gamma": gamma, "bloch_minus": lower, "bloch_plus": upper, "non_bloch": open_boundary_non_bloch_phase_boundary(gamma)})
        numerical_rows.append(
            _finite_size_boundary(
                geometry="square",
                gamma=gamma,
                sizes=phase["square_sizes"],
                m_offsets=phase["m_offsets"],
            )
        )
    checks["T003"] = {
        "analytic_rows": analytic_rows,
        "reduced_numerical_rows": numerical_rows,
        "paper_exact_status": "input_blocked",
        "blocked_input_schema": phase["blocked_input_schema"],
        "passed": bool(all(np.isfinite(list(row.values())).all() for row in analytic_rows)),
    }

    dynamics = parameters["square_dynamics"]
    square_parameters = fig2_square_parameter_sets(L=int(dynamics["length"]))
    snapshot_summaries = []
    for label, parameter_set in square_parameters.items():
        rows = square_wavepacket_snapshots(parameter_set, times=dynamics["times"])
        for time in dynamics["times"]:
            total = sum(float(row["intensity"]) for row in rows if np.isclose(float(row["time"]), float(time)))
            snapshot_summaries.append({"parameter_set": label, "time": float(time), "intensity_sum": total})
    spectrum_rows = generate_square_spectrum_rows(square_parameters, eigen_count=int(dynamics["eigen_count"]))
    checks["T004"] = {
        "snapshots": snapshot_summaries,
        "spectrum_row_count": len(spectrum_rows),
        "paper_length": 30,
        "attestation_length": int(dynamics["length"]),
        "passed": bool(all(abs(row["intensity_sum"] - 1.0) < 1e-10 for row in snapshot_summaries) and spectrum_rows),
    }

    gap = parameters["disk_gap_scaling"]
    disk_sets = {label: replace(value, radius=int(gap["radii"][0])) for label, value in fig_s2_gap_scaling_parameter_sets().items()}
    gap_rows = generate_disk_gap_scaling_rows(disk_sets, gap["radii"], eigen_count=int(gap["eigen_count"]))
    gap_fits = fit_gap_scaling_by_mass(gap_rows)
    checks["T005"] = {
        "data_row_count": len(gap_rows),
        "fits": gap_fits,
        "paper_exact_status": "input_blocked",
        "blocked_input_schema": gap["blocked_input_schema"],
        "passed": bool(len(gap_rows) == 3 * len(gap["radii"]) and all(np.isfinite(float(row["intercept"])) for row in gap_fits.values())),
    }

    disk_phase = parameters["disk_phase_boundary"]
    disk_boundaries = [
        _finite_size_boundary(
            geometry="disk",
            gamma=float(gamma),
            sizes=disk_phase["radii"],
            m_offsets=disk_phase["m_offsets"],
        )
        for gamma in disk_phase["gamma_values"]
    ]
    checks["T006"] = {
        "reduced_numerical_rows": disk_boundaries,
        "paper_exact_status": "input_blocked",
        "blocked_input_schema": disk_phase["blocked_input_schema"],
        "passed": bool(disk_boundaries and all(np.isfinite(row["reduced_numerical_boundary"]) for row in disk_boundaries)),
    }

    s4 = parameters["s4"]
    s4_analytic = s4_parameter_rows(s4["gamma_values"])
    s4_numeric = s4_finite_size_scan(s4["families"], s4["scan_gamma_values"], s4["sizes"], s4["m_offsets"])
    checks["T007"] = {
        "analytic_row_count": len(s4_analytic),
        "finite_size_row_count": len(s4_numeric),
        "paper_scale_status": "code_ready_not_run",
        "passed": bool(s4_analytic and s4_numeric and all(np.isfinite(float(row["intercept_gap_square"])) for row in s4_numeric)),
    }

    exact = parameters["exact_cylinder"]
    exact_phase_rows = exact_cylinder_phase_rows(exact["gamma_values"], t=float(exact["t"]))
    exact_arrays = exact_cylinder_spectrum_arrays(
        gamma=float(exact["gamma"]),
        m=float(exact["m"]),
        t=float(exact["t"]),
        length_y=int(exact["length_y"]),
        kx_points=int(exact["kx_points"]),
    )
    residual = similarity_transform_residual(int(exact["length_y"]), float(exact["gamma"]))
    checks["T011"] = {
        "phase_row_count": len(exact_phase_rows),
        "spectrum_shape": list(exact_arrays["T011_energies"].shape),
        "similarity_transform_residual": residual,
        "paper_grid": {"length_y": 40, "kx_points": 180},
        "paper_scale_status": "code_ready_not_run",
        "passed": bool(np.isfinite(exact_arrays["T011_energies"]).all() and residual < 1e-12),
    }

    checks["T012"] = _triangle_witness(parameters["triangle"])

    item_results = {
        item_id: {
            "target_id": target_id,
            "implementation_status": "attested" if checks[target_id]["passed"] else "failed",
            "scientific_status": "unchanged",
        }
        for target_id, item_ids in ITEMS_BY_TARGET.items()
        for item_id in item_ids
    }
    return {
        "schema_version": 1,
        "paper_id": "1804.04672",
        "profile": config["profile"],
        "purpose": "implementation_attestation_only",
        "scientific_coverage_changed": False,
        "source_pixels_used": False,
        "author_arrays_used": False,
        "author_code_used": False,
        "target_checks": checks,
        "item_results": item_results,
        "status": "passed" if all(row["passed"] for row in checks.values()) else "failed",
    }
