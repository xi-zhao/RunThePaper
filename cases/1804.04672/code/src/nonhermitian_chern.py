from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla


@dataclass(frozen=True)
class CylinderParams:
    t_x: float = 1.0
    t_y: float = 1.0
    v_x: float = 1.0
    v_y: float = 1.0
    gamma_x: float = 0.2
    gamma_y: float = 0.2
    gamma_z: float = 0.0
    m: float = 1.717
    L_y: int = 40
    target_id: str = "T001"


@dataclass(frozen=True)
class SquareParams:
    t_x: float = 1.0
    t_y: float = 1.0
    v_x: float = 1.0
    v_y: float = 1.0
    gamma_x: float = 0.15
    gamma_y: float = 0.15
    gamma_z: float = 0.0
    m: float = 2.0
    L: int = 30
    target_id: str = "T003"


@dataclass(frozen=True)
class DiskParams:
    t_x: float = 1.0
    t_y: float = 1.0
    v_x: float = 1.0
    v_y: float = 1.0
    gamma_x: float = 0.2
    gamma_y: float = 0.2
    gamma_z: float = 0.0
    m: float = 2.04
    radius: int = 10
    target_id: str = "T005"


def pauli_matrices() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    sx = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=np.complex128)
    sy = np.array([[0.0, -1.0j], [1.0j, 0.0]], dtype=np.complex128)
    sz = np.array([[1.0, 0.0], [0.0, -1.0]], dtype=np.complex128)
    return sx, sy, sz


def square_hamiltonian(params: SquareParams) -> np.ndarray:
    """Return the real-space square-geometry Hamiltonian used for Fig. 1/2."""

    return square_hamiltonian_sparse(params).toarray()


def square_hamiltonian_sparse(params: SquareParams) -> sp.csr_matrix:
    """Return the sparse real-space square Hamiltonian used for Fig. 2."""

    if params.L <= 0:
        raise ValueError("L must be positive")

    sx, sy, sz = pauli_matrices()
    onsite = (
        params.m * sz
        + 1.0j * params.gamma_x * sx
        + 1.0j * params.gamma_y * sy
        + 1.0j * params.gamma_z * sz
    )
    x_hopping = -0.5 * params.t_x * sz - 0.5j * params.v_x * sx
    y_hopping = -0.5 * params.t_y * sz - 0.5j * params.v_y * sy

    blocks: list[np.ndarray] = []
    row_indices: list[int] = []
    col_indices: list[int] = []

    def site_start(x_index: int, y_index: int) -> int:
        return 2 * (y_index * params.L + x_index)

    def add_block(row_start: int, col_start: int, block: np.ndarray) -> None:
        for local_row in range(2):
            for local_col in range(2):
                value = block[local_row, local_col]
                if value != 0:
                    row_indices.append(row_start + local_row)
                    col_indices.append(col_start + local_col)
                    blocks.append(np.asarray(value, dtype=np.complex128))

    for y_index in range(params.L):
        for x_index in range(params.L):
            start = site_start(x_index, y_index)
            add_block(start, start, onsite)
            if x_index + 1 < params.L:
                next_start = site_start(x_index + 1, y_index)
                add_block(start, next_start, x_hopping)
                add_block(next_start, start, x_hopping.conj().T)
            if y_index + 1 < params.L:
                next_start = site_start(x_index, y_index + 1)
                add_block(start, next_start, y_hopping)
                add_block(next_start, start, y_hopping.conj().T)

    size = 2 * params.L * params.L
    values = np.asarray(blocks, dtype=np.complex128)
    return sp.csr_matrix((values, (row_indices, col_indices)), shape=(size, size))


def fig2_square_parameter_sets(L: int = 30) -> dict[str, SquareParams]:
    """Return the two square-geometry parameter points used in Fig. 2."""

    return {
        "fig2a": SquareParams(
            L=L,
            m=2.2121,
            gamma_x=0.15,
            gamma_y=0.15,
            gamma_z=0.0,
            target_id="T004",
        ),
        "fig2b": SquareParams(
            L=L,
            m=1.7879,
            gamma_x=0.15,
            gamma_y=0.15,
            gamma_z=0.0,
            target_id="T004",
        ),
    }


def square_parameter_label(params: SquareParams) -> str:
    if abs(params.m - 2.2121) < 1e-6:
        return "fig2a"
    if abs(params.m - 1.7879) < 1e-6:
        return "fig2b"
    return f"m={params.m:g},gamma={params.gamma_x:g},L={params.L}"


def square_initial_wavepacket(params: SquareParams) -> np.ndarray:
    """Return the normalized Gaussian initial state from the Fig. 2 caption."""

    if params.L <= 0:
        raise ValueError("L must be positive")
    center_x = 15.0 if params.L >= 15 else (params.L + 1) / 2.0
    center_y = 1.0
    values = np.zeros(2 * params.L * params.L, dtype=np.complex128)
    spinor = np.asarray([1.0, 1.0], dtype=np.complex128)
    for y_index in range(params.L):
        y = y_index + 1
        for x_index in range(params.L):
            x = x_index + 1
            envelope = np.exp(-((x - center_x) ** 2) / 40.0 - ((y - center_y) ** 2) / 10.0)
            start = 2 * (y_index * params.L + x_index)
            values[start : start + 2] = envelope * spinor
    norm = np.linalg.norm(values)
    if norm <= 0:
        raise ValueError("initial wavepacket has zero norm")
    return values / norm


