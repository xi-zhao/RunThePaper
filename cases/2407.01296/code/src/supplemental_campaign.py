"""Clean-room numerical kernels for Fig. 2(d) and Supplementary Figs. S2/S4-S7.

Only equations and parameters printed in the paper/supplement are encoded.
Author notebooks, scripts, CSV files, and digitized figure curves are not
runtime inputs.  Underspecified geometry and observable conventions are kept
as explicit reconstruction choices in the JSON configuration.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence

import numpy as np
from scipy import linalg, sparse

from .geometry_adaptive import (
    HoppingModel,
    amoeba_potential,
    build_obc_hamiltonian,
    cut_coordinate_interval_sites,
    diamond_sites,
    full_spectrum,
    geometry_adaptive_potential,
    model_eq11,
    sparse_spectral_potential_grid,
    spectral_density_from_potential,
    square_sites,
    target_right_eigenstate,
)


def model_s17() -> dict[tuple[int, int], complex]:
    """Return the separable hopping model printed as Supplement Eq. (S17)."""

    return {
        (1, 0): 1.0,
        (-1, 0): 1.5,
        (2, 0): 0.5,
        (-2, 0): 2.0,
        (0, 1): 1.5,
        (0, -1): 1.0,
    }


def model_s27() -> dict[tuple[int, int], complex]:
    """Return the nonreciprocal coupled 2D model in Supplement Eq. (S27)."""

    return {
        (1, 0): 6.0,
        (-1, 0): -4.0,
        (0, 1): 6.0,
        (0, -1): -4.0,
        (1, 1): 0.5,
        (1, -1): 0.5,
        (-1, 1): 0.5,
        (-1, -1): 0.5,
    }


def _one_dimensional_obc(length: int, hoppings: dict[int, complex]) -> np.ndarray:
    if length <= 1:
        raise ValueError("length must exceed one")
    matrix = np.zeros((length, length), dtype=np.complex128)
    for displacement, amplitude in hoppings.items():
        if displacement == 0:
            matrix += amplitude * np.eye(length)
        elif displacement > 0:
            matrix += amplitude * np.diag(np.ones(length - displacement), displacement)
        else:
            matrix += amplitude * np.diag(np.ones(length + displacement), displacement)
    return matrix


def s17_separable_spectrum(length: int) -> np.ndarray:
    """Generate the exact L^2 square-OBC spectrum without an L^2 dense solve."""

    x_values = np.linalg.eigvals(
        _one_dimensional_obc(length, {1: 1.0, -1: 1.5, 2: 0.5, -2: 2.0})
    )
    y_values = np.linalg.eigvals(_one_dimensional_obc(length, {1: 1.5, -1: 1.0}))
    return (x_values[:, None] + y_values[None, :]).reshape(-1)


def s17_x_root_potential(energy: complex) -> float:
    """Evaluate Eq. (S20) from the two largest-modulus quartic roots."""

    roots = np.roots([0.5, 1.0, -complex(energy), 1.5, 2.0])
    moduli = np.sort(np.abs(roots))
    tiny = np.finfo(np.float64).tiny
    return float(
        np.log(0.5) + np.log(max(moduli[2], tiny)) + np.log(max(moduli[3], tiny))
    )


def s17_exact_potential_grid(
    real_axis: np.ndarray,
    imaginary_axis: np.ndarray,
    *,
    quadrature_points: int,
) -> np.ndarray:
    """Evaluate Eqs. (S19)-(S21) using the arcsine substitution."""

    theta = (np.arange(quadrature_points) + 0.5) * np.pi / quadrature_points
    y_energy = np.sqrt(6.0) * np.cos(theta)
    potential = np.empty((len(imaginary_axis), len(real_axis)), dtype=np.float64)
    for row, imaginary in enumerate(imaginary_axis):
        for column, real in enumerate(real_axis):
            energy = complex(float(real), float(imaginary))
            potential[row, column] = float(
                np.mean([s17_x_root_potential(energy - value) for value in y_energy])
            )
    return potential


def amoeba_potential_grid(
    real_axis: np.ndarray,
    imaginary_axis: np.ndarray,
    hoppings: HoppingModel,
    *,
    momentum_samples: int,
    tolerance: float,
) -> np.ndarray:
    values = np.empty((len(imaginary_axis), len(real_axis)), dtype=np.float64)
    for row, imaginary in enumerate(imaginary_axis):
        for column, real in enumerate(real_axis):
            values[row, column] = amoeba_potential(
                complex(float(real), float(imaginary)),
                hoppings,
                momentum_samples=momentum_samples,
                tolerance=tolerance,
            ).potential
    return values


def geometry_adaptive_density_grid(
    real_axis: np.ndarray,
    imaginary_axis: np.ndarray,
    hoppings: HoppingModel,
    *,
    basis: str,
    momentum_samples: int,
    tolerance: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Evaluate Eq. (10) and its Poisson density on a declared energy grid."""

    potential = np.empty((len(imaginary_axis), len(real_axis)), dtype=np.float64)
    for row, imaginary in enumerate(imaginary_axis):
        for column, real in enumerate(real_axis):
            potential[row, column] = geometry_adaptive_potential(
                complex(float(real), float(imaginary)),
                hoppings,
                basis=basis,
                momentum_samples=momentum_samples,
                tolerance=tolerance,
            ).potential
    density = spectral_density_from_potential(
        potential,
        real_step=float(real_axis[1] - real_axis[0]),
        imaginary_step=float(imaginary_axis[1] - imaginary_axis[0]),
    )
    return potential, density


