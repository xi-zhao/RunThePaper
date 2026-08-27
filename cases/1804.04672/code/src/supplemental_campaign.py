"""Independent numerical kernels for Supplemental Figs. S4--S9.

The module only consumes the paper equations and an explicit JSON config.  It
does not read the paper PDF, original EPS panels, digitized curves, author
code, or author numerical arrays.  Missing plotting details for the skin-state
panels (system size and which "typical" eigenstates were selected) are exposed
as reconstruction parameters instead of being inferred from source pixels.
"""

from __future__ import annotations

from typing import Iterable

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla

from nonhermitian_chern import (
    DiskParams,
    SquareParams,
    disk_hamiltonian_sparse,
    disk_lattice_sites,
    pauli_matrices,
    square_gap_square,
    square_hamiltonian_sparse,
)


def s4_theory_boundary(family: str, gamma: float) -> float:
    """Return the two low-energy non-Bloch predictions printed for Fig. S4."""

    gamma = float(gamma)
    if family == "gamma_x_only":
        return 2.0 + 0.5 * gamma**2
    if family == "anisotropic_velocity":
        return 2.0 + 1.28125 * gamma**2
    raise ValueError(f"unknown S4 family: {family}")


def s4_bloch_boundaries(family: str, gamma: float) -> tuple[float, float]:
    """Return Bloch gap closings from the 2x2 Bloch Hamiltonian at k=(0,0)."""

    gamma = float(gamma)
    if family == "gamma_x_only":
        shift = abs(gamma)
    elif family == "anisotropic_velocity":
        # At k=0 the velocities do not enter the Bloch exceptional-point fan.
        shift = np.sqrt(2.0) * abs(gamma)
    else:
        raise ValueError(f"unknown S4 family: {family}")
    return 2.0 - float(shift), 2.0 + float(shift)


def s4_parameter_rows(gamma_values: Iterable[float]) -> list[dict[str, float | str]]:
    rows: list[dict[str, float | str]] = []
    for family in ("gamma_x_only", "anisotropic_velocity"):
        for gamma in gamma_values:
            lower, upper = s4_bloch_boundaries(family, gamma)
            rows.extend(
                [
                    {
                        "target_id": "T007",
                        "panel": family,
                        "series": "non_bloch_theory",
                        "gamma": float(gamma),
                        "m": s4_theory_boundary(family, gamma),
                    },
                    {
                        "target_id": "T007",
                        "panel": family,
                        "series": "bloch_lower",
                        "gamma": float(gamma),
                        "m": lower,
                    },
                    {
                        "target_id": "T007",
                        "panel": family,
                        "series": "bloch_upper",
                        "gamma": float(gamma),
                        "m": upper,
                    },
                ]
            )
    return rows


def _s4_params(family: str, gamma: float, m: float, size: int) -> SquareParams:
    if family == "gamma_x_only":
        return SquareParams(
            L=size,
            m=m,
            gamma_x=gamma,
            gamma_y=0.0,
            v_x=1.0,
            v_y=1.0,
            target_id="T007",
        )
    if family == "anisotropic_velocity":
        return SquareParams(
            L=size,
            m=m,
            gamma_x=gamma,
            gamma_y=gamma,
            v_x=0.8,
            v_y=1.0,
            target_id="T007",
        )
    raise ValueError(f"unknown S4 family: {family}")


