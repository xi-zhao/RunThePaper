"""Independent numerics for Supplementary Fig. S2 and Eqs. (S17)-(S22).

The model is separable, ``H(beta_x, beta_y) = Hx(beta_x) + Hy(beta_y)``.
That structure turns the nominal 5625-by-5625 diagonalization into two
75-by-75 diagonalizations and reduces both spectral-potential constructions
to one-dimensional quadratures.  No released curve or source-figure pixel is
an input to any function in this module.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import linalg, sparse
from scipy.ndimage import label
from scipy.spatial import cKDTree

from src.geometry_adaptive import HoppingModel, batched_polynomial_roots


@dataclass(frozen=True)
class SeparableSpectrum:
    """Open-boundary spectrum and its two one-dimensional factors."""

    eigenvalues: np.ndarray
    x_eigenvalues: np.ndarray
    y_eigenvalues: np.ndarray


@dataclass(frozen=True)
class AmoebaPotentialGrid:
    """Eq. (S15) minimum and its optimizing imaginary momenta."""

    potential: np.ndarray
    deformation_x: np.ndarray
    deformation_y: np.ndarray
    boundary_hits: int
    objective_evaluations_per_energy: int


@dataclass(frozen=True)
class AmoebaOrder:
    """Integer order of one complement component of the amoeba."""

    winding_x: int
    winding_y: int
    minimum_sampled_modulus: float


@dataclass(frozen=True)
class AmoebaHole:
    """One bounded component of the characteristic amoeba complement."""

    center_x: float
    center_y: float
    cell_count: int
    clearance: float
    order: AmoebaOrder

    @property
    def is_central(self) -> bool:
        """A central hole has the zero order vector from Eq. (S14)."""

        return self.order.winding_x == 0 and self.order.winding_y == 0


@dataclass(frozen=True)
class AmoebaRaster:
    """Formula-generated amoeba mask and its bounded complement holes."""

    deformation_x: np.ndarray
    deformation_y: np.ndarray
    distance_to_zero_locus: np.ndarray
    zero_locus_mask: np.ndarray
    holes: tuple[AmoebaHole, ...]


def model_s17() -> dict[tuple[int, int], complex]:
    """Laurent hoppings obtained by expanding Supplementary Eq. (S17)."""

    return {
        (1, 0): 1.0,
        (-1, 0): 1.5,
        (2, 0): 0.5,
        (-2, 0): 2.0,
        (0, 1): 1.5,
        (0, -1): 1.0,
    }


def hx(beta: complex | np.ndarray) -> np.ndarray:
    """The x-directed Laurent polynomial in Eq. (S18)."""

    value = np.asarray(beta, dtype=np.complex128)
    return value + 1.5 / value + 0.5 * value**2 + 2.0 / value**2


def hy(beta: complex | np.ndarray) -> np.ndarray:
    """The y-directed Laurent polynomial in Eq. (S18)."""

    value = np.asarray(beta, dtype=np.complex128)
    return 1.5 * value + 1.0 / value


def bloch_s17(
    momentum_x: float | np.ndarray,
    momentum_y: float | np.ndarray,
) -> np.ndarray:
    """Evaluate Eq. (S17) directly on real Bloch momenta."""

    kx = np.asarray(momentum_x, dtype=np.float64)
    ky = np.asarray(momentum_y, dtype=np.float64)
    return (
        5.0 * (np.cos(kx) + np.cos(2.0 * kx))
        - 1j * (np.sin(kx) + 3.0 * np.sin(2.0 * kx))
        + 5.0 * np.cos(ky)
        + 1j * np.sin(ky)
    ) / 2.0


def _chain_hamiltonian(
    length: int,
    hoppings: dict[int, complex],
) -> sparse.csr_matrix:
    if length < 2:
        raise ValueError("length must be at least two")
    diagonals: list[np.ndarray] = []
    offsets: list[int] = []
    for displacement, amplitude in hoppings.items():
        if abs(displacement) >= length:
            continue
        diagonals.append(
            np.full(length - abs(displacement), amplitude, dtype=np.complex128)
        )
        offsets.append(displacement)
    return sparse.diags(
        diagonals,
        offsets,
        shape=(length, length),
        format="csr",
        dtype=np.complex128,
    )


def separable_square_spectrum(length: int = 75) -> SeparableSpectrum:
    """Return the exact finite-square OBC spectrum used in Fig. S2(a)."""

    x_matrix = _chain_hamiltonian(
        length,
        {1: 1.0, -1: 1.5, 2: 0.5, -2: 2.0},
    )
    y_matrix = _chain_hamiltonian(length, {1: 1.5, -1: 1.0})
    x_values = linalg.eigvals(x_matrix.toarray(), check_finite=False)
    y_values = linalg.eigvals(y_matrix.toarray(), check_finite=False)
    values = (x_values[:, None] + y_values[None, :]).reshape(-1)
    return SeparableSpectrum(
        eigenvalues=np.asarray(values, dtype=np.complex128),
        x_eigenvalues=np.asarray(x_values, dtype=np.complex128),
        y_eigenvalues=np.asarray(y_values, dtype=np.complex128),
    )


def x_root_potential(
    energy: complex | np.ndarray,
    *,
    batch_size: int = 65_536,
) -> np.ndarray:
    """Evaluate Eq. (S20) from the two largest-modulus quartic roots."""

    values = np.asarray(energy, dtype=np.complex128)
    flat = values.reshape(-1)
    result = np.empty(flat.size, dtype=np.float64)
    tiny = np.finfo(np.float64).tiny
    for start in range(0, flat.size, batch_size):
        stop = min(start + batch_size, flat.size)
        selected = flat[start:stop]
        coefficients = np.column_stack(
            (
                np.ones(selected.size, dtype=np.complex128),
                np.full(selected.size, 2.0, dtype=np.complex128),
                -2.0 * selected,
                np.full(selected.size, 3.0, dtype=np.complex128),
                np.full(selected.size, 4.0, dtype=np.complex128),
            )
        )
        roots = batched_polynomial_roots(coefficients)
        moduli = np.sort(np.abs(roots), axis=1)
        result[start:stop] = np.log(0.5) + np.sum(
            np.log(np.maximum(moduli[:, 2:], tiny)), axis=1
        )
    return result.reshape(values.shape)


def exact_tdl_potential(
    energy: complex | np.ndarray,
    *,
    quadrature_samples: int = 128,
    energy_batch_size: int = 256,
) -> np.ndarray:
    """Evaluate Eqs. (S19)-(S21) by the arcsine/angle substitution."""

    if quadrature_samples < 16:
        raise ValueError("quadrature_samples must be at least 16")
    values = np.asarray(energy, dtype=np.complex128)
    flat = values.reshape(-1)
    result = np.empty(flat.size, dtype=np.float64)
    theta = (np.arange(quadrature_samples, dtype=np.float64) + 0.5) * (
        np.pi / quadrature_samples
    )
    y_energy = np.sqrt(6.0) * np.cos(theta)
    for start in range(0, flat.size, energy_batch_size):
        stop = min(start + energy_batch_size, flat.size)
        shifted = flat[start:stop, None] - y_energy[None, :]
        result[start:stop] = np.mean(x_root_potential(shifted), axis=1)
    return result.reshape(values.shape)


def _y_root_log_moduli(
    energy: np.ndarray,
    deformation_x: np.ndarray,
    momentum_x: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    beta_x = np.exp(deformation_x[:, None] + 1j * momentum_x[None, :])
    shifted = energy[:, None] - hx(beta_x)
    discriminant = np.sqrt(shifted**2 - 6.0)
    first = (shifted + discriminant) / 3.0
    second = (shifted - discriminant) / 3.0
    tiny = np.finfo(np.float64).tiny
    return (
        np.log(np.maximum(np.abs(first), tiny)),
        np.log(np.maximum(np.abs(second), tiny)),
    )


def _minimum_over_y(
    energy: np.ndarray,
    deformation_x: np.ndarray,
    momentum_x: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    first, second = _y_root_log_moduli(energy, deformation_x, momentum_x)
    deformation_y = np.median(np.concatenate((first, second), axis=1), axis=1)
    first_term = np.maximum(deformation_y[:, None], first)
    second_term = np.maximum(deformation_y[:, None], second)
    potential = (
        np.log(1.5)
        - deformation_y
        + np.mean(first_term + second_term, axis=1)
    )
    return np.asarray(potential), np.asarray(deformation_y)


def jensen_ronkin_potential(
    energy: complex,
    *,
    deformation_x: float,
    deformation_y: float,
    momentum_samples: int = 256,
) -> float:
    """Evaluate Eq. (S15) using Jensen's formula for the y integral."""

    if momentum_samples < 16:
        raise ValueError("momentum_samples must be at least 16")
    momentum = (np.arange(momentum_samples, dtype=np.float64) + 0.5) * (
        2.0 * np.pi / momentum_samples
    )
    first, second = _y_root_log_moduli(
        np.asarray([energy], dtype=np.complex128),
        np.asarray([deformation_x], dtype=np.float64),
        momentum,
    )
    value = (
        np.log(1.5)
        - deformation_y
        + np.mean(
            np.maximum(deformation_y, first)
            + np.maximum(deformation_y, second)
        )
    )
    return float(value)