def normalized_state_width(
    coordinates: np.ndarray,
    density: np.ndarray,
    *,
    basis: str,
) -> float:
    """Return the RMS broadening normal to the selected square-cut edge."""

    points = np.asarray(coordinates, dtype=np.float64)
    probability = np.asarray(density, dtype=np.float64)
    probability /= probability.sum()
    if basis == "x":
        coordinate = points[:, 0]
    elif basis == "diagonal":
        coordinate = (points[:, 0] + points[:, 1]) / np.sqrt(2.0)
    else:
        raise ValueError(f"unknown width basis: {basis}")
    mean = float(np.sum(probability * coordinate))
    return float(np.sqrt(np.sum(probability * (coordinate - mean) ** 2)))


def s17_amoeba_residual_surface(
    energy: complex,
    deformation_axis: np.ndarray,
    *,
    momentum_samples: int,
) -> np.ndarray:
    """Approximate the S2(d) amoeba by min_k |H(exp(mu+ik))-E|."""

    momentum = (np.arange(momentum_samples) + 0.5) * 2.0 * np.pi / momentum_samples
    unit = np.exp(1.0j * momentum)
    result = np.empty((len(deformation_axis), len(deformation_axis)), dtype=np.float64)
    hoppings = model_s17()
    for row, mu_y in enumerate(deformation_axis):
        beta_y = np.exp(float(mu_y)) * unit[:, None]
        for column, mu_x in enumerate(deformation_axis):
            beta_x = np.exp(float(mu_x)) * unit[None, :]
            characteristic = np.full(
                (momentum_samples, momentum_samples),
                -complex(energy),
                dtype=np.complex128,
            )
            for (dx, dy), amplitude in hoppings.items():
                characteristic += amplitude * beta_x**dx * beta_y**dy
            result[row, column] = float(np.min(np.abs(characteristic)))
    return result


def s24_hamiltonian(
    length: int,
    *,
    delta: float = 0.01,
    t1_left: float = 0.5,
    t1_right: float = 1.0,
    t2_left: float = 1.0,
    t2_right: float = 0.5,
    onsite_v: float = 0.5,
) -> sparse.csr_matrix:
    onsite = np.array([[onsite_v, delta], [delta, -onsite_v]], dtype=np.complex128)
    forward = np.diag([t1_right, t2_right]).astype(np.complex128)
    reverse = np.diag([t1_left, t2_left]).astype(np.complex128)
    return (
        sparse.kron(sparse.eye(length, format="csr"), onsite, format="csr")
        + sparse.kron(
            sparse.diags(np.ones(length - 1), 1, format="csr"), forward, format="csr"
        )
        + sparse.kron(
            sparse.diags(np.ones(length - 1), -1, format="csr"), reverse, format="csr"
        )
    )


