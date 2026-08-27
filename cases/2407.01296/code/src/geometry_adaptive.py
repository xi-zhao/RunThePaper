"""Geometry-independent lattice models for the paper's OBC numerics.

The domain model has two inputs: a set of integer sites describing the cut
geometry, and a list of displacement/amplitude pairs describing the Bloch
Hamiltonian. Open boundaries are implemented by dropping hops whose endpoint
is outside the site set.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass

import numpy as np
from scipy import linalg, sparse
from scipy.optimize import minimize, minimize_scalar
from scipy.sparse.linalg import eigs, splu
from scipy.stats import t as student_t
from scipy.spatial import ConvexHull, cKDTree

Site = tuple[int, int]
HoppingModel = Mapping[Site, complex]


@dataclass(frozen=True)
class Eigensystem:
    eigenvalues: np.ndarray
    right_eigenvectors: np.ndarray


@dataclass(frozen=True)
class CylindricalMinimum:
    """Minimum of one deformed cylindrical potential."""

    potential: float
    deformation: float
    evaluations: int


@dataclass(frozen=True)
class GeometryPotential:
    """Two cylindrical branches and their geometry-adaptive minimum."""

    potential: float
    cylinder_1: CylindricalMinimum
    cylinder_2: CylindricalMinimum


@dataclass(frozen=True)
class TargetEigenstate:
    """A normalized right eigenstate selected near a declared complex energy."""

    target_energy: complex
    eigenvalue: complex
    right_eigenvector: np.ndarray
    normalized_residual: float
    candidate_count: int


@dataclass(frozen=True)
class GaussianProfileFit:
    """Fit ``probability = amplitude * exp(-kappa * (x-center)^2)``."""

    amplitude: float
    center: float
    kappa: float
    sigma: float
    r_squared: float
    point_count: int
    relative_floor: float

    def evaluate(self, coordinate: np.ndarray) -> np.ndarray:
        values = np.asarray(coordinate, dtype=np.float64)
        return self.amplitude * np.exp(-self.kappa * (values - self.center) ** 2)


@dataclass(frozen=True)
class LinearFit:
    """Ordinary least-squares line with a two-sided confidence interval."""

    slope: float
    intercept: float
    slope_standard_error: float
    intercept_standard_error: float
    intercept_confidence_interval: tuple[float, float]
    r_squared: float
    confidence: float
    point_count: int


@dataclass(frozen=True)
class AmoebaMinimum:
    """Minimum of the two-dimensional Ronkin potential."""

    potential: float
    deformation_x: float
    deformation_y: float
    evaluations: int


def square_sites(length_x: int, length_y: int | None = None) -> tuple[Site, ...]:
    """Return a deterministic rectangular integer lattice."""

    if length_x < 1:
        raise ValueError("length_x must be positive")
    length_y = length_x if length_y is None else length_y
    if length_y < 1:
        raise ValueError("length_y must be positive")
    return tuple((x, y) for y in range(length_y) for x in range(length_x))


def diamond_sites(radius: int) -> tuple[Site, ...]:
    """Return the equal-edge rhombus |x| + |y| <= radius."""

    if radius < 0:
        raise ValueError("radius must be non-negative")
    return tuple(
        (x, y)
        for y in range(-radius, radius + 1)
        for x in range(-radius, radius + 1)
        if abs(x) + abs(y) <= radius
    )


def cut_coordinate_sites(half_u: int, half_v: int) -> tuple[Site, ...]:
    """Return a rhombus bounded in u=x+y and v=-x+y cut coordinates."""

    if half_u < 0 or half_v < 0:
        raise ValueError("cut-coordinate half widths must be non-negative")
    return cut_coordinate_interval_sites((-half_u, half_u), (-half_v, half_v))


def cut_coordinate_interval_sites(
    u_bounds: tuple[int, int], v_bounds: tuple[int, int]
) -> tuple[Site, ...]:
    """Return a rhombus for possibly off-centered inclusive cut intervals."""

    u_min, u_max = u_bounds
    v_min, v_max = v_bounds
    if u_min > u_max or v_min > v_max:
        raise ValueError("cut-coordinate lower bounds must not exceed upper bounds")
    bound = max(abs(u_min), abs(u_max)) + max(abs(v_min), abs(v_max))
    return tuple(
        (x, y)
        for y in range(-bound, bound + 1)
        for x in range(-bound, bound + 1)
        if u_min <= x + y <= u_max and v_min <= -x + y <= v_max
    )


def model_eq11() -> dict[Site, complex]:
    """Directed hoppings from the formal paper's Eq. (11)."""

    return {
        (-1, 0): 2.0,
        (1, -1): 0.5,
        (0, 1): 1.5,
        (-1, 1): 0.9,
    }