def square_site_intensity(state: np.ndarray, L: int) -> np.ndarray:
    """Return normalized site intensity from a two-component square state."""

    expected = 2 * L * L
    if state.shape[0] != expected:
        raise ValueError("state length must be 2 * L * L")
    intensity = np.abs(state.reshape(L, L, 2)) ** 2
    intensity = intensity.sum(axis=2)
    total = float(intensity.sum())
    if total <= 0:
        return intensity
    return intensity / total


def square_wavepacket_snapshots(
    params: SquareParams,
    times: Iterable[float] = (0.0, 5.0, 20.0),
) -> list[dict[str, float | str]]:
    """Generate normalized Fig. 2 wave-packet intensity rows."""

    hamiltonian = square_hamiltonian_sparse(params)
    initial_state = square_initial_wavepacket(params)
    label = square_parameter_label(params)
    rows: list[dict[str, float | str]] = []
    for time in [float(value) for value in times]:
        if abs(time) < 1e-14:
            state = initial_state
        else:
            state = spla.expm_multiply((-1.0j * time) * hamiltonian, initial_state)
        intensity = square_site_intensity(np.asarray(state), params.L)
        for y_index in range(params.L):
            for x_index in range(params.L):
                rows.append(
                    {
                        "target_id": params.target_id,
                        "series_id": f"{label}_wavepacket",
                        "parameter_set": label,
                        "time": time,
                        "x": float(x_index + 1),
                        "y": float(y_index + 1),
                        "intensity": float(intensity[y_index, x_index]),
                        "source": "independent_numerics",
                    }
                )
    return rows


def lowest_square_eigenvalues(
    params: SquareParams,
    eigen_count: int = 22,
) -> np.ndarray:
    """Return eigenvalues closest to zero for the square open-boundary system."""

    if eigen_count <= 0:
        raise ValueError("eigen_count must be positive")
    size = 2 * params.L * params.L
    hamiltonian = square_hamiltonian_sparse(params)
    if size <= max(80, eigen_count + 2):
        eigenvalues = np.linalg.eigvals(hamiltonian.toarray())
    else:
        k = min(eigen_count, size - 2)
        eigenvalues = spla.eigs(hamiltonian, k=k, sigma=0.0, return_eigenvectors=False)
    order = np.lexsort((eigenvalues.imag, np.abs(eigenvalues.real)))
    selected = eigenvalues[order[:eigen_count]]
    return selected[np.argsort(selected.real)]


def generate_square_spectrum_rows(
    parameter_sets: dict[str, SquareParams],
    eigen_count: int = 22,
) -> list[dict[str, float | int | str]]:
    """Generate low-energy square spectra rows for both Fig. 2 parameter sets."""

    rows: list[dict[str, float | int | str]] = []
    for label, params in parameter_sets.items():
        for eigen_index, value in enumerate(lowest_square_eigenvalues(params, eigen_count)):
            rows.append(
                {
                    "target_id": params.target_id,
                    "series_id": f"{label}_low_energy",
                    "parameter_set": label,
                    "eigen_index": eigen_index,
                    "energy_real": float(value.real),
                    "energy_imag": float(value.imag),
                    "source": "independent_numerics",
                }
            )
    return rows


def fig_s2_gap_scaling_parameter_sets() -> dict[str, DiskParams]:
    """Return the three disk-geometry parameter points used in Fig. S2."""

    return {
        "fig_s2a": DiskParams(m=2.2000),
        "fig_s2b": DiskParams(m=2.0800),
        "fig_s2c": DiskParams(m=2.0400),
    }


def disk_lattice_sites(radius: int) -> tuple[tuple[int, int], ...]:
    """Return integer disk sites obeying x^2 + y^2 <= radius^2."""

    if radius <= 0:
        raise ValueError("radius must be positive")
    radius_squared = radius * radius
    sites = [
        (x, y)
        for y in range(-radius, radius + 1)
        for x in range(-radius, radius + 1)
        if x * x + y * y <= radius_squared
    ]
    return tuple(sites)