def s4_finite_size_scan(
    families: Iterable[str],
    gamma_values: Iterable[float],
    sizes: Iterable[int],
    m_offsets: Iterable[float],
) -> list[dict[str, float | int | str]]:
    """Independently scan the S4 transition using finite-square spectra.

    The returned thermodynamic intercept is obtained by fitting min|E|^2
    against 1/L^2.  Locating the root is deliberately left to aggregation so
    every computed point and its finite-size provenance remain visible.
    """

    sizes = tuple(int(value) for value in sizes)
    if len(sizes) < 2:
        raise ValueError("S4 finite-size scan needs at least two sizes")
    rows: list[dict[str, float | int | str]] = []
    inverse_size_square = np.asarray([1.0 / size**2 for size in sizes])
    for family in families:
        for gamma in gamma_values:
            theory = s4_theory_boundary(family, gamma)
            for offset in m_offsets:
                m = theory + float(offset)
                gaps = np.asarray(
                    [
                        square_gap_square(_s4_params(family, float(gamma), m, size), eigen_count=6)
                        for size in sizes
                    ]
                )
                slope, intercept = np.polyfit(inverse_size_square, gaps, deg=1)
                rows.append(
                    {
                        "target_id": "T007",
                        "panel": family,
                        "gamma": float(gamma),
                        "m": float(m),
                        "theory_m": float(theory),
                        "intercept_gap_square": float(intercept),
                        "slope": float(slope),
                        "size_count": len(sizes),
                    }
                )
    return rows


def _right_eigenpairs_near(
    hamiltonian: sp.csr_matrix, shifts: Iterable[complex]
) -> list[tuple[complex, np.ndarray]]:
    size = hamiltonian.shape[0]
    pairs: list[tuple[complex, np.ndarray]] = []
    dense_cache: tuple[np.ndarray, np.ndarray] | None = None
    for shift in shifts:
        if size <= 180:
            if dense_cache is None:
                values, vectors = np.linalg.eig(hamiltonian.toarray())
                dense_cache = values, vectors
            values, vectors = dense_cache
            index = int(np.argmin(np.abs(values - shift)))
            value = complex(values[index])
            vector = vectors[:, index]
        else:
            values, vectors = spla.eigs(hamiltonian, k=1, sigma=complex(shift))
            value = complex(values[0])
            vector = vectors[:, 0]
        residual = np.linalg.norm(hamiltonian @ vector - value * vector) / max(
            np.linalg.norm(vector), 1e-15
        )
        if residual > 1e-6:
            raise RuntimeError(f"right-eigenvector residual too large: {residual}")
        pairs.append((value, np.asarray(vector, dtype=np.complex128)))
    return pairs


def _normalized_site_density(vector: np.ndarray) -> np.ndarray:
    density = np.sum(np.abs(vector.reshape(-1, 2)) ** 2, axis=1)
    total = float(density.sum())
    if not np.isfinite(total) or total <= 0:
        raise RuntimeError("invalid eigenstate density")
    return density / total


def skin_profile_arrays(
    *,
    square_size: int,
    disk_radius: int,
    shifts: Iterable[complex],
) -> tuple[dict[str, np.ndarray], list[dict[str, float | str]]]:
    """Generate the four S5 and four S6 reconstructed skin-state panels."""

    arrays: dict[str, np.ndarray] = {}
    summaries: list[dict[str, float | str]] = []
    shifts = tuple(complex(value) for value in shifts)
    for target_id, gamma_x, gamma_y in (
        ("T008", 0.15, 0.15),
        ("T009", 0.0, 0.15),
    ):
        square = SquareParams(
            L=square_size,
            m=2.2121,
            gamma_x=gamma_x,
            gamma_y=gamma_y,
            target_id=target_id,
        )
        disk = DiskParams(
            radius=disk_radius,
            m=2.2121,
            gamma_x=gamma_x,
            gamma_y=gamma_y,
            target_id=target_id,
        )
        for geometry, hamiltonian, coordinates in (
            (
                "square",
                square_hamiltonian_sparse(square),
                np.asarray(
                    [(x + 1, y + 1) for y in range(square_size) for x in range(square_size)],
                    dtype=float,
                ),
            ),
            (
                "disk",
                disk_hamiltonian_sparse(disk),
                np.asarray(disk_lattice_sites(disk_radius), dtype=float),
            ),
        ):
            arrays[f"{target_id}_{geometry}_coordinates"] = coordinates
            for state_index, (value, vector) in enumerate(
                _right_eigenpairs_near(hamiltonian, shifts)
            ):
                density = _normalized_site_density(vector)
                arrays[f"{target_id}_{geometry}_state_{state_index}_density"] = density
                center = density @ coordinates
                summaries.append(
                    {
                        "target_id": target_id,
                        "geometry": geometry,
                        "state_index": float(state_index),
                        "requested_shift_real": float(shifts[state_index].real),
                        "requested_shift_imag": float(shifts[state_index].imag),
                        "eigenvalue_real": float(value.real),
                        "eigenvalue_imag": float(value.imag),
                        "center_x": float(center[0]),
                        "center_y": float(center[1]),
                    }
                )
    return arrays, summaries