def model_eq15() -> dict[Site, complex]:
    """Reciprocal critical-skin hoppings from the formal paper's Eq. (15)."""

    return {
        (-1, 0): 1.0,
        (1, 0): 1.0,
        (0, -1): 0.5j,
        (0, 1): 0.5j,
    }


def build_obc_hamiltonian(
    sites: Sequence[Site], hoppings: HoppingModel
) -> sparse.csr_matrix:
    """Build H[row=r, col=r+d]=t and discard endpoints outside the geometry."""

    unique_sites = tuple(dict.fromkeys(sites))
    if len(unique_sites) != len(sites):
        raise ValueError("sites must be unique")
    index = {site: position for position, site in enumerate(unique_sites)}
    rows: list[int] = []
    cols: list[int] = []
    data: list[complex] = []

    for row_site, row in index.items():
        x, y = row_site
        for (dx, dy), amplitude in hoppings.items():
            col = index.get((x + dx, y + dy))
            if col is not None and amplitude != 0:
                rows.append(row)
                cols.append(col)
                data.append(complex(amplitude))

    size = len(unique_sites)
    return sparse.csr_matrix((data, (rows, cols)), shape=(size, size), dtype=np.complex128)


def full_spectrum(hamiltonian: sparse.spmatrix | np.ndarray) -> np.ndarray:
    """Compute all complex eigenvalues with the local optimized LAPACK."""

    dense = _as_dense(hamiltonian)
    return linalg.eigvals(dense, overwrite_a=True, check_finite=False)


def full_right_eigensystem(hamiltonian: sparse.spmatrix | np.ndarray) -> Eigensystem:
    """Compute all eigenvalues and Euclidean-normalized right eigenvectors."""

    dense = _as_dense(hamiltonian)
    eigenvalues, vectors = linalg.eig(dense, overwrite_a=True, check_finite=False)
    norms = np.linalg.norm(vectors, axis=0)
    if np.any(norms == 0):
        raise RuntimeError("eigensolver returned a zero right eigenvector")
    vectors = vectors / norms
    return Eigensystem(eigenvalues=eigenvalues, right_eigenvectors=vectors)


def target_right_eigenstate(
    hamiltonian: sparse.spmatrix | np.ndarray,
    target_energy: complex,
    *,
    candidate_count: int = 8,
    tolerance: float = 1e-10,
    maximum_iterations: int = 10_000,
) -> TargetEigenstate:
    """Select the right eigenstate closest to ``target_energy`` by shift-invert.

    A deterministic complex starting vector avoids an implicit random state
    selection.  The returned residual is normalized by the eigenvector norm and
    is the numerical gate used by the Fig. 4(b) finite-size campaign.
    """

    matrix = sparse.csr_matrix(hamiltonian, dtype=np.complex128)
    size = matrix.shape[0]
    if matrix.shape[1] != size:
        raise ValueError("hamiltonian must be square")
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
        ncv=min(size, max(2 * candidate_count + 1, 32)),
    )
    selected = int(np.argmin(np.abs(eigenvalues - target_energy)))
    vector = np.asarray(vectors[:, selected], dtype=np.complex128)
    vector /= np.linalg.norm(vector)
    eigenvalue = complex(eigenvalues[selected])
    residual = np.linalg.norm(matrix @ vector - eigenvalue * vector) / np.linalg.norm(vector)
    return TargetEigenstate(
        target_energy=complex(target_energy),
        eigenvalue=eigenvalue,
        right_eigenvector=vector,
        normalized_residual=float(residual),
        candidate_count=candidate_count,
    )


def aggregate_right_density(right_eigenvectors: np.ndarray) -> np.ndarray:
    """Sum normalized right-eigenstate probabilities over all eigenstates."""

    if right_eigenvectors.ndim != 2:
        raise ValueError("right_eigenvectors must be a two-dimensional array")
    return np.sum(np.abs(right_eigenvectors) ** 2, axis=1).real