def amoeba_potential_grid(
    energy: complex | np.ndarray,
    *,
    momentum_samples: int = 128,
    deformation_bounds: tuple[float, float] = (-2.5, 2.5),
    coarse_samples: int = 41,
    refinement_steps: int = 18,
    energy_batch_size: int = 256,
) -> AmoebaPotentialGrid:
    """Minimize Eq. (S15) with an exact inner-y minimum and batched x search."""

    if momentum_samples < 16:
        raise ValueError("momentum_samples must be at least 16")
    if coarse_samples < 5:
        raise ValueError("coarse_samples must be at least five")
    if refinement_steps < 1:
        raise ValueError("refinement_steps must be positive")
    lower, upper = deformation_bounds
    if lower >= upper:
        raise ValueError("deformation_bounds must be increasing")

    values = np.asarray(energy, dtype=np.complex128)
    flat = values.reshape(-1)
    potentials = np.empty(flat.size, dtype=np.float64)
    optimum_x = np.empty(flat.size, dtype=np.float64)
    optimum_y = np.empty(flat.size, dtype=np.float64)
    boundary_hits = 0
    momentum = (np.arange(momentum_samples, dtype=np.float64) + 0.5) * (
        2.0 * np.pi / momentum_samples
    )
    coarse = np.linspace(lower, upper, coarse_samples)
    golden = (np.sqrt(5.0) - 1.0) / 2.0

    for start in range(0, flat.size, energy_batch_size):
        stop = min(start + energy_batch_size, flat.size)
        selected = flat[start:stop]
        coarse_values = np.empty((selected.size, coarse_samples), dtype=np.float64)
        for index, deformation in enumerate(coarse):
            coarse_values[:, index], _ = _minimum_over_y(
                selected,
                np.full(selected.size, deformation),
                momentum,
            )
        best = np.argmin(coarse_values, axis=1)
        boundary_hits += int(np.count_nonzero((best == 0) | (best == coarse_samples - 1)))
        left_index = np.maximum(best - 1, 0)
        right_index = np.minimum(best + 1, coarse_samples - 1)
        left = coarse[left_index]
        right = coarse[right_index]

        for _ in range(refinement_steps):
            first_x = right - golden * (right - left)
            second_x = left + golden * (right - left)
            first_value, _ = _minimum_over_y(selected, first_x, momentum)
            second_value, _ = _minimum_over_y(selected, second_x, momentum)
            choose_first = first_value <= second_value
            right = np.where(choose_first, second_x, right)
            left = np.where(choose_first, left, first_x)

        final_x = 0.5 * (left + right)
        final_value, final_y = _minimum_over_y(selected, final_x, momentum)
        potentials[start:stop] = final_value
        optimum_x[start:stop] = final_x
        optimum_y[start:stop] = final_y

    shape = values.shape
    return AmoebaPotentialGrid(
        potential=potentials.reshape(shape),
        deformation_x=optimum_x.reshape(shape),
        deformation_y=optimum_y.reshape(shape),
        boundary_hits=boundary_hits,
        objective_evaluations_per_energy=coarse_samples + 2 * refinement_steps + 1,
    )


