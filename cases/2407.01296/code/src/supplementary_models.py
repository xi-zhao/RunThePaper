"""Independent numerical models for Supplementary Figs. S4 and S6.

The functions in this module are derived from Supplementary Eqs. (S24),
(S26), and (S28).  They never consume source-figure pixels or digitized
curves; the only inputs are paper parameters and numerical resolution.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

import numpy as np
from scipy import linalg, sparse
from scipy.optimize import root

from src.geometry_adaptive import HoppingModel


@dataclass(frozen=True)
class ExponentialDecayFit:
    """Fit ``p(x) = A exp(-2 kappa x)`` along one boundary tail."""

    amplitude: float
    kappa: float
    r_squared: float
    point_count: int
    peak_site: int


@dataclass(frozen=True)
class FermiPoint:
    """Isolated zero of a scalar complex Bloch Hamiltonian."""

    momentum_1: float
    momentum_2: float
    charge: int
    residual: float
    jacobian_determinant: float


@dataclass(frozen=True)
class BiorthogonalDiagonalResponse:
    """First-order response weights for arbitrary real onsite disorder.

    For right/left eigenvectors ``|R_i>`` and ``<L_i|``, row ``i`` of
    ``weights`` contains ``<L_i|n_j|R_i>/<L_i|R_i>`` for every site ``j``.
    Multiplying this row by a diagonal disorder realization evaluates the
    first-order energy shift used operationally for Supplementary Eq. (S29).
    """

    eigenvalues: np.ndarray
    weights: np.ndarray
    maximum_uniform_shift_error: float
    minimum_left_right_overlap: float
    maximum_sampled_eigenpair_residual: float


def double_chain_hamiltonian(
    length: int,
    *,
    t1_left: float = 0.5,
    t1_right: float = 1.0,
    t2_left: float = 1.0,
    t2_right: float = 0.5,
    potential: float = 0.5,
    coupling: float = 0.01,
) -> sparse.csr_matrix:
    """Build the open-boundary double-chain Hamiltonian in Eq. (S24).

    Sites are interleaved as ``(cell 0, chain 1)``, ``(cell 0, chain 2)``,
    and so on.  The convention ``H[row=n, col=n+d]=t_d`` gives the Laurent
    term ``t_d beta**d`` under a plane-wave substitution.
    """

    if length < 2:
        raise ValueError("length must be at least two")
    rows: list[int] = []
    columns: list[int] = []
    values: list[complex] = []

    def add(row: int, column: int, value: complex) -> None:
        if value != 0:
            rows.append(row)
            columns.append(column)
            values.append(complex(value))

    for cell in range(length):
        first = 2 * cell
        second = first + 1
        add(first, first, potential)
        add(second, second, -potential)
        add(first, second, coupling)
        add(second, first, coupling)
        if cell + 1 < length:
            next_first = first + 2
            next_second = second + 2
            add(first, next_first, t1_right)
            add(next_first, first, t1_left)
            add(second, next_second, t2_right)
            add(next_second, second, t2_left)

    size = 2 * length
    return sparse.csr_matrix(
        (values, (rows, columns)), shape=(size, size), dtype=np.complex128
    )


def double_chain_bloch_spectrum(
    momentum: np.ndarray,
    *,
    t1_left: float = 0.5,
    t1_right: float = 1.0,
    t2_left: float = 1.0,
    t2_right: float = 0.5,
    potential: float = 0.5,
    coupling: float = 0.01,
) -> np.ndarray:
    """Return the two periodic-boundary bands of Eq. (S24)."""

    k = np.asarray(momentum, dtype=np.float64).reshape(-1)
    beta = np.exp(1j * k)
    first = t1_left / beta + t1_right * beta + potential
    second = t2_left / beta + t2_right * beta - potential
    center = 0.5 * (first + second)
    splitting = np.sqrt((0.5 * (first - second)) ** 2 + coupling**2)
    return np.column_stack((center + splitting, center - splitting))


def site_probability(eigenvector: np.ndarray) -> np.ndarray:
    """Sum the two chain components into a normalized cell probability."""

    vector = np.asarray(eigenvector, dtype=np.complex128).reshape(-1)
    if vector.size < 4 or vector.size % 2:
        raise ValueError("eigenvector must contain two components per cell")
    probability = np.abs(vector[0::2]) ** 2 + np.abs(vector[1::2]) ** 2
    total = float(np.sum(probability))
    if total <= 0.0 or not np.isfinite(total):
        raise ValueError("eigenvector has no finite probability mass")
    return np.asarray(probability / total, dtype=np.float64)


def fit_boundary_exponential(
    probability: np.ndarray,
    *,
    relative_floor: float = 1e-8,
) -> ExponentialDecayFit:
    """Fit the left-boundary decay up to the chain midpoint.

    The fit starts at the largest probability in the left half.  This covers
    both a normal edge state whose maximum sits a few sites inside the chain
    and the scale-free state whose maximum is at the boundary.
    """

    values = np.asarray(probability, dtype=np.float64).reshape(-1)
    if values.size < 10 or np.any(values < 0.0) or values.max() <= 0.0:
        raise ValueError("probability must contain at least ten non-negative values")
    if not 0.0 < relative_floor < 1.0:
        raise ValueError("relative_floor must lie between zero and one")
    midpoint = max(5, values.size // 2)
    peak_site = int(np.argmax(values[:midpoint]))
    coordinate = np.arange(peak_site, midpoint, dtype=np.float64) - peak_site
    tail = values[peak_site:midpoint]
    mask = tail >= float(tail.max()) * relative_floor
    if np.count_nonzero(mask) < 5:
        raise ValueError("too few points remain above the fit floor")
    design = np.column_stack(
        (np.ones(np.count_nonzero(mask)), coordinate[mask])
    )
    response = np.log(tail[mask])
    coefficients, *_ = np.linalg.lstsq(design, response, rcond=None)
    prediction = design @ coefficients
    residual_sum = float(np.sum((response - prediction) ** 2))
    total_sum = float(np.sum((response - np.mean(response)) ** 2))
    r_squared = 1.0 - residual_sum / total_sum if total_sum > 0.0 else 1.0
    slope = float(coefficients[1])
    if slope >= 0.0:
        raise ValueError("selected profile does not decay away from the boundary")
    return ExponentialDecayFit(
        amplitude=float(np.exp(coefficients[0])),
        kappa=-0.5 * slope,
        r_squared=r_squared,
        point_count=int(np.count_nonzero(mask)),
        peak_site=peak_site,
    )


def laurent_bloch_value(
    momentum_1: float | np.ndarray,
    momentum_2: float | np.ndarray,
    hoppings: Mapping[tuple[int, int], complex],
) -> np.ndarray:
    """Evaluate a scalar two-dimensional Laurent Hamiltonian on the BZ."""

    first = np.asarray(momentum_1, dtype=np.float64)
    second = np.asarray(momentum_2, dtype=np.float64)
    value = np.zeros(np.broadcast_shapes(first.shape, second.shape), dtype=np.complex128)
    for (power_1, power_2), amplitude in hoppings.items():
        value = value + complex(amplitude) * np.exp(
            1j * (power_1 * first + power_2 * second)
        )
    return value


def winding_number(
    hoppings: HoppingModel,
    *,
    integration_axis: int,
    fixed_momentum: float,
    reference_energy: complex = 0.0j,
    momentum_samples: int = 2048,
) -> int:
    """Evaluate Eq. (S28) as a closed-loop phase winding."""

    if integration_axis not in (0, 1):
        raise ValueError("integration_axis must be zero or one")
    if momentum_samples < 64:
        raise ValueError("momentum_samples must be at least 64")
    integration = (np.arange(momentum_samples, dtype=np.float64) + 0.5) * (
        2.0 * np.pi / momentum_samples
    ) - np.pi
    if integration_axis == 0:
        values = laurent_bloch_value(integration, fixed_momentum, hoppings)
    else:
        values = laurent_bloch_value(fixed_momentum, integration, hoppings)
    values = np.asarray(values - complex(reference_energy), dtype=np.complex128)
    if float(np.min(np.abs(values))) < 1e-10:
        raise ValueError("integration loop crosses the reference energy")
    phase_steps = np.angle(np.roll(values, -1) / values)
    return int(np.rint(float(np.sum(phase_steps) / (2.0 * np.pi))))


def winding_sweep(
    hoppings: HoppingModel,
    fixed_momenta: np.ndarray,
    *,
    integration_axis: int,
    reference_energy: complex = 0.0j,
    momentum_samples: int = 2048,
) -> np.ndarray:
    """Return the integer winding for every transverse-momentum slice."""

    return np.asarray(
        [
            winding_number(
                hoppings,
                integration_axis=integration_axis,
                fixed_momentum=float(momentum),
                reference_energy=reference_energy,
                momentum_samples=momentum_samples,
            )
            for momentum in np.asarray(fixed_momenta, dtype=np.float64).reshape(-1)
        ],
        dtype=np.int64,
    )


def find_fermi_points(
    hoppings: HoppingModel,
    *,
    reference_energy: complex = 0.0j,
    seed_count: int = 20,
    residual_tolerance: float = 1e-9,
    duplicate_tolerance: float = 1e-6,
) -> tuple[FermiPoint, ...]:
    """Find isolated BZ zeros and their Jacobian topological charges."""

    if seed_count < 4:
        raise ValueError("seed_count must be at least four")

    def residual(momentum: np.ndarray) -> np.ndarray:
        value = complex(
            laurent_bloch_value(momentum[0], momentum[1], hoppings)
            - reference_energy
        )
        return np.asarray((value.real, value.imag), dtype=np.float64)

    roots: list[np.ndarray] = []
    seeds = np.linspace(-np.pi, np.pi, seed_count, endpoint=False)
    for first in seeds:
        for second in seeds:
            result = root(residual, np.asarray((first, second)), method="hybr")
            if not result.success or float(np.linalg.norm(result.fun)) > residual_tolerance:
                continue
            folded = _fold_momentum(np.asarray(result.x, dtype=np.float64))
            if any(
                _periodic_distance(folded, existing) <= duplicate_tolerance
                for existing in roots
            ):
                continue
            roots.append(folded)

    points = [_fermi_point(momentum, hoppings, reference_energy) for momentum in roots]
    return tuple(sorted(points, key=lambda item: (item.momentum_1, item.momentum_2)))


def biorthogonal_diagonal_response(
    hamiltonian: sparse.spmatrix | np.ndarray,
    *,
    residual_samples: int = 12,
) -> BiorthogonalDiagonalResponse:
    """Build the clean-system response kernel in Supplementary Eq. (S29).

    The paper's released implementation evaluates the mean absolute
    first-order energy shift, even though the printed equation does not show
    the absolute-value bars explicitly.  This routine implements that
    biorthogonal perturbation formula without loading any released curves or
    figure pixels.
    """

    dense = (
        hamiltonian.toarray()
        if sparse.issparse(hamiltonian)
        else np.asarray(hamiltonian, dtype=np.complex128).copy()
    )
    if dense.ndim != 2 or dense.shape[0] != dense.shape[1] or dense.shape[0] < 2:
        raise ValueError("hamiltonian must be a square matrix of size at least two")
    if residual_samples < 1:
        raise ValueError("residual_samples must be positive")

    eigenvalues, left, right = linalg.eig(
        dense,
        left=True,
        right=True,
        overwrite_a=False,
        check_finite=False,
    )
    overlaps = np.einsum("ji,ji->i", left.conj(), right)
    overlap_magnitudes = np.abs(overlaps)
    if np.any(overlap_magnitudes == 0.0) or not np.all(np.isfinite(overlaps)):
        raise RuntimeError("eigensolver returned a singular left-right pairing")

    weights = ((left.conj() * right) / overlaps[None, :]).T
    uniform_error = float(np.max(np.abs(np.sum(weights, axis=1) - 1.0)))

    dimension = dense.shape[0]
    sample_indices = np.unique(
        np.linspace(
            0,
            dimension - 1,
            min(residual_samples, dimension),
            dtype=np.int64,
        )
    )
    operator_norm = float(np.max(np.sum(np.abs(dense), axis=1)))
    maximum_residual = 0.0
    for index in sample_indices:
        eigenvalue = complex(eigenvalues[index])
        right_vector = right[:, index]
        left_vector = left[:, index]
        right_residual = np.linalg.norm(dense @ right_vector - eigenvalue * right_vector)
        left_residual = np.linalg.norm(
            dense.conj().T @ left_vector - eigenvalue.conjugate() * left_vector
        )
        right_scale = (operator_norm + abs(eigenvalue)) * np.linalg.norm(right_vector)
        left_scale = (operator_norm + abs(eigenvalue)) * np.linalg.norm(left_vector)
        maximum_residual = max(
            maximum_residual,
            float(right_residual / right_scale),
            float(left_residual / left_scale),
        )

    return BiorthogonalDiagonalResponse(
        eigenvalues=np.asarray(eigenvalues, dtype=np.complex128),
        weights=np.asarray(weights, dtype=np.complex128),
        maximum_uniform_shift_error=uniform_error,
        minimum_left_right_overlap=float(np.min(overlap_magnitudes)),
        maximum_sampled_eigenpair_residual=maximum_residual,
    )


def mean_absolute_first_order_shift(
    response: BiorthogonalDiagonalResponse,
    onsite_samples: np.ndarray,
) -> float:
    """Average the absolute Eq. (S29) shift over states and realizations."""

    samples = np.asarray(onsite_samples, dtype=np.float64)
    if samples.ndim != 2 or samples.shape[1] != response.weights.shape[1]:
        raise ValueError("onsite_samples must have shape (realizations, sites)")
    if samples.shape[0] < 1 or not np.all(np.isfinite(samples)):
        raise ValueError("onsite_samples must contain finite realizations")
    shifts = samples @ response.weights.T
    return float(np.mean(np.abs(shifts)))


def _fermi_point(
    momentum: np.ndarray,
    hoppings: HoppingModel,
    reference_energy: complex,
) -> FermiPoint:
    step = 1e-5
    derivatives: list[np.ndarray] = []
    for axis in range(2):
        displacement = np.zeros(2, dtype=np.float64)
        displacement[axis] = step
        difference = (
            laurent_bloch_value(
                *(momentum + displacement), hoppings
            )
            - laurent_bloch_value(*(momentum - displacement), hoppings)
        ) / (2.0 * step)
        derivatives.append(
            np.asarray((complex(difference).real, complex(difference).imag))
        )
    jacobian = np.column_stack(derivatives)
    determinant = float(np.linalg.det(jacobian))
    value = complex(
        laurent_bloch_value(momentum[0], momentum[1], hoppings)
        - reference_energy
    )
    return FermiPoint(
        momentum_1=float(momentum[0]),
        momentum_2=float(momentum[1]),
        charge=int(np.sign(determinant)),
        residual=float(abs(value)),
        jacobian_determinant=determinant,
    )


def _fold_momentum(momentum: np.ndarray) -> np.ndarray:
    return (momentum + np.pi) % (2.0 * np.pi) - np.pi


def _periodic_distance(first: np.ndarray, second: np.ndarray) -> float:
    return float(np.linalg.norm(np.angle(np.exp(1j * (first - second)))))