def eigensystem_residuals(
    hamiltonian: sparse.spmatrix | np.ndarray,
    eigensystem: Eigensystem,
    *,
    batch_size: int = 128,
) -> np.ndarray:
    """Return normalized right-eigenpair residuals without a giant temporary."""

    matrix = sparse.csr_matrix(hamiltonian, dtype=np.complex128)
    vectors = np.asarray(eigensystem.right_eigenvectors, dtype=np.complex128)
    eigenvalues = np.asarray(eigensystem.eigenvalues, dtype=np.complex128).reshape(-1)
    if matrix.shape[0] != matrix.shape[1] or vectors.shape != matrix.shape:
        raise ValueError("hamiltonian and right-eigenvector matrix shapes differ")
    if eigenvalues.size != matrix.shape[0]:
        raise ValueError("one eigenvalue is required per right eigenvector")
    if batch_size < 1:
        raise ValueError("batch_size must be positive")
    operator_norm = float(np.max(np.asarray(np.abs(matrix).sum(axis=1)).reshape(-1)))
    residuals = np.empty(eigenvalues.size, dtype=np.float64)
    for start in range(0, eigenvalues.size, batch_size):
        stop = min(start + batch_size, eigenvalues.size)
        selected = vectors[:, start:stop]
        difference = matrix @ selected - selected * eigenvalues[None, start:stop]
        numerator = np.linalg.norm(difference, axis=0)
        denominator = (operator_norm + np.abs(eigenvalues[start:stop])) * np.linalg.norm(
            selected, axis=0
        )
        residuals[start:stop] = numerator / np.maximum(
            denominator, np.finfo(np.float64).tiny
        )
    return residuals


def reflection_symmetrized_density(
    sites: Sequence[Site],
    density: np.ndarray,
) -> np.ndarray:
    """Average density over the exact x/y reflection symmetries of Eq. (15)."""

    values = np.asarray(density, dtype=np.float64).reshape(-1)
    if len(sites) != values.size:
        raise ValueError("site and density lengths differ")
    index = {site: position for position, site in enumerate(sites)}
    symmetrized = np.empty_like(values)
    for position, (x, y) in enumerate(sites):
        orbit = {(x, y), (-x, y), (x, -y), (-x, -y)}
        try:
            symmetrized[position] = np.mean([values[index[site]] for site in orbit])
        except KeyError as error:
            raise ValueError("site set is not closed under x/y reflections") from error
    return symmetrized


def rhombus_localization_metrics(
    sites: Sequence[Site],
    density: np.ndarray,
    *,
    boundary_strip_fraction: float = 0.10,
) -> dict[str, float | int]:
    """Quantify boundary enrichment and distinguish edges from corners."""

    values = np.asarray(density, dtype=np.float64).reshape(-1)
    if len(sites) != values.size:
        raise ValueError("site and density lengths differ")
    if np.any(values < 0.0) or values.sum() <= 0.0:
        raise ValueError("density must be non-negative with positive total weight")
    if not 0.0 < boundary_strip_fraction < 0.5:
        raise ValueError("boundary_strip_fraction must lie between zero and one half")
    coordinates = np.asarray(sites, dtype=np.int64)
    radial = np.abs(coordinates[:, 0]) + np.abs(coordinates[:, 1])
    radius = int(np.max(radial))
    strip_width = max(1, int(round(boundary_strip_fraction * radius)))
    boundary = radius - radial <= strip_width
    vertices = np.asarray(
        ((-radius, 0), (0, radius), (radius, 0), (0, -radius)), dtype=np.int64
    )
    corner_distance = np.min(
        np.sum(np.abs(coordinates[:, None, :] - vertices[None, :, :]), axis=2),
        axis=1,
    )
    corners = corner_distance <= strip_width
    normalized = values / values.sum()
    boundary_mass = float(normalized[boundary].sum())
    corner_mass = float(normalized[corners].sum())
    boundary_site_fraction = float(np.mean(boundary))
    corner_site_fraction = float(np.mean(corners))
    return {
        "radius": radius,
        "boundary_strip_width": strip_width,
        "boundary_mass_fraction": boundary_mass,
        "boundary_site_fraction": boundary_site_fraction,
        "boundary_enrichment": boundary_mass / boundary_site_fraction,
        "corner_mass_fraction": corner_mass,
        "corner_site_fraction": corner_site_fraction,
        "corner_fraction_of_boundary_mass": corner_mass / boundary_mass,
        "corner_fraction_of_boundary_sites": corner_site_fraction
        / boundary_site_fraction,
    }


