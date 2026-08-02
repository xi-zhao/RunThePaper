"""Independent numerical objects for arXiv:1706.07435.

The functions in this module implement equations from the paper.  They never
read the source figures or any digitized source data.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike, NDArray


ComplexArray = NDArray[np.complex128]
FloatArray = NDArray[np.float64]

SIGMA_X: ComplexArray = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=np.complex128)
SIGMA_Y: ComplexArray = np.array([[0.0, -1.0j], [1.0j, 0.0]], dtype=np.complex128)
SIGMA_Z: ComplexArray = np.array([[1.0, 0.0], [0.0, -1.0]], dtype=np.complex128)

# The paper explicitly uses sigma_+ = sigma_x + i sigma_y, without 1/2.
SIGMA_PLUS: ComplexArray = SIGMA_X + 1.0j * SIGMA_Y


@dataclass(frozen=True)
class DiracDomain:
    """Constant parameters on one side of a continuum Dirac domain wall."""

    kappa_x: float
    kappa_y: float
    mass: float
    delta: float


@dataclass(frozen=True)
class DomainWallSolution:
    """One localized common-spinor solution of Supplement Eqs. (10)-(12)."""

    energy: complex
    inverse_length_left: complex
    inverse_length_right: complex
    spinor: ComplexArray
    equation_residual: float
    localization_margin: float


def _complex_array(value: ArrayLike) -> ComplexArray:
    return np.asarray(value, dtype=np.complex128)


def dirac_radicand(
    kx: ArrayLike,
    ky: ArrayLike,
    *,
    kappa_x: float,
    kappa_y: float,
    mass: float,
    delta: float,
) -> ComplexArray:
    """Return ``E^2`` for main-text Eq. (4)."""

    kx_array = _complex_array(kx)
    ky_array = _complex_array(ky)
    kappa_sq = kappa_x**2 + kappa_y**2
    constant = mass**2 - delta**2 - kappa_sq
    real_part = kx_array**2 + ky_array**2 + constant
    imag_part = 2.0j * (kx_array * kappa_x + ky_array * kappa_y + mass * delta)
    return real_part + imag_part


def dirac_eigenvalues(
    kx: ArrayLike,
    ky: ArrayLike,
    *,
    kappa_x: float,
    kappa_y: float,
    mass: float,
    delta: float,
) -> tuple[ComplexArray, ComplexArray]:
    """Return the two principal square-root sheets of main-text Eq. (4)."""

    plus = np.sqrt(
        dirac_radicand(
            kx,
            ky,
            kappa_x=kappa_x,
            kappa_y=kappa_y,
            mass=mass,
            delta=delta,
        )
    )
    return plus, -plus


def dirac_hamiltonian(
    kx: float,
    ky: float,
    *,
    kappa_x: float,
    kappa_y: float,
    mass: float,
    delta: float,
) -> ComplexArray:
    """Return the 2x2 generalized Dirac Hamiltonian of main Eq. (4)."""

    return (
        (kx + 1.0j * kappa_x) * SIGMA_X
        + (ky + 1.0j * kappa_y) * SIGMA_Y
        + (mass + 1.0j * delta) * SIGMA_Z
    )


def domain_ansatz_hamiltonian(ky: float, inverse_length: complex, domain: DiracDomain) -> ComplexArray:
    """Return the constant 2x2 matrix after the domain-wall exponential ansatz."""

    shifted_inverse_length = inverse_length - domain.kappa_x
    return (
        (-1.0j * shifted_inverse_length) * SIGMA_X
        + (ky + 1.0j * domain.kappa_y) * SIGMA_Y
        + (domain.mass + 1.0j * domain.delta) * SIGMA_Z
    )


def solve_domain_wall_edge(ky: float, left: DiracDomain, right: DiracDomain) -> DomainWallSolution:
    """Solve the common-spinor matching problem in closed form.

    Subtracting the two ansatz Hamiltonians shows that the difference in the
    shifted inverse lengths is a momentum-independent complex square root.
    Equality of the two characteristic polynomials then fixes their sum.  Of
    the two algebraic roots, this routine selects the one satisfying
    ``Re(q_left)>0`` and ``Re(q_right)<0``.
    """

    momentum_left = ky + 1.0j * left.kappa_y
    momentum_right = ky + 1.0j * right.kappa_y
    mass_left = left.mass + 1.0j * left.delta
    mass_right = right.mass + 1.0j * right.delta
    delta_momentum = momentum_left - momentum_right
    delta_mass = mass_left - mass_right
    principal_difference = np.sqrt(delta_momentum**2 + delta_mass**2)
    if abs(principal_difference) < 1e-14:
        raise ValueError("domain-wall matching is singular for identical or critically merged domains")

    candidates: list[DomainWallSolution] = []
    for shifted_difference in (principal_difference, -principal_difference):
        shifted_sum = (
            delta_mass * (mass_left + mass_right)
            + delta_momentum * (momentum_left + momentum_right)
        ) / shifted_difference
        shifted_left = 0.5 * (shifted_sum + shifted_difference)
        shifted_right = 0.5 * (shifted_sum - shifted_difference)
        inverse_left = shifted_left + left.kappa_x
        inverse_right = shifted_right + right.kappa_x
        localization_margin = float(min(inverse_left.real, -inverse_right.real))
        if localization_margin <= 0.0:
            continue

        hamiltonian_left = domain_ansatz_hamiltonian(ky, inverse_left, left)
        hamiltonian_right = domain_ansatz_hamiltonian(ky, inverse_right, right)
        difference_matrix = hamiltonian_left - hamiltonian_right
        _, _, right_singular_vectors = np.linalg.svd(difference_matrix)
        spinor = right_singular_vectors.conj().T[:, -1]
        spinor = spinor / np.linalg.norm(spinor)
        energy = complex(np.vdot(spinor, hamiltonian_left @ spinor))

        left_vector_residual = np.linalg.norm(hamiltonian_left @ spinor - energy * spinor)
        right_vector_residual = np.linalg.norm(hamiltonian_right @ spinor - energy * spinor)
        left_determinant_residual = abs(
            energy**2 - (mass_left**2 + momentum_left**2 - shifted_left**2)
        )
        right_determinant_residual = abs(
            energy**2 - (mass_right**2 + momentum_right**2 - shifted_right**2)
        )
        matching_residual = abs(
            (mass_left + energy) * (momentum_right - shifted_right)
            - (mass_right + energy) * (momentum_left - shifted_left)
        )
        equation_residual = float(
            max(
                left_vector_residual,
                right_vector_residual,
                left_determinant_residual,
                right_determinant_residual,
                matching_residual,
            )
        )
        candidates.append(
            DomainWallSolution(
                energy=energy,
                inverse_length_left=complex(inverse_left),
                inverse_length_right=complex(inverse_right),
                spinor=np.asarray(spinor, dtype=np.complex128),
                equation_residual=equation_residual,
                localization_margin=localization_margin,
            )
        )

    if not candidates:
        raise ValueError("no algebraic domain-wall root satisfies both localization inequalities")
    return min(candidates, key=lambda candidate: (candidate.equation_residual, -candidate.localization_margin))


def symmetric_domain_wall_energy(
    kappa_left_y: ArrayLike,
    kappa_right_y: ArrayLike,
    *,
    mass_scale: float = 1.0,
) -> ComplexArray:
    """Closed-form Supplement Figure 2 energy at ``ky=0``.

    This is the ``m_left=-m_scale``, ``m_right=+m_scale`` and
    ``kappa_x=delta=0`` specialization of :func:`solve_domain_wall_edge`.
    """

    left_values = np.asarray(kappa_left_y, dtype=np.float64)
    right_values = np.asarray(kappa_right_y, dtype=np.float64)
    denominator_squared = (2.0 * mass_scale) ** 2 - (left_values - right_values) ** 2
    if np.any(denominator_squared <= 0.0):
        raise ValueError("separable localized solution requires |kappa_left_y-kappa_right_y| < 2|m|")
    denominator = np.sqrt(denominator_squared)
    return np.asarray(
        1.0j * mass_scale * (left_values + right_values) / denominator,
        dtype=np.complex128,
    )


def exceptional_points(
    *,
    kappa_x: float,
    kappa_y: float,
    mass: float,
    delta: float,
) -> FloatArray:
    """Return the two main-text exceptional points as a ``(2, 2)`` array.

    Raises ``ValueError`` outside the EP-pair phase because the printed
    momentum coordinates are then not real.
    """

    kappa = float(np.hypot(kappa_x, kappa_y))
    if kappa == 0.0:
        raise ValueError("exceptional-point pair requires nonzero |kappa|")
    if abs(mass) >= kappa:
        raise ValueError("real isolated exceptional points require |mass| < |kappa|")

    direction = np.array([kappa_x, kappa_y], dtype=np.float64) / kappa
    perpendicular = np.array([-direction[1], direction[0]], dtype=np.float64)
    center = -(mass * delta / kappa) * direction
    displacement = np.sqrt((kappa**2 - mass**2) * (kappa**2 + delta**2)) / kappa
    return np.stack((center + displacement * perpendicular, center - displacement * perpendicular))


def exceptional_trajectory(
    masses: ArrayLike,
    *,
    kappa_x: float,
    kappa_y: float,
    delta: float,
) -> FloatArray:
    """Evaluate the closed-form EP pair along a mass trajectory.

    The endpoint values ``|mass|=|kappa|`` are included and represent the two
    hybrid points where the pair coalesces.  Values outside that interval are
    rejected because the isolated exceptional momenta cease to be real.
    """

    mass_array = np.asarray(masses, dtype=np.float64)
    kappa = float(np.hypot(kappa_x, kappa_y))
    if kappa == 0.0:
        raise ValueError("exceptional-point trajectory requires nonzero |kappa|")
    if np.any(np.abs(mass_array) > kappa + 1e-14):
        raise ValueError("real exceptional-point trajectory requires |mass| <= |kappa|")

    direction = np.array([kappa_x, kappa_y], dtype=np.float64) / kappa
    perpendicular = np.array([-direction[1], direction[0]], dtype=np.float64)
    center = -(mass_array[..., None] * delta / kappa) * direction
    displacement = (
        np.sqrt(np.maximum(0.0, (kappa**2 - mass_array**2) * (kappa**2 + delta**2)))
        / kappa
    )
    return np.stack(
        (center + displacement[..., None] * perpendicular, center - displacement[..., None] * perpendicular),
        axis=-2,
    )


def exceptional_point_hamiltonian(kx: float, ky: float) -> ComplexArray:
    """Canonical Hamiltonian used in main Figure 2."""

    return SIGMA_PLUS + kx * SIGMA_X + ky * SIGMA_Y


def exceptional_radicand(kx: ArrayLike, ky: ArrayLike) -> ComplexArray:
    """Return ``E^2=kx^2+ky^2+2*kx+2i*ky`` for main Figure 2."""

    kx_array = _complex_array(kx)
    ky_array = _complex_array(ky)
    return kx_array**2 + ky_array**2 + 2.0 * kx_array + 2.0j * ky_array


def exceptional_eigenvalues(kx: ArrayLike, ky: ArrayLike) -> tuple[ComplexArray, ComplexArray]:
    """Return the principal sheets of the canonical exceptional-point model."""

    plus = np.sqrt(exceptional_radicand(kx, ky))
    return plus, -plus


def tracked_exceptional_loop(
    theta: ArrayLike,
    *,
    radius: float = 1.0,
) -> dict[str, FloatArray | ComplexArray]:
    """Track both energy sheets continuously around a circular momentum loop.

    A pointwise principal square root has an artificial branch-cut jump.  The
    phase of ``E^2`` is therefore unwrapped before it is halved.
    """

    theta_array = np.asarray(theta, dtype=np.float64)
    kx = radius * np.cos(theta_array)
    ky = radius * np.sin(theta_array)
    radicand = exceptional_radicand(kx, ky)
    unwrapped_phase = np.unwrap(np.angle(radicand))
    plus = np.sqrt(np.abs(radicand)) * np.exp(0.5j * unwrapped_phase)
    return {
        "theta": theta_array,
        "kx": kx,
        "ky": ky,
        "radicand": radicand,
        "e_plus": plus,
        "e_minus": -plus,
    }


def energy_difference_vorticity(energy_difference: ArrayLike) -> float:
    """Discretize main-text Eq. (8) on an ordered closed loop."""

    values = _complex_array(energy_difference)
    if values.ndim != 1 or values.size < 2:
        raise ValueError("energy_difference must be a one-dimensional loop")
    if np.any(np.abs(values) == 0.0):
        raise ValueError("vorticity is undefined on a loop containing a degeneracy")
    phase = np.unwrap(np.angle(values))
    return float(-(phase[-1] - phase[0]) / (2.0 * np.pi))


def hybrid_eigenvalues(
    kx: ArrayLike,
    ky: ArrayLike,
    *,
    mass: float = 1.0,
    delta: float = 1.0,
) -> tuple[ComplexArray, ComplexArray]:
    """Return eigenvalues for Supplement Eq. (20)."""

    kx_array = _complex_array(kx)
    ky_array = _complex_array(ky)
    constant = mass**2 - delta**2
    radicand = kx_array**2 + ky_array**2 + constant + 2.0j * delta * kx_array
    plus = np.sqrt(radicand)
    return plus, -plus


def hybrid_hamiltonian(
    kx: float,
    ky: float,
    *,
    mass: float = 1.0,
    delta: float = 1.0,
) -> ComplexArray:
    """Return the 2x2 Hamiltonian of Supplement Eq. (20)."""

    return (kx + 1.0j * delta) * SIGMA_X + ky * SIGMA_Y + mass * SIGMA_Z


def tracked_hybrid_loop(
    theta: ArrayLike,
    *,
    radius: float = 1.0,
    mass: float = 1.0,
    delta: float = 1.0,
) -> dict[str, FloatArray | ComplexArray]:
    """Track the hybrid-point sheets continuously around a circular loop."""

    theta_array = np.asarray(theta, dtype=np.float64)
    kx = radius * np.cos(theta_array)
    ky = radius * np.sin(theta_array)
    radicand = kx**2 + ky**2 + mass**2 - delta**2 + 2.0j * delta * kx
    unwrapped_phase = np.unwrap(np.angle(radicand))
    plus = np.sqrt(np.abs(radicand)) * np.exp(0.5j * unwrapped_phase)
    return {
        "theta": theta_array,
        "kx": kx,
        "ky": ky,
        "radicand": radicand,
        "e_plus": plus,
        "e_minus": -plus,
    }


def lattice_bloch_hamiltonian(
    kx: float,
    ky: float,
    *,
    kappa_x: float,
    kappa_y: float,
    mass: float,
    delta: float,
    hopping: float = 1.0,
) -> ComplexArray:
    """Return the square-lattice Bloch Hamiltonian of Supplement Eq. (13)."""

    return (
        (hopping * np.sin(kx) + 1.0j * kappa_x) * SIGMA_X
        + (hopping * np.sin(ky) + 1.0j * kappa_y) * SIGMA_Y
        + (np.cos(kx) + np.cos(ky) + mass + 1.0j * delta) * SIGMA_Z
    )


def cylinder_blocks(
    ky: float,
    *,
    kappa_x: float,
    kappa_y: float,
    mass: float,
    delta: float,
    hopping: float = 1.0,
) -> tuple[ComplexArray, ComplexArray, ComplexArray]:
    """Return onsite, forward, and reverse blocks for an open-x cylinder."""

    onsite = (
        1.0j * kappa_x * SIGMA_X
        + (hopping * np.sin(ky) + 1.0j * kappa_y) * SIGMA_Y
        + (np.cos(ky) + mass + 1.0j * delta) * SIGMA_Z
    )
    forward = 0.5 * SIGMA_Z + hopping * SIGMA_X / (2.0j)
    reverse = 0.5 * SIGMA_Z - hopping * SIGMA_X / (2.0j)
    return onsite, forward, reverse


def cylinder_hamiltonian(
    sites: int,
    ky: float,
    *,
    kappa_x: float,
    kappa_y: float,
    mass: float,
    delta: float,
    hopping: float = 1.0,
) -> ComplexArray:
    """Build the paper's ``2*sites`` open-x, periodic-y cylinder matrix."""

    if sites < 2:
        raise ValueError("cylinder requires at least two x sites")
    onsite, forward, reverse = cylinder_blocks(
        ky,
        kappa_x=kappa_x,
        kappa_y=kappa_y,
        mass=mass,
        delta=delta,
        hopping=hopping,
    )
    matrix = np.zeros((2 * sites, 2 * sites), dtype=np.complex128)
    for site in range(sites):
        row = slice(2 * site, 2 * site + 2)
        matrix[row, row] = onsite
        if site + 1 < sites:
            next_site = slice(2 * (site + 1), 2 * (site + 1) + 2)
            matrix[row, next_site] = forward
            matrix[next_site, row] = reverse
    return matrix