def exact_model_bloch_boundaries(gamma: float, t: float = 1.0) -> tuple[float, float]:
    center = t * (np.cosh(gamma) + np.cosh(gamma))
    radius = np.sqrt(2.0 * np.sinh(gamma) ** 2)
    return float(center - radius), float(center + radius)


def exact_model_phase_rows(gamma_values: Iterable[float], t: float = 1.0) -> list[dict[str, float | str]]:
    rows: list[dict[str, float | str]] = []
    for gamma in gamma_values:
        lower, upper = exact_model_bloch_boundaries(float(gamma), t=t)
        for series, m in (
            ("open_boundary_non_bloch", 2.0 * t),
            ("bloch_lower", lower),
            ("bloch_upper", upper),
        ):
            rows.append(
                {
                    "target_id": "T010",
                    "series": series,
                    "gamma": float(gamma),
                    "m": float(m),
                }
            )
    return rows


def exact_square_hamiltonian(
    *, length: int, gamma_x: float, gamma_y: float, m: float, t: float = 1.0
) -> sp.csr_matrix:
    """Return the open-square Hamiltonian printed in Supplement Sec. VI.

    The implementation is intentionally separate from the main-model square
    kernel: the exactly solvable model has asymmetric hopping amplitudes rather
    than imaginary onsite Zeeman fields.  Keeping the two Hamiltonians distinct
    prevents an apparently harmless parameter switch from changing the model.
    """

    if length <= 1:
        raise ValueError("length must exceed one")
    sx, sy, sz = pauli_matrices()
    onsite = float(m) * sz
    forward = {
        (1, 0): 0.5 * np.exp(-float(gamma_x)) * (-1.0j * sx - float(t) * sz),
        (0, 1): 0.5 * np.exp(-float(gamma_y)) * (-1.0j * sy - float(t) * sz),
    }
    reverse = {
        (1, 0): 0.5 * np.exp(float(gamma_x)) * (1.0j * sx - float(t) * sz),
        (0, 1): 0.5 * np.exp(float(gamma_y)) * (1.0j * sy - float(t) * sz),
    }
    site_count = length * length
    rows: list[int] = []
    columns: list[int] = []
    values: list[complex] = []

    def site_index(x: int, y: int) -> int:
        return y * length + x

    def add_block(row_site: int, column_site: int, block: np.ndarray) -> None:
        for local_row in range(2):
            for local_column in range(2):
                value = complex(block[local_row, local_column])
                if value != 0.0:
                    rows.append(2 * row_site + local_row)
                    columns.append(2 * column_site + local_column)
                    values.append(value)

    for y in range(length):
        for x in range(length):
            site = site_index(x, y)
            add_block(site, site, onsite)
            for displacement in ((1, 0), (0, 1)):
                nx, ny = x + displacement[0], y + displacement[1]
                if nx >= length or ny >= length:
                    continue
                neighbour = site_index(nx, ny)
                add_block(site, neighbour, forward[displacement])
                add_block(neighbour, site, reverse[displacement])
    dimension = 2 * site_count
    return sp.csr_matrix((values, (rows, columns)), shape=(dimension, dimension))