def rhombus_edge_profile(
    sites: Sequence[Site],
    right_eigenvector: np.ndarray,
    *,
    edge: str = "v_positive",
) -> tuple[np.ndarray, np.ndarray, int]:
    """Return an ordered probability profile along one equal-rhombus edge.

    The cut coordinates are ``u=x+y`` and ``v=-x+y``.  A fixed-``v`` edge is
    parameterized by ``u`` and vice versa.  The returned integer is the boundary
    length ``L`` used in the paper's ``1/L`` scaling plot.
    """

    values = np.asarray(right_eigenvector, dtype=np.complex128).reshape(-1)
    if len(sites) != values.size:
        raise ValueError("site and eigenvector lengths differ")
    coordinates = np.asarray(sites, dtype=np.int64)
    u = coordinates[:, 0] + coordinates[:, 1]
    v = -coordinates[:, 0] + coordinates[:, 1]
    radius = int(max(np.max(np.abs(u)), np.max(np.abs(v))))
    definitions = {
        "v_positive": (v == radius, u),
        "v_negative": (v == -radius, u),
        "u_positive": (u == radius, v),
        "u_negative": (u == -radius, v),
    }
    if edge not in definitions:
        raise ValueError(f"unsupported rhombus edge: {edge}")
    mask, along = definitions[edge]
    selected_coordinate = np.asarray(along[mask], dtype=np.float64)
    probability = np.abs(values[mask]) ** 2
    order = np.argsort(selected_coordinate)
    return selected_coordinate[order], probability[order].real, radius


def fit_gaussian_profile(
    coordinate: np.ndarray,
    probability: np.ndarray,
    *,
    relative_floor: float = 1e-5,
) -> GaussianProfileFit:
    """Fit a Gaussian through a quadratic regression of log probability."""

    x = np.asarray(coordinate, dtype=np.float64).reshape(-1)
    values = np.asarray(probability, dtype=np.float64).reshape(-1)
    if x.size != values.size or x.size < 5:
        raise ValueError("coordinate and probability need at least five paired values")
    if not 0.0 < relative_floor < 1.0:
        raise ValueError("relative_floor must lie between zero and one")
    if np.any(values < 0.0) or not np.all(np.isfinite(values)) or values.max() <= 0.0:
        raise ValueError("probability must be finite, non-negative, and nonzero")
    normalized = values / values.max()
    mask = normalized >= relative_floor
    if np.count_nonzero(mask) < 5:
        raise ValueError("too few profile points remain above relative_floor")
    design = np.column_stack((np.ones(np.count_nonzero(mask)), x[mask], x[mask] ** 2))
    response = np.log(normalized[mask])
    coefficients, *_ = np.linalg.lstsq(design, response, rcond=None)
    quadratic = float(coefficients[2])
    if quadratic >= 0.0:
        raise ValueError("profile does not have a decaying Gaussian curvature")
    kappa = -quadratic
    center = float(coefficients[1] / (2.0 * kappa))
    log_amplitude = float(coefficients[0] + kappa * center**2)
    prediction = design @ coefficients
    residual_sum = float(np.sum((response - prediction) ** 2))
    total_sum = float(np.sum((response - np.mean(response)) ** 2))
    r_squared = 1.0 - residual_sum / total_sum if total_sum > 0.0 else 1.0
    return GaussianProfileFit(
        amplitude=float(np.exp(log_amplitude)),
        center=center,
        kappa=kappa,
        sigma=float(1.0 / np.sqrt(2.0 * kappa)),
        r_squared=float(r_squared),
        point_count=int(np.count_nonzero(mask)),
        relative_floor=float(relative_floor),
    )