def cylinder_boundary_weights(
    eigenvectors: ArrayLike,
    *,
    sites: int,
    edge_sites: int = 4,
) -> tuple[FloatArray, FloatArray]:
    """Return normalized left/right boundary weights for column eigenvectors."""

    vectors = _complex_array(eigenvectors)
    if vectors.shape[0] != 2 * sites:
        raise ValueError("eigenvector row count must equal 2*sites")
    if not 1 <= edge_sites <= sites // 2:
        raise ValueError("edge_sites must lie between one and half the cylinder")
    probabilities = np.abs(vectors.reshape(sites, 2, -1)) ** 2
    site_probabilities = probabilities.sum(axis=1)
    normalization = site_probabilities.sum(axis=0)
    if np.any(normalization == 0.0):
        raise ValueError("zero-norm eigenvector encountered")
    left = site_probabilities[:edge_sites].sum(axis=0) / normalization
    right = site_probabilities[-edge_sites:].sum(axis=0) / normalization
    return np.asarray(left, dtype=np.float64), np.asarray(right, dtype=np.float64)


def unordered_pair_error(expected: ArrayLike, actual: ArrayLike) -> float:
    """Maximum error between two unordered two-eigenvalue sets."""

    expected_pair = _complex_array(expected).reshape(2)
    actual_pair = _complex_array(actual).reshape(2)
    direct = max(abs(expected_pair[0] - actual_pair[0]), abs(expected_pair[1] - actual_pair[1]))
    swapped = max(abs(expected_pair[0] - actual_pair[1]), abs(expected_pair[1] - actual_pair[0]))
    return float(min(direct, swapped))