def disk_hamiltonian_sparse(params: DiskParams) -> sp.csr_matrix:
    """Return the sparse open-boundary disk Hamiltonian for Fig. S2."""

    sites = disk_lattice_sites(params.radius)
    site_index = {site: index for index, site in enumerate(sites)}
    sx, sy, sz = pauli_matrices()
    onsite = (
        params.m * sz
        + 1.0j * params.gamma_x * sx
        + 1.0j * params.gamma_y * sy
        + 1.0j * params.gamma_z * sz
    )
    x_hopping = -0.5 * params.t_x * sz - 0.5j * params.v_x * sx
    y_hopping = -0.5 * params.t_y * sz - 0.5j * params.v_y * sy

    values: list[complex] = []
    row_indices: list[int] = []
    col_indices: list[int] = []

    def add_block(row_site: tuple[int, int], col_site: tuple[int, int], block: np.ndarray) -> None:
        row_start = 2 * site_index[row_site]
        col_start = 2 * site_index[col_site]
        for local_row in range(2):
            for local_col in range(2):
                value = block[local_row, local_col]
                if value != 0:
                    row_indices.append(row_start + local_row)
                    col_indices.append(col_start + local_col)
                    values.append(complex(value))

    for site in sites:
        x, y = site
        add_block(site, site, onsite)
        x_neighbor = (x + 1, y)
        if x_neighbor in site_index:
            add_block(site, x_neighbor, x_hopping)
            add_block(x_neighbor, site, x_hopping.conj().T)
        y_neighbor = (x, y + 1)
        if y_neighbor in site_index:
            add_block(site, y_neighbor, y_hopping)
            add_block(y_neighbor, site, y_hopping.conj().T)

    size = 2 * len(sites)
    return sp.csr_matrix((values, (row_indices, col_indices)), shape=(size, size))


def square_gap_square(params: SquareParams, eigen_count: int = 8) -> float:
    """Return min |E|^2 for a finite square open-boundary spectrum near zero."""

    values = lowest_square_eigenvalues(params, eigen_count=eigen_count)
    return float(np.min(np.abs(values)) ** 2)


def disk_gap_square(params: DiskParams, eigen_count: int = 8) -> float:
    """Return min |E|^2 for a finite disk spectrum near zero energy."""

    if eigen_count <= 0:
        raise ValueError("eigen_count must be positive")
    hamiltonian = disk_hamiltonian_sparse(params)
    size = hamiltonian.shape[0]
    if size <= max(80, eigen_count + 2):
        eigenvalues = np.linalg.eigvals(hamiltonian.toarray())
    else:
        k = min(eigen_count, size - 2)
        eigenvalues = spla.eigs(hamiltonian, k=k, sigma=0.0, return_eigenvectors=False)
    return float(np.min(np.abs(eigenvalues)) ** 2)


def generate_disk_gap_scaling_rows(
    parameter_sets: dict[str, DiskParams],
    radii: Iterable[int],
    *,
    eigen_count: int = 8,
) -> list[dict[str, float | int | str]]:
    """Generate Fig. S2 finite-size gap-square rows for disk geometry."""

    radius_values = [int(value) for value in radii]
    if not radius_values:
        raise ValueError("at least one radius is required")
    rows: list[dict[str, float | int | str]] = []
    for label, base_params in parameter_sets.items():
        for radius in radius_values:
            params = DiskParams(
                t_x=base_params.t_x,
                t_y=base_params.t_y,
                v_x=base_params.v_x,
                v_y=base_params.v_y,
                gamma_x=base_params.gamma_x,
                gamma_y=base_params.gamma_y,
                gamma_z=base_params.gamma_z,
                m=base_params.m,
                radius=radius,
                target_id=base_params.target_id,
            )
            rows.append(
                {
                    "target_id": params.target_id,
                    "series_id": f"{label}_gap_square",
                    "parameter_set": label,
                    "m": float(params.m),
                    "radius": radius,
                    "inverse_radius_square": float(1.0 / (radius * radius)),
                    "gap_square": disk_gap_square(params, eigen_count=eigen_count),
                    "source": "independent_numerics",
                }
            )
    return rows


def fit_gap_scaling_by_mass(
    rows: list[dict[str, float | int | str]],
) -> dict[str, dict[str, float | str]]:
    """Fit gap_square = intercept + slope / L^2 for each Fig. S2 mass."""

    parameter_sets = sorted({str(row["parameter_set"]) for row in rows})
    fits: dict[str, dict[str, float | str]] = {}
    for label in parameter_sets:
        selected = [row for row in rows if row["parameter_set"] == label]
        if len(selected) < 2:
            raise ValueError("at least two radii are required for a linear fit")
        x_values = np.asarray([float(row["inverse_radius_square"]) for row in selected], dtype=float)
        y_values = np.asarray([float(row["gap_square"]) for row in selected], dtype=float)
        slope, intercept = np.polyfit(x_values, y_values, deg=1)
        fits[label] = {
            "target_id": str(selected[0].get("target_id", "T005")),
            "parameter_set": label,
            "m": float(selected[0]["m"]),
            "intercept": float(intercept),
            "slope": float(slope),
            "source": "linear_fit_to_independent_numerics",
        }
    return fits


def open_boundary_bloch_phase_boundaries(
    gamma: float,
    *,
    gamma_y: float | None = None,
    t_x: float = 1.0,
    t_y: float = 1.0,
) -> tuple[float, float]:
    """Return the ordinary Bloch phase-boundary fan for the main model."""

    gy = gamma if gamma_y is None else gamma_y
    width = float(np.sqrt(gamma**2 + gy**2))
    center = t_x + t_y
    return center - width, center + width