def linear_fit_with_confidence(
    x: np.ndarray,
    y: np.ndarray,
    *,
    confidence: float = 0.95,
) -> LinearFit:
    """Fit ``y=slope*x+intercept`` and report the intercept interval."""

    independent = np.asarray(x, dtype=np.float64).reshape(-1)
    dependent = np.asarray(y, dtype=np.float64).reshape(-1)
    if independent.size != dependent.size or independent.size < 3:
        raise ValueError("linear fit needs at least three paired values")
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must lie between zero and one")
    design = np.column_stack((independent, np.ones(independent.size)))
    coefficients, *_ = np.linalg.lstsq(design, dependent, rcond=None)
    prediction = design @ coefficients
    residual = dependent - prediction
    degrees_of_freedom = independent.size - 2
    residual_variance = float(np.dot(residual, residual) / degrees_of_freedom)
    covariance = residual_variance * np.linalg.inv(design.T @ design)
    standard_errors = np.sqrt(np.diag(covariance))
    critical_value = float(student_t.ppf((1.0 + confidence) / 2.0, degrees_of_freedom))
    intercept = float(coefficients[1])
    intercept_error = float(standard_errors[1])
    total_sum = float(np.sum((dependent - np.mean(dependent)) ** 2))
    residual_sum = float(np.dot(residual, residual))
    r_squared = 1.0 - residual_sum / total_sum if total_sum > 0.0 else 1.0
    return LinearFit(
        slope=float(coefficients[0]),
        intercept=intercept,
        slope_standard_error=float(standard_errors[0]),
        intercept_standard_error=intercept_error,
        intercept_confidence_interval=(
            intercept - critical_value * intercept_error,
            intercept + critical_value * intercept_error,
        ),
        r_squared=float(r_squared),
        confidence=float(confidence),
        point_count=int(independent.size),
    )


def spectral_potential(eigenvalues: np.ndarray, probe_energy: complex) -> float:
    """Evaluate formal Eq. (2) with a machine-epsilon log regularizer."""

    values = np.asarray(eigenvalues, dtype=np.complex128)
    if values.size == 0:
        raise ValueError("eigenvalues must be non-empty")
    distances = np.maximum(np.abs(values - probe_energy), np.finfo(float).eps)
    return float(np.mean(np.log(distances)))


def spectral_potential_grid(
    eigenvalues: np.ndarray,
    probe_energies: np.ndarray,
    *,
    batch_size: int = 2048,
) -> np.ndarray:
    """Evaluate Eq. (2) on a grid without an unbounded difference array."""

    spectrum = np.asarray(eigenvalues, dtype=np.complex128).reshape(-1)
    probes = np.asarray(probe_energies, dtype=np.complex128)
    if spectrum.size == 0:
        raise ValueError("eigenvalues must be non-empty")
    flat_probes = probes.reshape(-1)
    result = np.empty(flat_probes.shape, dtype=np.float64)
    tiny = np.finfo(np.float64).tiny
    for start in range(0, flat_probes.size, batch_size):
        stop = min(start + batch_size, flat_probes.size)
        distances = np.abs(spectrum[:, None] - flat_probes[None, start:stop])
        result[start:stop] = np.mean(np.log(np.maximum(distances, tiny)), axis=0)
    return result.reshape(probes.shape)


def sparse_spectral_potential(
    hamiltonian: sparse.spmatrix | np.ndarray,
    probe_energy: complex,
) -> float:
    """Evaluate Eq. (2) as ``log|det(H-E)|/N`` using sparse LU."""

    matrix = sparse.csc_matrix(hamiltonian, dtype=np.complex128)
    size = matrix.shape[0]
    if matrix.shape[1] != size or size == 0:
        raise ValueError("hamiltonian must be a non-empty square matrix")
    shifted = matrix - complex(probe_energy) * sparse.identity(
        size, format="csc", dtype=np.complex128
    )
    factorization = splu(shifted, permc_spec="COLAMD")
    diagonal = np.abs(factorization.U.diagonal())
    if np.any(diagonal == 0.0):
        return float("-inf")
    return float(np.sum(np.log(diagonal)) / size)


def sparse_spectral_potential_grid(
    hamiltonian: sparse.spmatrix | np.ndarray,
    probe_energies: np.ndarray,
) -> np.ndarray:
    """Evaluate the exact finite-OBC potential on a probe grid by sparse LU."""

    probes = np.asarray(probe_energies, dtype=np.complex128)
    values = np.empty(probes.size, dtype=np.float64)
    for index, energy in enumerate(probes.reshape(-1)):
        values[index] = sparse_spectral_potential(hamiltonian, complex(energy))
    return values.reshape(probes.shape)


