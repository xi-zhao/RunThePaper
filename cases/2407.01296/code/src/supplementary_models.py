"""Independent numerical models for Supplementary Figs. S4-S7.

The functions in this module are derived from Supplementary Eqs. (S24),
(S26)-(S29). They never consume source-figure pixels or digitized curves; the
only inputs are paper parameters and numerical resolution.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

import numpy as np
from scipy import linalg, sparse
from scipy.optimize import minimize_scalar, root
from scipy.sparse.linalg import eigs

from src.geometry_adaptive import HoppingModel, Site, TargetEigenstate


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


@dataclass(frozen=True)
class SpatialProfileMetrics:
    """Coordinate-space diagnostics for one normalized right eigenstate."""

    center_x: float
    center_y: float
    rms_width: float
    inverse_participation_ratio: float
    effective_site_count: float
    boundary_mass: float
    peak_x: int
    peak_y: int


@dataclass(frozen=True)
class DoubleChainTDLSpectrum:
    """Equation-defined OBC thermodynamic spectrum for Eq. (S24).

    For the quartic characteristic equation ordered as
    ``|beta_1| <= ... <= |beta_4|``, the one-dimensional non-Bloch continuum
    is the locus ``|beta_2| = |beta_3|``.  ``root_gaps`` stores the residual
    ``log|beta_3| - log|beta_2|`` for every returned energy.
    """

    energies: np.ndarray
    root_gaps: np.ndarray
    real_samples: int
    imaginary_samples: int
    root_gap_tolerance: float


def model_s27() -> dict[tuple[int, int], complex]:
    """Directed hoppings obtained by expanding Supplementary Eq. (S27)."""

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


def spatial_profile_metrics(
    sites: Sequence[Site], eigenvector: np.ndarray
) -> SpatialProfileMetrics:
    """Measure size, participation, and boundary enrichment of a lattice state.

    Boundary sites are detected from the four nearest-neighbour directions,
    which makes the definition work for both the square and rhombus cuts in
    Supplementary Fig. S5 without geometry-specific thresholds.
    """

    coordinates = np.asarray(sites, dtype=np.float64)
    vector = np.asarray(eigenvector, dtype=np.complex128).reshape(-1)
    if coordinates.ndim != 2 or coordinates.shape[1] != 2:
        raise ValueError("sites must contain two-dimensional integer coordinates")
    if coordinates.shape[0] != vector.size:
        raise ValueError("site and eigenvector lengths differ")
    probability = np.abs(vector) ** 2
    total = float(np.sum(probability))
    if total <= 0.0 or not np.isfinite(total):
        raise ValueError("eigenvector has no finite probability mass")
    probability = np.asarray(probability / total, dtype=np.float64)
    center = probability @ coordinates
    squared_distance = np.sum((coordinates - center) ** 2, axis=1)
    rms_width = float(np.sqrt(probability @ squared_distance))
    inverse_participation_ratio = float(np.sum(probability**2))

    site_set = set(sites)
    nearest_neighbours = ((1, 0), (-1, 0), (0, 1), (0, -1))
    boundary = np.asarray(
        [
            any((x + dx, y + dy) not in site_set for dx, dy in nearest_neighbours)
            for x, y in sites
        ],
        dtype=bool,
    )
    peak = int(np.argmax(probability))
    return SpatialProfileMetrics(
        center_x=float(center[0]),
        center_y=float(center[1]),
        rms_width=rms_width,
        inverse_participation_ratio=inverse_participation_ratio,
        effective_site_count=1.0 / inverse_participation_ratio,
        boundary_mass=float(np.sum(probability[boundary])),
        peak_x=int(sites[peak][0]),
        peak_y=int(sites[peak][1]),
    )


def select_target_spatial_eigenstate(
    sites: Sequence[Site],
    hamiltonian: sparse.spmatrix | np.ndarray,
    target_energy: complex,
    *,
    selection: str = "nearest",
    candidate_count: int = 16,
    tolerance: float = 1e-10,
    maximum_iterations: int = 10_000,
) -> TargetEigenstate:
    """Select a declared local spectral state with a deterministic rule.

    ``nearest`` chooses the eigenvalue nearest the declared target.
    ``narrowest`` and ``widest`` choose the smallest or largest coordinate-space
    RMS width among the same local shift-invert candidate set. They
    operationalize the normal A and scale-free B branches in Supplementary
    Fig. S5 without inspecting source-figure pixels.
    """

    if selection not in {"nearest", "narrowest", "widest"}:
        raise ValueError("selection must be 'nearest', 'narrowest', or 'widest'")
    matrix = sparse.csr_matrix(hamiltonian, dtype=np.complex128)
    size = matrix.shape[0]
    if matrix.shape[1] != size or size != len(sites):
        raise ValueError("hamiltonian shape must match the declared sites")
    if not 1 <= candidate_count < size - 1:
        raise ValueError("candidate_count must be between 1 and matrix size - 2")

    phase = np.arange(size, dtype=np.float64)
    initial = np.exp(1j * (np.sqrt(2.0) * phase + 0.13 * phase**2 / max(size, 1)))
    initial /= np.linalg.norm(initial)
    eigenvalues, vectors = eigs(
        matrix,
        k=candidate_count,
        sigma=complex(target_energy),
        which="LM",
        v0=initial,
        tol=tolerance,
        maxiter=maximum_iterations,
        ncv=min(size, max(2 * candidate_count + 1, 40)),
    )
    if selection == "nearest":
        selected = int(np.argmin(np.abs(eigenvalues - target_energy)))
    else:
        widths = [
            spatial_profile_metrics(sites, vectors[:, index]).rms_width
            for index in range(candidate_count)
        ]
        selected = int(np.argmin(widths) if selection == "narrowest" else np.argmax(widths))
    vector = np.asarray(vectors[:, selected], dtype=np.complex128)
    vector /= np.linalg.norm(vector)
    eigenvalue = complex(eigenvalues[selected])
    residual = float(np.linalg.norm(matrix @ vector - eigenvalue * vector))
    return TargetEigenstate(
        target_energy=complex(target_energy),
        eigenvalue=eigenvalue,
        right_eigenvector=vector,
        normalized_residual=residual,
        candidate_count=candidate_count,
    )


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


def double_chain_characteristic_coefficients(
    energy: complex,
    *,
    t1_left: float = 0.5,
    t1_right: float = 1.0,
    t2_left: float = 1.0,
    t2_right: float = 0.5,
    potential: float = 0.5,
    coupling: float = 0.01,
) -> np.ndarray:
    """Return coefficients of ``beta^2 det[H(beta)-E]`` for Eq. (S24).

    The returned array is ordered from ``beta^4`` to ``beta^0``.  Expanding
    the two diagonal Laurent polynomials before subtracting ``coupling**2``
    keeps the derivation explicit and avoids using any finite-size spectrum.
    """

    value = complex(energy)
    first_zero = potential - value
    second_zero = -potential - value
    return np.asarray(
        (
            t1_right * t2_right,
            first_zero * t2_right + t1_right * second_zero,
            t1_left * t2_right
            + first_zero * second_zero
            + t1_right * t2_left
            - coupling**2,
            t1_left * second_zero + first_zero * t2_left,
            t1_left * t2_left,
        ),
        dtype=np.complex128,
    )


def double_chain_characteristic_roots(
    energy: complex,
    **parameters: float,
) -> np.ndarray:
    """Solve the four generalized-Bloch roots at one complex energy."""

    coefficients = double_chain_characteristic_coefficients(energy, **parameters)
    roots = np.roots(coefficients)
    return roots[np.argsort(np.abs(roots))]


def double_chain_middle_root_gap(
    energy: complex,
    **parameters: float,
) -> float:
    """Return the non-negative residual of ``|beta_2|=|beta_3|``."""

    roots = double_chain_characteristic_roots(energy, **parameters)
    moduli = np.abs(roots)
    if np.any(moduli <= 0.0) or not np.all(np.isfinite(moduli)):
        return float("inf")
    return float(np.log(moduli[2]) - np.log(moduli[1]))


def double_chain_tdl_spectrum(
    *,
    real_window: tuple[float, float] = (-2.05, 2.05),
    imaginary_window: tuple[float, float] = (0.0, 0.55),
    real_samples: int = 801,
    imaginary_samples: int = 161,
    root_gap_tolerance: float = 1e-7,
    coarse_gap_tolerance: float = 0.025,
    **parameters: float,
) -> DoubleChainTDLSpectrum:
    """Numerically trace the exact middle-root condition of Eq. (S24).

    Each fixed-Re(E) slice is searched for every local minimum of the
    non-negative middle-root gap.  Candidate minima are refined directly on
    the quartic-root equation and accepted only when the declared equality
    tolerance is met.  Complex-conjugate partners are generated from the real
    coefficients, not inferred from a source figure or a large finite chain.
    """

    if real_samples < 21 or imaginary_samples < 21:
        raise ValueError("TDL tracing requires at least 21 samples per axis")
    if real_window[0] >= real_window[1]:
        raise ValueError("real_window must be increasing")
    if imaginary_window[0] != 0.0 or imaginary_window[1] <= 0.0:
        raise ValueError("imaginary_window must start at zero and end positive")
    if root_gap_tolerance <= 0.0 or coarse_gap_tolerance <= root_gap_tolerance:
        raise ValueError("gap tolerances must satisfy 0 < root < coarse")

    real_axis = np.linspace(*real_window, real_samples)
    imaginary_axis = np.linspace(*imaginary_window, imaginary_samples)
    energies: list[complex] = []
    gaps: list[float] = []

    def gap_at(real_energy: float, imaginary_energy: float) -> float:
        return double_chain_middle_root_gap(
            complex(real_energy, imaginary_energy), **parameters
        )

    for real_energy in real_axis:
        coarse = np.asarray(
            [gap_at(float(real_energy), float(value)) for value in imaginary_axis],
            dtype=np.float64,
        )
        candidate_indices: list[int] = []
        if coarse[0] <= coarse[1]:
            candidate_indices.append(0)
        candidate_indices.extend(
            index
            for index in range(1, imaginary_axis.size - 1)
            if coarse[index] <= coarse[index - 1]
            and coarse[index] <= coarse[index + 1]
        )

        for index in candidate_indices:
            if coarse[index] > coarse_gap_tolerance:
                continue
            if index == 0:
                imaginary_energy = 0.0
                refined_gap = float(coarse[0])
            else:
                result = minimize_scalar(
                    lambda value: gap_at(float(real_energy), float(value)),
                    bounds=(
                        float(imaginary_axis[index - 1]),
                        float(imaginary_axis[index + 1]),
                    ),
                    method="bounded",
                    options={"xatol": 1e-13, "maxiter": 160},
                )
                imaginary_energy = float(result.x)
                refined_gap = float(result.fun)
            if refined_gap > root_gap_tolerance:
                continue
            energies.append(complex(float(real_energy), imaginary_energy))
            gaps.append(refined_gap)
            if imaginary_energy > 10.0 * np.finfo(float).eps:
                energies.append(complex(float(real_energy), -imaginary_energy))
                gaps.append(refined_gap)

    if not energies:
        raise RuntimeError("no points satisfied the Eq. (S24) middle-root condition")
    order = np.lexsort(
        (
            np.asarray([value.imag for value in energies]),
            np.asarray([value.real for value in energies]),
        )
    )
    return DoubleChainTDLSpectrum(
        energies=np.asarray(energies, dtype=np.complex128)[order],
        root_gaps=np.asarray(gaps, dtype=np.float64)[order],
        real_samples=real_samples,
        imaginary_samples=imaginary_samples,
        root_gap_tolerance=root_gap_tolerance,
    )


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