def open_boundary_non_bloch_phase_boundary(
    gamma: float,
    *,
    gamma_y: float | None = None,
    t_x: float = 1.0,
    t_y: float = 1.0,
    v_x: float = 1.0,
    v_y: float = 1.0,
) -> float:
    """Return the low-energy non-Bloch phase boundary for Fig. 1."""

    gy = gamma if gamma_y is None else gamma_y
    return float(
        t_x
        + t_y
        + t_x * gamma**2 / (2.0 * v_x**2)
        + t_y * gy**2 / (2.0 * v_y**2)
    )


def source_disk_numerical_boundary_points() -> tuple[tuple[float, float], ...]:
    """Return the supplemental numerical boundary table used as a reference."""

    return (
        (0.05, 2.0025),
        (0.10, 2.0100),
        (0.15, 2.0225),
        (0.20, 2.0400),
        (0.25, 2.0625),
        (0.30, 2.0885),
        (0.35, 2.1200),
        (0.40, 2.1540),
        (0.45, 2.1940),
        (0.50, 2.2360),
    )


def source_disk_numerical_boundary(gamma: float) -> float:
    """Interpolate the supplemental open-boundary numerical phase boundary."""

    points = source_disk_numerical_boundary_points()
    gamma_values = np.asarray([point[0] for point in points], dtype=float)
    m_values = np.asarray([point[1] for point in points], dtype=float)
    if gamma <= gamma_values[0]:
        return float(open_boundary_non_bloch_phase_boundary(gamma))
    if gamma >= gamma_values[-1]:
        return float(m_values[-1])
    return float(np.interp(gamma, gamma_values, m_values))


def generate_open_boundary_phase_diagram_rows(
    gamma_values: Iterable[float],
    independent_boundary: dict[float, float] | None = None,
) -> list[dict[str, float | str]]:
    """Generate the Fig. 1 phase-diagram objects with explicit provenance.

    ``independent_boundary`` maps gamma to the m* transition computed from
    finite-size open-boundary spectra (see run_independent_obc_boundary.py).
    When provided it is emitted as its own series so the rendered red curve
    can come from independent numerics with the source table as reference.
    """

    rows: list[dict[str, float | str]] = []
    for gamma, m_star in sorted((independent_boundary or {}).items()):
        rows.append(
            {
                "target_id": "T003",
                "series_id": "independent_numerical_boundary",
                "gamma": float(gamma),
                "m": float(m_star),
                "region": "open_boundary_transition",
                "source": "independent_finite_size_extrapolation",
            }
        )
    for gamma in [float(value) for value in gamma_values]:
        lower_bloch, upper_bloch = open_boundary_bloch_phase_boundaries(gamma)
        theory_boundary = open_boundary_non_bloch_phase_boundary(gamma)
        numerical_reference = source_disk_numerical_boundary(gamma)
        rows.extend(
            [
                {
                    "target_id": "T003",
                    "series_id": "bloch_boundary_lower",
                    "gamma": gamma,
                    "m": lower_bloch,
                    "region": "bloch_gap_closing",
                    "source": "analytic_bloch_reference",
                },
                {
                    "target_id": "T003",
                    "series_id": "bloch_boundary_upper",
                    "gamma": gamma,
                    "m": upper_bloch,
                    "region": "bloch_gap_closing",
                    "source": "analytic_bloch_reference",
                },
                {
                    "target_id": "T003",
                    "series_id": "non_bloch_theory_boundary",
                    "gamma": gamma,
                    "m": theory_boundary,
                    "region": "non_bloch_transition",
                    "source": "analytic_non_bloch_low_energy",
                },
                {
                    "target_id": "T003",
                    "series_id": "source_numerical_boundary",
                    "gamma": gamma,
                    "m": numerical_reference,
                    "region": "open_boundary_transition",
                    "source": "supplement_disk_table_reference",
                },
            ]
        )

    marker_gamma = 0.15
    lower_marker, upper_marker = open_boundary_bloch_phase_boundaries(marker_gamma)
    rows.extend(
        [
            {
                "target_id": "T003",
                "series_id": "fig2_marker_star",
                "gamma": marker_gamma,
                "m": lower_marker,
                "region": "topological_example_for_fig2b",
                "source": "main_text_fig2_caption",
            },
            {
                "target_id": "T003",
                "series_id": "fig2_marker_square",
                "gamma": marker_gamma,
                "m": upper_marker,
                "region": "trivial_example_for_fig2a",
                "source": "main_text_fig2_caption",
            },
        ]
    )
    return rows