def ronkin_potential(
    energy: complex,
    hoppings: HoppingModel,
    *,
    deformation_x: float,
    deformation_y: float,
    momentum_samples: int,
) -> float:
    """Evaluate the two-dimensional Ronkin integral in formal Eq. (12)."""

    if momentum_samples < 8:
        raise ValueError("momentum_samples must be at least 8")
    momentum = (np.arange(momentum_samples, dtype=np.float64) + 0.5) * (
        2.0 * np.pi / momentum_samples
    )
    beta_x = np.exp(float(deformation_x) + 1j * momentum)[None, :]
    beta_y = np.exp(float(deformation_y) + 1j * momentum)[:, None]
    characteristic = np.full(
        (momentum_samples, momentum_samples),
        -complex(energy),
        dtype=np.complex128,
    )
    for (dx, dy), amplitude in hoppings.items():
        characteristic += complex(amplitude) * beta_x**dx * beta_y**dy
    magnitude = np.maximum(np.abs(characteristic), np.finfo(np.float64).tiny)
    return float(np.mean(np.log(magnitude)))


def amoeba_potential(
    energy: complex,
    hoppings: HoppingModel,
    *,
    momentum_samples: int = 96,
    deformation_bounds: tuple[float, float] = (-2.5, 2.5),
    tolerance: float = 1e-4,
) -> AmoebaMinimum:
    """Minimize the Ronkin potential over both imaginary momentum shifts."""

    lower, upper = deformation_bounds
    if lower >= upper:
        raise ValueError("deformation_bounds must be increasing")

    def objective(deformation: np.ndarray) -> float:
        return ronkin_potential(
            energy,
            hoppings,
            deformation_x=float(deformation[0]),
            deformation_y=float(deformation[1]),
            momentum_samples=momentum_samples,
        )

    starts = (
        np.array((0.0, 0.0)),
        np.array((0.35, 0.0)),
        np.array((-0.35, 0.0)),
        np.array((0.0, 0.35)),
        np.array((0.0, -0.35)),
    )
    results = [
        minimize(
            objective,
            start,
            method="Powell",
            bounds=((lower, upper), (lower, upper)),
            options={"xtol": tolerance, "ftol": tolerance, "maxiter": 120},
        )
        for start in starts
    ]
    successful = [result for result in results if result.success and np.isfinite(result.fun)]
    if not successful:
        raise RuntimeError(f"Amoeba minimization failed at E={energy}")
    result = min(successful, key=lambda item: float(item.fun))
    return AmoebaMinimum(
        potential=float(result.fun),
        deformation_x=float(result.x[0]),
        deformation_y=float(result.x[1]),
        evaluations=int(sum(item.nfev for item in results)),
    )


def basis_hopping_model(hoppings: HoppingModel, basis: str) -> dict[Site, complex]:
    """Express a Cartesian Laurent hopping model in a lattice-cut basis."""

    if basis == "square":
        return {
            displacement: complex(amplitude)
            for displacement, amplitude in hoppings.items()
        }
    if basis != "rhombus":
        raise ValueError(f"unsupported cut basis: {basis}")

    transformed: dict[Site, complex] = {}
    for (dx, dy), amplitude in hoppings.items():
        # beta_x = beta_1 / beta_2 and beta_y = beta_1 * beta_2.
        displacement = (dx + dy, -dx + dy)
        transformed[displacement] = (
            transformed.get(displacement, 0.0j) + complex(amplitude)
        )
    return transformed


def _batched_polynomial_roots(coefficients: np.ndarray) -> np.ndarray:
    """Return roots for rows of descending-order polynomial coefficients."""

    values = np.asarray(coefficients, dtype=np.complex128)
    if values.ndim != 2 or values.shape[1] < 2:
        raise ValueError("coefficients must have shape (batch, degree + 1)")
    degree = values.shape[1] - 1
    leading = values[:, 0]
    if np.any(np.abs(leading) < 1e-14):
        raise FloatingPointError("slice polynomial lost its leading coefficient")
    normalized = values[:, 1:] / leading[:, None]
    if degree == 1:
        return -normalized
    companions = np.zeros((values.shape[0], degree, degree), dtype=np.complex128)
    companions[:, 0, :] = -normalized
    rows = np.arange(1, degree)
    companions[:, rows, rows - 1] = 1.0
    return np.asarray(np.linalg.eigvals(companions), dtype=np.complex128)