def exact_square_similarity_transform_residual(
    length: int, gamma_x: float, gamma_y: float, *, m: float = 1.8, t: float = 1.0
) -> float:
    """Check ``S^-1 H(gamma) S = H(0)`` for the full open square."""

    h = exact_square_hamiltonian(
        length=length, gamma_x=gamma_x, gamma_y=gamma_y, m=m, t=t
    ).toarray()
    h_zero = exact_square_hamiltonian(
        length=length, gamma_x=0.0, gamma_y=0.0, m=m, t=t
    ).toarray()
    scale_by_site = np.asarray(
        [
            np.exp(gamma_x * x + gamma_y * y)
            for y in range(length)
            for x in range(length)
        ],
        dtype=float,
    )
    scale = np.repeat(scale_by_site, 2)
    transformed = (h / scale[:, None]) * scale[None, :]
    return float(
        np.linalg.norm(transformed - h_zero) / max(np.linalg.norm(h_zero), 1e-15)
    )


def exact_cylinder_boundaries(gamma: float, t: float = 1.0) -> tuple[float, float]:
    return 1.0 + t * float(np.exp(-gamma)), 1.0 + t * float(np.exp(gamma))


def exact_cylinder_phase_rows(
    gamma_values: Iterable[float], t: float = 1.0
) -> list[dict[str, float | str]]:
    rows: list[dict[str, float | str]] = []
    for gamma in gamma_values:
        nb_lower, nb_upper = exact_cylinder_boundaries(float(gamma), t=t)
        bloch_lower, bloch_upper = exact_model_bloch_boundaries(float(gamma), t=t)
        for series, m in (
            ("non_bloch_lower", nb_lower),
            ("non_bloch_upper", nb_upper),
            ("bloch_lower", bloch_lower),
            ("bloch_upper", bloch_upper),
        ):
            rows.append(
                {
                    "target_id": "T011",
                    "series": series,
                    "gamma": float(gamma),
                    "m": float(m),
                }
            )
    return rows


def exact_cylinder_hamiltonian(
    kx: float, *, gamma_x: float, gamma_y: float, m: float, t: float, length_y: int
) -> sp.csr_matrix:
    if length_y <= 1:
        raise ValueError("length_y must exceed one")
    sx, sy, sz = pauli_matrices()
    complex_kx = complex(kx, gamma_x)
    onsite = np.sin(complex_kx) * sx + (m - t * np.cos(complex_kx)) * sz
    forward = 0.5 * np.exp(-gamma_y) * (-1.0j * sy - t * sz)
    reverse = 0.5 * np.exp(gamma_y) * (1.0j * sy - t * sz)
    return sp.kron(sp.eye(length_y, format="csr"), onsite, format="csr") + sp.kron(
        sp.diags(np.ones(length_y - 1), 1, format="csr"), forward, format="csr"
    ) + sp.kron(sp.diags(np.ones(length_y - 1), -1, format="csr"), reverse, format="csr")


def exact_cylinder_spectrum_arrays(
    *, gamma: float, m: float, t: float, length_y: int, kx_points: int
) -> dict[str, np.ndarray]:
    kx = np.linspace(-np.pi, np.pi, int(kx_points), endpoint=False)
    energies = np.empty((len(kx), 2 * length_y), dtype=np.complex128)
    for index, value in enumerate(kx):
        energies[index] = np.linalg.eigvals(
            exact_cylinder_hamiltonian(
                float(value),
                gamma_x=gamma,
                gamma_y=gamma,
                m=m,
                t=t,
                length_y=length_y,
            ).toarray()
        )
    return {"T011_kx": kx, "T011_energies": energies}


def similarity_transform_residual(length_y: int, gamma_y: float) -> float:
    """Check the exact cylinder's y-skin similarity transformation."""

    h = exact_cylinder_hamiltonian(
        0.37, gamma_x=0.2, gamma_y=gamma_y, m=1.7554, t=1.0, length_y=length_y
    ).toarray()
    h_zero = exact_cylinder_hamiltonian(
        0.37, gamma_x=0.2, gamma_y=0.0, m=1.7554, t=1.0, length_y=length_y
    ).toarray()
    site_scale = np.exp(gamma_y * np.arange(length_y))
    scale = np.repeat(site_scale, 2)
    transformed = (h / scale[:, None]) * scale[None, :]
    return float(np.linalg.norm(transformed - h_zero) / max(np.linalg.norm(h_zero), 1e-15))