def generate_disk_phase_diagram_rows(
    gamma_values: Iterable[float],
    independent_boundary: dict[float, float] | None = None,
) -> list[dict[str, float | str]]:
    """Generate Supplemental Fig. S3 disk phase-diagram objects.

    ``independent_boundary`` maps gamma to the m* transition computed from
    disk finite-size spectra; when provided it is emitted as its own series
    so the red curve can come from independent numerics.
    """

    rows: list[dict[str, float | str]] = []
    for gamma, m_star in sorted((independent_boundary or {}).items()):
        rows.append(
            {
                "target_id": "T006",
                "series_id": "independent_numerical_boundary",
                "gamma": float(gamma),
                "m": float(m_star),
                "region": "disk_open_boundary_transition",
                "source": "independent_finite_size_extrapolation",
            }
        )
    for gamma in [float(value) for value in gamma_values]:
        lower_bloch, upper_bloch = open_boundary_bloch_phase_boundaries(gamma)
        theory_boundary = open_boundary_non_bloch_phase_boundary(gamma)
        numerical_reference = source_disk_numerical_boundary(gamma)
        rows.extend(
            [
                {
                    "target_id": "T006",
                    "series_id": "bloch_boundary_lower",
                    "gamma": gamma,
                    "m": lower_bloch,
                    "region": "bloch_gap_closing",
                    "source": "analytic_bloch_reference",
                },
                {
                    "target_id": "T006",
                    "series_id": "bloch_boundary_upper",
                    "gamma": gamma,
                    "m": upper_bloch,
                    "region": "bloch_gap_closing",
                    "source": "analytic_bloch_reference",
                },
                {
                    "target_id": "T006",
                    "series_id": "non_bloch_theory_boundary",
                    "gamma": gamma,
                    "m": theory_boundary,
                    "region": "non_bloch_transition",
                    "source": "analytic_non_bloch_low_energy",
                },
                {
                    "target_id": "T006",
                    "series_id": "source_disk_numerical_boundary",
                    "gamma": gamma,
                    "m": numerical_reference,
                    "region": "disk_open_boundary_transition",
                    "source": "supplement_disk_table_reference",
                },
            ]
        )
    return rows


def cylinder_hamiltonian(kx: float, params: CylinderParams) -> np.ndarray:
    if params.L_y <= 0:
        raise ValueError("L_y must be positive")

    sx, sy, sz = pauli_matrices()
    onsite = (
        (params.v_x * np.sin(kx) + 1.0j * params.gamma_x) * sx
        + 1.0j * params.gamma_y * sy
        + (params.m - params.t_x * np.cos(kx) + 1.0j * params.gamma_z) * sz
    )
    forward_hopping = -0.5 * params.t_y * sz - 0.5j * params.v_y * sy
    reverse_hopping = forward_hopping.conj().T

    size = 2 * params.L_y
    hamiltonian = np.zeros((size, size), dtype=np.complex128)
    for y_index in range(params.L_y):
        start = 2 * y_index
        hamiltonian[start : start + 2, start : start + 2] = onsite
        if y_index + 1 < params.L_y:
            next_start = start + 2
            hamiltonian[start : start + 2, next_start : next_start + 2] = (
                forward_hopping
            )
            hamiltonian[next_start : next_start + 2, start : start + 2] = reverse_hopping

    return hamiltonian


def non_bloch_cylinder_radius(kx: float, params: CylinderParams) -> float:
    """Return the equal-modulus bulk radius for the open-y cylinder."""

    numerator = params.m - params.t_x * np.cos(kx) + params.gamma_y
    denominator = params.m - params.t_x * np.cos(kx) - params.gamma_y
    if abs(denominator) < 1e-14:
        raise ValueError("non-Bloch cylinder radius is singular at this kx")
    return float(np.sqrt(abs(numerator / denominator)))


def non_bloch_cylinder_hamiltonian(
    kx: float, ky_tilde: float, params: CylinderParams
) -> np.ndarray:
    """Return the 2x2 non-Bloch cylinder bulk Hamiltonian.

    The open-y continuum obeys |beta_1(E)|=|beta_2(E)|. For this model that
    gives beta=r(kx) exp(i ky_tilde), with r(kx) from the supplement.
    """

    sx, sy, sz = pauli_matrices()
    beta = non_bloch_cylinder_radius(kx, params) * np.exp(1.0j * ky_tilde)
    sin_ky = (beta - beta**-1) / (2.0j)
    cos_ky = (beta + beta**-1) / 2.0
    return (
        (params.v_x * np.sin(kx) + 1.0j * params.gamma_x) * sx
        + (params.v_y * sin_ky + 1.0j * params.gamma_y) * sy
        + (
            params.m
            - params.t_x * np.cos(kx)
            - params.t_y * cos_ky
            + 1.0j * params.gamma_z
        )
        * sz
    )


def non_bloch_cylinder_bulk_eigenvalues(
    kx: float, params: CylinderParams, ky_points: int = 720
) -> np.ndarray:
    """Sample the non-Bloch cylinder bulk continuum at a fixed kx."""

    if ky_points <= 0:
        raise ValueError("ky_points must be positive")
    values: list[complex] = []
    for ky_tilde in np.linspace(-np.pi, np.pi, ky_points, endpoint=False):
        values.extend(
            np.linalg.eigvals(
                non_bloch_cylinder_hamiltonian(float(kx), float(ky_tilde), params)
            )
        )
    return np.asarray(values, dtype=np.complex128)