def cylindrical_root_potential(
    energy: complex,
    hoppings: HoppingModel,
    *,
    outer_axis: int,
    deformation: float,
    momentum_samples: int,
) -> float:
    """Evaluate one deformed cylindrical integral using the Eq. (4) roots."""

    if outer_axis not in (0, 1):
        raise ValueError("outer_axis must be 0 or 1")
    if momentum_samples < 8:
        raise ValueError("momentum_samples must be at least 8")
    inner_axis = 1 - outer_axis
    inner_exponents = [displacement[inner_axis] for displacement in hoppings]
    minimum_exponent = min(0, min(inner_exponents))
    maximum_exponent = max(0, max(inner_exponents))
    p = -minimum_exponent
    q = maximum_exponent
    degree = p + q
    if degree < 1:
        raise ValueError("the inner direction has no hopping range")

    momenta = (np.arange(momentum_samples, dtype=np.float64) + 0.5) * (
        2.0 * np.pi / momentum_samples
    )
    outer_beta = np.exp(deformation + 1j * momenta)
    coefficients = np.zeros((momentum_samples, degree + 1), dtype=np.complex128)
    for displacement, amplitude in hoppings.items():
        inner_exponent = displacement[inner_axis]
        outer_exponent = displacement[outer_axis]
        descending_index = degree - (inner_exponent + p)
        coefficients[:, descending_index] += amplitude * outer_beta**outer_exponent
    coefficients[:, degree - p] -= energy

    roots = _batched_polynomial_roots(coefficients)
    root_moduli = np.sort(np.abs(roots), axis=1)
    selected = root_moduli[:, p : p + q]
    tiny = np.finfo(np.float64).tiny
    slice_potential = np.sum(np.log(np.maximum(selected, tiny)), axis=1)
    slice_potential += np.log(np.maximum(np.abs(coefficients[:, 0]), tiny))
    return float(np.mean(slice_potential))


def minimize_cylindrical_potential(
    energy: complex,
    hoppings: HoppingModel,
    *,
    outer_axis: int,
    momentum_samples: int,
    deformation_bounds: tuple[float, float],
    tolerance: float,
) -> CylindricalMinimum:
    """Minimize one cylindrical branch over its imaginary momentum shift."""

    def objective(deformation: float) -> float:
        return cylindrical_root_potential(
            energy,
            hoppings,
            outer_axis=outer_axis,
            deformation=float(deformation),
            momentum_samples=momentum_samples,
        )

    result = minimize_scalar(
        objective,
        bounds=deformation_bounds,
        method="bounded",
        options={"xatol": tolerance, "maxiter": 80},
    )
    if not result.success or not np.isfinite(result.fun):
        raise RuntimeError(f"cylindrical minimization failed at E={energy}: {result.message}")
    return CylindricalMinimum(
        potential=float(result.fun),
        deformation=float(result.x),
        evaluations=int(result.nfev),
    )


def geometry_adaptive_potential(
    energy: complex,
    hoppings: HoppingModel,
    *,
    basis: str,
    momentum_samples: int,
    deformation_bounds: tuple[float, float] = (-1.5, 1.5),
    tolerance: float = 1e-4,
) -> GeometryPotential:
    """Evaluate Eqs. (8)-(10) in the square or rhombus cut basis."""

    basis_hoppings = basis_hopping_model(hoppings, basis)
    cylinder_1 = minimize_cylindrical_potential(
        energy,
        basis_hoppings,
        outer_axis=0,
        momentum_samples=momentum_samples,
        deformation_bounds=deformation_bounds,
        tolerance=tolerance,
    )
    cylinder_2 = minimize_cylindrical_potential(
        energy,
        basis_hoppings,
        outer_axis=1,
        momentum_samples=momentum_samples,
        deformation_bounds=deformation_bounds,
        tolerance=tolerance,
    )
    return GeometryPotential(
        potential=min(cylinder_1.potential, cylinder_2.potential),
        cylinder_1=cylinder_1,
        cylinder_2=cylinder_2,
    )