def amoeba_zero_locus(
    energy: complex,
    deformation_x: np.ndarray,
    *,
    momentum_samples: int = 512,
) -> tuple[np.ndarray, np.ndarray]:
    """Parameterize the characteristic-polynomial amoeba without image data."""

    x_values = np.asarray(deformation_x, dtype=np.float64).reshape(-1)
    if x_values.size < 2:
        raise ValueError("deformation_x must contain at least two values")
    if momentum_samples < 16:
        raise ValueError("momentum_samples must be at least 16")
    momentum = (np.arange(momentum_samples, dtype=np.float64) + 0.5) * (
        2.0 * np.pi / momentum_samples
    )
    energy_values = np.full(x_values.size, complex(energy), dtype=np.complex128)
    first, second = _y_root_log_moduli(energy_values, x_values, momentum)
    x_grid = np.broadcast_to(x_values[:, None], first.shape)
    return (
        np.concatenate((x_grid.reshape(-1), x_grid.reshape(-1))),
        np.concatenate((first.reshape(-1), second.reshape(-1))),
    )


def torus_winding_order(
    energy: complex,
    *,
    deformation_x: float,
    deformation_y: float,
    momentum_samples: int = 4096,
) -> AmoebaOrder:
    """Return the integer amoeba order at a point outside its zero locus."""

    if momentum_samples < 64:
        raise ValueError("momentum_samples must be at least 64")
    momentum = (np.arange(momentum_samples, dtype=np.float64) + 0.5) * (
        2.0 * np.pi / momentum_samples
    )
    fixed_x = np.exp(deformation_x)
    fixed_y = np.exp(deformation_y)
    x_loop = hx(np.exp(deformation_x + 1j * momentum)) + hy(fixed_y) - energy
    y_loop = hx(fixed_x) + hy(np.exp(deformation_y + 1j * momentum)) - energy

    def winding(values: np.ndarray) -> int:
        steps = np.angle(np.roll(values, -1) / values)
        return int(np.rint(np.sum(steps) / (2.0 * np.pi)))

    minimum = min(float(np.min(np.abs(x_loop))), float(np.min(np.abs(y_loop))))
    return AmoebaOrder(
        winding_x=winding(x_loop),
        winding_y=winding(y_loop),
        minimum_sampled_modulus=minimum,
    )