def cylinder_bloch_phase_boundaries(
    gamma: float, gamma_y: float | None = None, t_x: float = 1.0, t_y: float = 1.0
) -> tuple[float, float]:
    """Return the Bloch gap-closing lines shown as dotted curves in Fig. 3(a)."""

    return open_boundary_bloch_phase_boundaries(
        gamma, gamma_y=gamma_y, t_x=t_x, t_y=t_y
    )


def cylinder_non_bloch_gap_boundaries(gamma: float) -> tuple[float, float]:
    """Return the Fig. 3(a) non-Bloch cylinder band-touching boundaries.

    For the paper's symmetric main-model scan
    ``t_x=t_y=v_x=v_y=1`` and ``gamma_x=gamma_y=gamma``, the open-y GBZ gives
    ``beta=r(k_x) exp(i tilde{k}_y)``. The red cylinder boundary is the
    non-Bloch bulk band touching at ``kx=0, tilde{k}_y=0``.
    """

    gamma_abs = abs(float(gamma))
    lower = 1.0 + float(np.sqrt(1.0 - 2.0 * gamma_abs + 2.0 * gamma_abs**2))
    upper = 1.0 + float(np.sqrt(1.0 + 2.0 * gamma_abs + 2.0 * gamma_abs**2))
    return lower, upper


def _cylinder_boundary_distance(gamma: float, m: float) -> float:
    lower, upper = cylinder_non_bloch_gap_boundaries(gamma)
    if lower <= m <= upper:
        return 0.0
    return float(min(abs(m - lower), abs(m - upper)))


def cylinder_real_line_gap(
    gamma: float,
    m: float,
    *,
    kx_points: int = 61,
    ky_points: int = 61,
    params_template: CylinderParams | None = None,
) -> float:
    """Return the smallest separation from the Re(E)=0 band-separation line.

    This remains a diagnostic for band separability. The Fig. 3(a) phase
    boundary itself is generated from the analytic non-Bloch band-touching
    condition in :func:`cylinder_non_bloch_gap_boundaries`.
    """

    if kx_points <= 0 or ky_points <= 0:
        raise ValueError("kx_points and ky_points must be positive")
    base = params_template or CylinderParams()
    params = CylinderParams(
        t_x=base.t_x,
        t_y=base.t_y,
        v_x=base.v_x,
        v_y=base.v_y,
        gamma_x=gamma,
        gamma_y=gamma,
        gamma_z=base.gamma_z,
        m=m,
        L_y=base.L_y,
        target_id=base.target_id,
    )
    best_gap = float("inf")
    for kx in _momentum_grid_with_zero(kx_points):
        for ky_tilde in _momentum_grid_with_zero(ky_points):
            try:
                eigenvalues = np.linalg.eigvals(
                    non_bloch_cylinder_hamiltonian(
                        float(kx), float(ky_tilde), params
                    )
                )
            except ValueError:
                continue
            best_gap = min(best_gap, float(np.min(np.abs(eigenvalues.real))))
    return best_gap


def _momentum_grid_with_zero(points: int) -> np.ndarray:
    grid = np.linspace(-np.pi, np.pi, points, endpoint=False)
    if np.any(np.isclose(grid, 0.0)):
        return grid
    return np.sort(np.append(grid, 0.0))


def non_bloch_bulk_min_abs_energy(
    gamma: float,
    m: float,
    *,
    coarse_points: int = 201,
    refine_rounds: int = 3,
    params_template: CylinderParams | None = None,
) -> float:
    """Return min |E| of the non-Bloch bulk dispersion via closed form.

    Uses E^2 = dx^2 + dy^2 + dz^2 of the 2x2 non-Bloch Hamiltonian, evaluated
    on a dense momentum grid with local grid refinement around the minimum.
    This is an independent gaplessness probe: it does not use the analytic
    band-touching boundary formula.
    """

    base = params_template or CylinderParams()
    v_x, v_y = base.v_x, base.v_y
    t_x, t_y = base.t_x, base.t_y
    gamma_x = gamma_y = float(gamma)
    gamma_z = base.gamma_z

    def min_on_window(kx_lo: float, kx_hi: float, ky_lo: float, ky_hi: float, points: int) -> tuple[float, float, float]:
        kx = np.linspace(kx_lo, kx_hi, points)
        ky = np.linspace(ky_lo, ky_hi, points)
        kx_mesh, ky_mesh = np.meshgrid(kx, ky, indexing="ij")
        numerator = m - t_x * np.cos(kx_mesh) + gamma_y
        denominator = m - t_x * np.cos(kx_mesh) - gamma_y
        with np.errstate(divide="ignore", invalid="ignore"):
            radius = np.sqrt(np.abs(numerator / denominator))
            beta = radius * np.exp(1.0j * ky_mesh)
            sin_ky = (beta - beta**-1) / 2.0j
            cos_ky = (beta + beta**-1) / 2.0
            dx = v_x * np.sin(kx_mesh) + 1.0j * gamma_x
            dy = v_y * sin_ky + 1.0j * gamma_y
            dz = m - t_x * np.cos(kx_mesh) - t_y * cos_ky + 1.0j * gamma_z
            abs_energy = np.sqrt(np.abs(dx**2 + dy**2 + dz**2))
        abs_energy = np.where(np.isfinite(abs_energy), abs_energy, np.inf)
        flat_index = int(np.argmin(abs_energy))
        i, j = np.unravel_index(flat_index, abs_energy.shape)
        return float(abs_energy[i, j]), float(kx_mesh[i, j]), float(ky_mesh[i, j])

    best, kx_best, ky_best = min_on_window(-np.pi, np.pi, -np.pi, np.pi, coarse_points)
    window = 2.0 * np.pi / coarse_points
    for _ in range(refine_rounds):
        value, kx_best, ky_best = min_on_window(
            kx_best - window, kx_best + window, ky_best - window, ky_best + window, 81
        )
        best = min(best, value)
        window /= 40.0
    return best