def spectral_density_from_potential(
    potential: np.ndarray,
    *,
    real_step: float,
    imaginary_step: float,
    trim_boundary: bool = False,
) -> np.ndarray:
    """Apply Eq. (3) with the paper's three-point central Laplacian.

    The stencil is defined only on the interior grid. ``trim_boundary=True``
    returns that exact ``(ny - 2, nx - 2)`` array used by the author notebook.
    The default keeps the input shape for structured output files and fills the
    unevaluable outer ring with zero.
    """

    values = np.asarray(potential, dtype=np.float64)
    if values.ndim != 2 or min(values.shape) < 3:
        raise ValueError("potential must be a two-dimensional grid of at least 3 x 3")
    center = values[1:-1, 1:-1]
    second_real = (
        values[1:-1, 2:] + values[1:-1, :-2] - 2.0 * center
    ) / real_step**2
    second_imaginary = (
        values[2:, 1:-1] + values[:-2, 1:-1] - 2.0 * center
    ) / imaginary_step**2
    interior = np.asarray(
        (second_real + second_imaginary) / (2.0 * np.pi),
        dtype=np.float64,
    )
    if trim_boundary:
        return interior
    density = np.zeros_like(values)
    density[1:-1, 1:-1] = interior
    return density


def spectrum_metrics(eigenvalues: np.ndarray) -> dict[str, float]:
    """Return ordering-free support metrics for a complex spectrum."""

    values = np.asarray(eigenvalues, dtype=np.complex128)
    points = np.column_stack((values.real, values.imag))
    hull_area = 0.0
    if len(points) >= 3:
        try:
            hull_area = float(ConvexHull(points).volume)
        except Exception:
            hull_area = 0.0
    return {
        "count": int(values.size),
        "real_min": float(values.real.min()),
        "real_max": float(values.real.max()),
        "imag_min": float(values.imag.min()),
        "imag_max": float(values.imag.max()),
        "real_span": float(np.ptp(values.real)),
        "imag_span": float(np.ptp(values.imag)),
        "centroid_real": float(values.real.mean()),
        "centroid_imag": float(values.imag.mean()),
        "hull_area": hull_area,
    }


def symmetric_cloud_distance(first: np.ndarray, second: np.ndarray) -> dict[str, float]:
    """Nearest-neighbor distance in both directions between complex point clouds."""

    first_points = _complex_points(first)
    second_points = _complex_points(second)
    first_to_second = cKDTree(second_points).query(first_points, k=1)[0]
    second_to_first = cKDTree(first_points).query(second_points, k=1)[0]
    combined = np.concatenate((first_to_second, second_to_first))
    return {
        "mean": float(combined.mean()),
        "median": float(np.median(combined)),
        "p95": float(np.quantile(combined, 0.95)),
        "max": float(combined.max()),
    }


def density_metrics(sites: Sequence[Site], density: np.ndarray) -> dict[str, object]:
    """Summarize the location and concentration of aggregate eigenstate density."""

    values = np.asarray(density, dtype=float)
    if len(sites) != len(values):
        raise ValueError("site and density lengths differ")
    if np.any(values < 0) or values.sum() <= 0:
        raise ValueError("density must be non-negative with positive total weight")
    coords = np.asarray(sites, dtype=float)
    normalized = values / values.sum()
    maximum = int(np.argmax(values))
    top_count = max(1, int(np.ceil(0.01 * len(values))))
    top_indices = np.argpartition(values, -top_count)[-top_count:]
    center = np.sum(coords * normalized[:, None], axis=0)
    return {
        "max_site": [int(sites[maximum][0]), int(sites[maximum][1])],
        "center_of_mass": [float(center[0]), float(center[1])],
        "max_normalized_density": float(normalized[maximum]),
        "top_one_percent_weight": float(normalized[top_indices].sum()),
    }


def _as_dense(hamiltonian: sparse.spmatrix | np.ndarray) -> np.ndarray:
    if sparse.issparse(hamiltonian):
        return np.asarray(hamiltonian.toarray(), dtype=np.complex128, order="F")
    return np.array(hamiltonian, dtype=np.complex128, order="F", copy=True)


def _complex_points(values: Iterable[complex]) -> np.ndarray:
    array = np.asarray(tuple(values), dtype=np.complex128)
    if array.size == 0:
        raise ValueError("point cloud must be non-empty")
    return np.column_stack((array.real, array.imag))