def classify_amoeba_holes(
    energy: complex,
    *,
    deformation_x_bounds: tuple[float, float] = (-1.5, 2.0),
    deformation_y_bounds: tuple[float, float] = (-4.0, 3.0),
    raster_samples: int = 281,
    momentum_samples: int = 768,
    zero_locus_tolerance: float = 0.045,
    minimum_hole_cells: int = 5,
) -> AmoebaRaster:
    """Rasterize the polynomial zero locus and classify all bounded holes.

    The raster is a numerical representation of the characteristic-polynomial
    amoeba, not a segmentation of the published panel.  Connected complement
    components touching the raster boundary are unbounded and excluded.  Each
    bounded component is classified by its integer torus winding order.
    """

    if raster_samples < 32:
        raise ValueError("raster_samples must be at least 32")
    if zero_locus_tolerance <= 0.0:
        raise ValueError("zero_locus_tolerance must be positive")
    if minimum_hole_cells < 1:
        raise ValueError("minimum_hole_cells must be positive")
    x_values = np.linspace(*deformation_x_bounds, raster_samples)
    y_values = np.linspace(*deformation_y_bounds, raster_samples)
    locus_x, locus_y = amoeba_zero_locus(
        energy,
        x_values,
        momentum_samples=momentum_samples,
    )
    tree = cKDTree(np.column_stack((locus_x, locus_y)))
    grid_x, grid_y = np.meshgrid(x_values, y_values)
    probes = np.column_stack((grid_x.reshape(-1), grid_y.reshape(-1)))
    distance = tree.query(probes, workers=-1)[0].reshape(grid_x.shape)
    zero_locus_mask = distance <= zero_locus_tolerance
    components, component_count = label(
        ~zero_locus_mask,
        structure=np.ones((3, 3), dtype=np.int8),
    )
    boundary_labels = set(
        np.unique(
            np.concatenate(
                (
                    components[0, :],
                    components[-1, :],
                    components[:, 0],
                    components[:, -1],
                )
            )
        ).tolist()
    )
    holes: list[AmoebaHole] = []
    for component in range(1, component_count + 1):
        if component in boundary_labels:
            continue
        coordinates = np.argwhere(components == component)
        if coordinates.shape[0] < minimum_hole_cells:
            continue
        component_distance = distance[components == component]
        center_y_index, center_x_index = coordinates[
            int(np.argmax(component_distance))
        ]
        center_x = float(x_values[center_x_index])
        center_y = float(y_values[center_y_index])
        holes.append(
            AmoebaHole(
                center_x=center_x,
                center_y=center_y,
                cell_count=int(coordinates.shape[0]),
                clearance=float(distance[center_y_index, center_x_index]),
                order=torus_winding_order(
                    energy,
                    deformation_x=center_x,
                    deformation_y=center_y,
                ),
            )
        )
    holes.sort(key=lambda item: (-item.cell_count, item.center_x, item.center_y))
    return AmoebaRaster(
        deformation_x=x_values,
        deformation_y=y_values,
        distance_to_zero_locus=distance,
        zero_locus_mask=zero_locus_mask,
        holes=tuple(holes),
    )


def model_s17_hopping_map() -> HoppingModel:
    """Typed alias used by generic lattice and Ronkin infrastructure."""

    return model_s17()