def non_bloch_chern_number(
    gamma: float,
    m: float,
    *,
    kx_points: int = 41,
    ky_points: int = 41,
    gap_threshold: float = 0.12,
    params_template: CylinderParams | None = None,
) -> int | None:
    """Integrate the non-Bloch Chern number C_y directly on the deformed torus.

    Uses the Fukui-Hatsugai-Suzuki lattice construction with biorthogonal
    left/right link variables for the lower Re(E) band of the 2x2 non-Bloch
    cylinder Hamiltonian. Returns ``None`` when the real line gap closes on
    the sampled grid, where the band Chern number is undefined.

    The momentum grid is offset by an irrational fraction (1/pi) of a step:
    GBZ radius singularities sit at special angles that are rational
    multiples of pi (kx = 0, pi/2, pi, ...), and the irrational offset
    guarantees no grid point ever lands on one, for any grid size.
    """

    if kx_points <= 0 or ky_points <= 0:
        raise ValueError("kx_points and ky_points must be positive")
    base = params_template or CylinderParams()
    params = CylinderParams(
        t_x=base.t_x,
        t_y=base.t_y,
        v_x=base.v_x,
        v_y=base.v_y,
        gamma_x=gamma,
        gamma_y=gamma,
        gamma_z=base.gamma_z,
        m=m,
        L_y=base.L_y,
        target_id=base.target_id,
    )
    offset = 1.0 / np.pi
    kx_grid = -np.pi + (np.arange(kx_points) + offset) * (2.0 * np.pi / kx_points)
    ky_grid = -np.pi + (np.arange(ky_points) + offset) * (2.0 * np.pi / ky_points)

    right_vectors = np.empty((kx_points, ky_points, 2), dtype=np.complex128)
    left_vectors = np.empty((kx_points, ky_points, 2), dtype=np.complex128)
    min_real_gap = float("inf")
    for i, kx in enumerate(kx_grid):
        for j, ky_tilde in enumerate(ky_grid):
            h = non_bloch_cylinder_hamiltonian(float(kx), float(ky_tilde), params)
            eigenvalues, right = np.linalg.eig(h)
            left = np.linalg.inv(right)  # rows are biorthonormal left eigenvectors
            band = int(np.argmin(eigenvalues.real))
            min_real_gap = min(min_real_gap, float(abs(eigenvalues[band].real)))
            right_vectors[i, j] = right[:, band]
            left_vectors[i, j] = left[band, :]

    if min_real_gap < gap_threshold:
        return None

    def link(i: int, j: int, i2: int, j2: int) -> complex:
        value = complex(np.dot(left_vectors[i, j], right_vectors[i2, j2]))
        if value == 0:
            raise ValueError("biorthogonal link vanished; refine the momentum grid")
        return value

    total_flux = 0.0
    for i in range(kx_points):
        i_next = (i + 1) % kx_points
        for j in range(ky_points):
            j_next = (j + 1) % ky_points
            plaquette = (
                link(i, j, i_next, j)
                * link(i_next, j, i_next, j_next)
                / link(i, j_next, i_next, j_next)
                / link(i, j, i, j_next)
            )
            total_flux += float(np.angle(plaquette))

    return int(round(total_flux / (2.0 * np.pi)))


def classify_cylinder_phase_point(
    gamma: float,
    m: float,
    *,
    kx_points: int = 61,
    ky_points: int = 61,
    gap_threshold: float = 0.12,
) -> str:
    """Classify a Fig. 3(a) cylinder phase point."""

    lower, upper = cylinder_non_bloch_gap_boundaries(gamma)
    if lower <= m <= upper:
        return "gapless"
    return "chern_one" if m < 2.0 else "chern_zero"