def s24_bloch_spectrum(
    momentum_points: int, *, delta: float = 0.01
) -> tuple[np.ndarray, np.ndarray]:
    momentum = np.linspace(-np.pi, np.pi, momentum_points, endpoint=False)
    values = np.empty((momentum_points, 2), dtype=np.complex128)
    for index, k in enumerate(momentum):
        beta = np.exp(1.0j * k)
        matrix = np.array(
            [
                [0.5 / beta + beta + 0.5, delta],
                [delta, 1.0 / beta + 0.5 * beta - 0.5],
            ],
            dtype=np.complex128,
        )
        values[index] = np.linalg.eigvals(matrix)
    return momentum, values


def s24_winding(
    energy: complex, *, delta: float = 0.01, momentum_points: int = 2048
) -> int:
    momentum, bands = s24_bloch_spectrum(momentum_points, delta=delta)
    del momentum
    determinant = (bands[:, 0] - energy) * (bands[:, 1] - energy)
    closed = np.append(determinant, determinant[0])
    return int(np.rint(np.sum(np.angle(closed[1:] / closed[:-1])) / (2.0 * np.pi)))


def s24_state_profiles(
    length: int, *, delta: float = 0.01
) -> dict[str, np.ndarray | complex]:
    matrix = s24_hamiltonian(length, delta=delta).toarray()
    values, vectors = np.linalg.eig(matrix)
    indices = {
        "largest_real": int(np.argmax(values.real)),
        "largest_imaginary": int(np.argmax(values.imag)),
    }
    result: dict[str, np.ndarray | complex] = {}
    for name, index in indices.items():
        vector = vectors[:, index]
        density = np.sum(np.abs(vector.reshape(length, 2)) ** 2, axis=1)
        density /= density.sum()
        result[f"{name}_density"] = density
        result[f"{name}_eigenvalue"] = complex(values[index])
    return result


def bloch_value(hoppings: HoppingModel, kx: np.ndarray, ky: np.ndarray) -> np.ndarray:
    value = np.zeros(
        np.broadcast_shapes(np.shape(kx), np.shape(ky)), dtype=np.complex128
    )
    for (dx, dy), amplitude in hoppings.items():
        value += complex(amplitude) * np.exp(1.0j * (dx * kx + dy * ky))
    return value


def _closed_curve_winding(values: np.ndarray, energy: complex = 0.0j) -> int:
    shifted = np.asarray(values, dtype=np.complex128) - complex(energy)
    closed = np.append(shifted, shifted[0])
    if np.min(np.abs(closed)) < 1e-9:
        return 0
    return int(np.rint(np.sum(np.angle(closed[1:] / closed[:-1])) / (2.0 * np.pi)))


def directional_winding_rows(
    hoppings: HoppingModel,
    *,
    basis: str,
    transverse_points: int,
    path_points: int,
    energy: complex = 0.0j,
) -> list[dict[str, float | int | str]]:
    """Compute the square or diagonal winding maps used by Supplement Fig. S6."""

    transverse = (
        -np.pi + (np.arange(transverse_points) + 0.37) * 2.0 * np.pi / transverse_points
    )
    path = -np.pi + (np.arange(path_points) + 0.23) * 2.0 * np.pi / path_points
    rows: list[dict[str, float | int | str]] = []
    for fixed in transverse:
        if basis == "square_y":
            values = bloch_value(hoppings, np.full_like(path, fixed), path)
        elif basis == "diagonal_1m1":
            # k_parallel=(kx-ky)/2, k_perp=(kx+ky)/2.
            values = bloch_value(hoppings, path + fixed, fixed - path)
        else:
            raise ValueError(f"unknown winding basis: {basis}")
        rows.append(
            {
                "basis": basis,
                "transverse_momentum": float(fixed),
                "winding": _closed_curve_winding(values, energy),
            }
        )
    return rows


def geometry_sites(specification: dict[str, object]) -> tuple[tuple[int, int], ...]:
    kind = specification["kind"]
    if kind == "square":
        return square_sites(int(specification["length"]))
    if kind == "diamond":
        return diamond_sites(int(specification["radius"]))
    if kind == "cut_intervals":
        u = tuple(int(value) for value in specification["u_bounds"])
        v = tuple(int(value) for value in specification["v_bounds"])
        return cut_coordinate_interval_sites(u, v)
    raise ValueError(f"unknown geometry kind: {kind}")


def eigenvalues_with_backend(matrix: sparse.spmatrix, backend: str) -> np.ndarray:
    if backend == "spectrum_skipped":
        return np.empty(0, dtype=np.complex128)
    if backend == "numpy_dense":
        return full_spectrum(matrix)
    if backend == "cupy_dense":
        try:
            import cupy as cp
        except ImportError as exc:  # pragma: no cover - exercised on A100 host
            raise RuntimeError(
                "cupy_dense backend requires CuPy on the GPU host"
            ) from exc
        values = cp.linalg.eigvals(cp.asarray(matrix.toarray()))
        return cp.asnumpy(values)
    raise ValueError(f"unknown eigensolver backend: {backend}")


def s5_geometry_result(
    specification: dict[str, object],
    *,
    backend: str,
    target_energies: Sequence[complex],
) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    sites = geometry_sites(specification)
    matrix = build_obc_hamiltonian(sites, model_s27())
    eigenvalues = eigenvalues_with_backend(matrix, backend)
    arrays: dict[str, np.ndarray] = {"coordinates": np.asarray(sites, dtype=np.int64)}
    for index, energy in enumerate(target_energies):
        state = target_right_eigenstate(matrix, complex(energy), candidate_count=4)
        density = np.abs(state.right_eigenvector) ** 2
        density /= density.sum()
        arrays[f"state_{index}_density"] = density
        arrays[f"state_{index}_eigenvalue"] = np.asarray(state.eigenvalue)
        arrays[f"state_{index}_residual"] = np.asarray(state.normalized_residual)
    return eigenvalues, arrays


def independent_fig2d_rows(
    geometries: Sequence[dict[str, object]],
    probes: np.ndarray,
    *,
    momentum_samples: int,
    tolerance: float,
) -> list[dict[str, float | int | str]]:
    """Generate Fig. 2(d) convergence without released ED tables."""

    rows: list[dict[str, float | int | str]] = []
    for specification in geometries:
        basis = str(specification["basis"])
        sites = geometry_sites(specification)
        matrix = build_obc_hamiltonian(sites, model_eq11())
        finite = sparse_spectral_potential_grid(matrix, probes)
        theory = np.asarray(
            [
                geometry_adaptive_potential(
                    complex(energy),
                    model_eq11(),
                    basis=basis,
                    momentum_samples=momentum_samples,
                    tolerance=tolerance,
                ).potential
                for energy in probes
            ]
        )
        for index, (energy, finite_value, theory_value) in enumerate(
            zip(probes, finite, theory, strict=True)
        ):
            rows.append(
                {
                    "geometry": basis,
                    "size_label": str(specification["label"]),
                    "site_count": len(sites),
                    "probe_index": index,
                    "real_E": float(energy.real),
                    "imag_E": float(energy.imag),
                    "finite_potential": float(finite_value),
                    "theory_potential": float(theory_value),
                    "absolute_difference": float(abs(finite_value - theory_value)),
                }
            )
    return rows


def biorthogonal_first_order_disorder(
    matrix: sparse.spmatrix,
    disorder_vectors: Iterable[np.ndarray],
) -> list[dict[str, float]]:
    """Evaluate the printed first-order shift and two ambiguity-safe summaries."""

    dense = matrix.toarray()
    _, left, right = linalg.eig(dense, left=True, right=True, check_finite=False)
    overlap = np.sum(np.conjugate(left) * right, axis=0)
    if np.min(np.abs(overlap)) < 1e-12:
        raise RuntimeError("biorthogonal overlap is numerically singular")
    rows: list[dict[str, float]] = []
    for disorder in disorder_vectors:
        values = np.asarray(disorder, dtype=np.float64)
        shifts = np.sum(np.conjugate(left) * values[:, None] * right, axis=0) / overlap
        rows.append(
            {
                "mean_shift_real": float(np.mean(shifts).real),
                "mean_shift_imag": float(np.mean(shifts).imag),
                "magnitude_of_mean_shift": float(abs(np.mean(shifts))),
                "mean_shift_magnitude": float(np.mean(np.abs(shifts))),
            }
        )
    return rows