def generate_cylinder_phase_diagram_rows(
    gamma_values: Iterable[float],
    m_values: Iterable[float],
    *,
    kx_points: int = 61,
    ky_points: int = 61,
    gap_threshold: float = 0.12,
) -> list[dict[str, float | str]]:
    """Generate the data objects used by the Fig. 3(a) cylinder phase diagram."""

    gamma_list = [float(value) for value in gamma_values]
    m_list = [float(value) for value in m_values]
    rows: list[dict[str, float | str]] = []

    for gamma in gamma_list:
        lower_bloch, upper_bloch = cylinder_bloch_phase_boundaries(gamma)
        lower_non_bloch, upper_non_bloch = cylinder_non_bloch_gap_boundaries(gamma)
        rows.append(
            {
                "target_id": "T002",
                "series_id": "bloch_boundary_lower",
                "gamma": gamma,
                "m": lower_bloch,
                "region": "bloch_gap_closing",
                "line_gap": float("nan"),
                "source": "analytic_reference",
            }
        )
        rows.append(
            {
                "target_id": "T002",
                "series_id": "bloch_boundary_upper",
                "gamma": gamma,
                "m": upper_bloch,
                "region": "bloch_gap_closing",
                "line_gap": float("nan"),
                "source": "analytic_reference",
            }
        )
        for branch, boundary_m in [
            ("lower", lower_non_bloch),
            ("upper", upper_non_bloch),
        ]:
            rows.append(
                {
                    "target_id": "T002",
                    "series_id": "non_bloch_gap_boundary",
                    "branch": branch,
                    "gamma": gamma,
                    "m": boundary_m,
                    "region": "non_bloch_band_touching",
                    "line_gap": 0.0,
                    "source": "analytic_non_bloch_boundary",
                }
            )

        for m in m_list:
            if lower_non_bloch <= m <= upper_non_bloch:
                region = "gapless"
            else:
                region = "chern_one" if m < 2.0 else "chern_zero"
            rows.append(
                {
                    "target_id": "T002",
                    "series_id": "cylinder_phase_region",
                    "gamma": gamma,
                    "m": m,
                    "region": region,
                    "line_gap": _cylinder_boundary_distance(gamma, m),
                    "source": "analytic_non_bloch_boundary",
                }
            )

    return rows


def edge_weights(
    eigenvector: np.ndarray, L_y: int, edge_layers: int | None = None
) -> tuple[float, float]:
    if L_y <= 0:
        raise ValueError("L_y must be positive")
    if eigenvector.shape[0] != 2 * L_y:
        raise ValueError("eigenvector length must be 2 * L_y")

    layers = edge_layers if edge_layers is not None else max(1, L_y // 10)
    layers = max(1, min(layers, L_y))

    probability_by_site = np.abs(eigenvector.reshape(L_y, 2)) ** 2
    probability_by_site = probability_by_site.sum(axis=1)
    norm = float(probability_by_site.sum())
    if norm <= 0.0:
        return 0.0, 0.0

    left_weight = float(probability_by_site[:layers].sum() / norm)
    right_weight = float(probability_by_site[-layers:].sum() / norm)
    return left_weight, right_weight


def classify_edge_state(
    left_weight: float, right_weight: float, threshold: float = 0.35
) -> str:
    left = left_weight >= threshold
    right = right_weight >= threshold
    if left and right:
        return "both_edges"
    if left:
        return "left_edge"
    if right:
        return "right_edge"
    return "bulk"


def parameter_label(params: CylinderParams) -> str:
    return (
        f"m={params.m:g},gamma_x={params.gamma_x:g},"
        f"gamma_y={params.gamma_y:g},gamma_z={params.gamma_z:g},Ly={params.L_y}"
    )


def generate_cylinder_spectrum_rows(
    kx_values: Iterable[float],
    params: CylinderParams,
    edge_layers: int | None = None,
    edge_threshold: float = 0.35,
) -> list[dict[str, float | int | str]]:
    rows: list[dict[str, float | int | str]] = []
    label = parameter_label(params)

    for kx_index, kx in enumerate(kx_values):
        hamiltonian = cylinder_hamiltonian(float(kx), params)
        eigenvalues, eigenvectors = np.linalg.eig(hamiltonian)
        order = np.lexsort((eigenvalues.imag, eigenvalues.real))

        for band_index, eigen_index in enumerate(order):
            energy = eigenvalues[eigen_index]
            left_weight, right_weight = edge_weights(
                eigenvectors[:, eigen_index], params.L_y, edge_layers=edge_layers
            )
            edge_label = classify_edge_state(left_weight, right_weight, edge_threshold)
            series_id = (
                "bulk_spectrum_all_kx"
                if edge_label == "bulk"
                else "edge_localization_candidate"
            )
            sort_key = kx_index * (2 * params.L_y) + band_index
            rows.append(
                {
                    "target_id": params.target_id,
                    "series_id": series_id,
                    "parameter_label": label,
                    "x": float(kx),
                    "y_real": float(energy.real),
                    "y_imag": float(energy.imag),
                    "y_abs": float(abs(energy)),
                    "branch_key": f"kx:{kx_index}:band:{band_index}",
                    "sort_key": sort_key,
                    "source": "independent_numerics",
                    "kx": float(kx),
                    "kx_index": kx_index,
                    "band_index": band_index,
                    "energy_real": float(energy.real),
                    "energy_imag": float(energy.imag),
                    "edge_label": edge_label,
                    "edge_weight_left": left_weight,
                    "edge_weight_right": right_weight,
                }
            )

    return rows
