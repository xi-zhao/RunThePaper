"""Formula-level implementation of the Lipkin-Meshkov-Glick Hamiltonian.

The code uses only the Hamiltonian printed in Eq. (1).  In a fixed ``J_z``
parity sector the matrix is tridiagonal because ``J_x^2-J_y^2`` changes
``m`` by two.  This gives an exact, memory-light solver up to the paper's
``N=5000`` without importing author code or numerical arrays.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.integrate import quad
from scipy.linalg import eigh_tridiagonal
from scipy.optimize import root


@dataclass(frozen=True)
class SectorSpectrum:
    """One invariant ``m``-parity sector of the finite-N Hamiltonian."""

    m: np.ndarray
    energies: np.ndarray
    eigenvectors: np.ndarray | None = None


def sector_diagonals(
    particles: int, coupling: float, sector: int = 0
) -> tuple[np.ndarray, np.ndarray]:
    """Return diagonal/off-diagonal arrays for one exact parity block.

    ``sector=0`` starts at ``m=-j`` and ``sector=1`` at ``m=-j+1``.
    The printed Hamiltonian gives

    ``<m+2|H|m> = lambda/(2N) * sqrt((j-m)(j+m+1)(j-m-1)(j+m+2))``.
    """

    if particles < 2:
        raise ValueError("particles must be at least two")
    if sector not in (0, 1):
        raise ValueError("sector must be zero or one")
    j = particles / 2.0
    m = np.arange(-j + sector, j + 1.0, 2.0, dtype=float)
    left = m[:-1]
    radicand = (j - left) * (j + left + 1.0) * (j - left - 1.0) * (j + left + 2.0)
    off_diagonal = coupling / (2.0 * particles) * np.sqrt(np.maximum(radicand, 0.0))
    return m, off_diagonal


def lmg_sector(
    particles: int,
    coupling: float,
    sector: int = 0,
    *,
    eigenvectors: bool = False,
) -> SectorSpectrum:
    """Diagonalize one exact parity block with a symmetric tridiagonal solver."""

    diagonal, off_diagonal = sector_diagonals(particles, coupling, sector)
    result = eigh_tridiagonal(diagonal, off_diagonal, eigvals_only=not eigenvectors)
    if eigenvectors:
        energies, vectors = result
        return SectorSpectrum(diagonal, energies, vectors)
    return SectorSpectrum(diagonal, result)


def classical_minimum_mu(coupling: float) -> float:
    """Positive classical minimum from Eqs. (4)-(5)."""

    if coupling <= 1.0:
        return 0.0
    return float(np.sqrt(1.0 - coupling**-2))


def classical_ground_energy(particles: int, coupling: float) -> float:
    """Extensive classical ground energy in Eq. (6)."""

    if coupling <= 1.0:
        return -particles / 2.0
    return -particles * (coupling + 1.0 / coupling) / 4.0


def theory_separatrix_coefficient(coupling: float) -> float:
    """The coefficient ``2*pi*sqrt(lambda^2-1)`` in Eq. (12)."""

    if coupling <= 1.0:
        raise ValueError("the separatrix exists only for coupling > 1")
    return float(2.0 * np.pi * np.sqrt(coupling * coupling - 1.0))


def separatrix_spacing(
    particles: int, coupling: float, sector: int = 0
) -> dict[str, float | int]:
    """Return the same-parity level gap whose midpoint is nearest ``E_c=-N/2``.

    The paper does not specify a tie-breaking convention.  Selecting by the
    midpoint makes the observable explicit and avoids tuning to source pixels.
    """

    energies = lmg_sector(particles, coupling, sector).energies
    midpoints = 0.5 * (energies[:-1] + energies[1:])
    index = int(np.argmin(np.abs(midpoints + particles / 2.0)))
    lower = float(energies[index])
    upper = float(energies[index + 1])
    return {
        "particles": particles,
        "coupling": coupling,
        "sector": sector,
        "lower_index": index,
        "lower_energy": lower,
        "upper_energy": upper,
        "midpoint_offset": float(0.5 * (lower + upper) + particles / 2.0),
        "spacing": upper - lower,
    }


def separatrix_spacing_with_selector(
    particles: int,
    coupling: float,
    sector: int = 0,
    *,
    selector: str = "midpoint_nearest",
    local_pair_count: int = 7,
) -> dict[str, float | int | str]:
    """Resolve the publication's unspecified finite-N separatrix pair.

    The paper fixes the target energy ``E_c=-N/2`` but does not say how a
    discrete same-parity spectrum is mapped to that energy.  Keeping the
    alternatives in one function makes that ambiguity observable instead of
    hiding it in plotting code.

    ``midpoint_nearest`` chooses the pair whose midpoint is nearest ``E_c``.
    ``straddling`` chooses the pair containing ``E_c`` (falling back to the
    nearest midpoint).  ``local_minimum_gap`` searches only among the
    ``local_pair_count`` pairs nearest ``E_c``; the locality guard prevents an
    unrelated minimum elsewhere in the band from being selected.
    """

    if local_pair_count < 1 or local_pair_count % 2 == 0:
        raise ValueError("local_pair_count must be a positive odd integer")
    spectrum = lmg_sector(particles, coupling, sector)
    energies = spectrum.energies
    gaps = np.diff(energies)
    midpoints = 0.5 * (energies[:-1] + energies[1:])
    critical_energy = -particles / 2.0

    if selector == "midpoint_nearest":
        index = int(np.argmin(np.abs(midpoints - critical_energy)))
    elif selector == "straddling":
        candidates = np.flatnonzero(
            (energies[:-1] <= critical_energy) & (critical_energy <= energies[1:])
        )
        index = (
            int(candidates[0])
            if len(candidates)
            else int(np.argmin(np.abs(midpoints - critical_energy)))
        )
    elif selector == "local_minimum_gap":
        count = min(local_pair_count, len(gaps))
        local = np.argsort(np.abs(midpoints - critical_energy))[:count]
        index = int(local[np.argmin(gaps[local])])
    else:
        raise ValueError(f"unknown separatrix selector: {selector}")

    lower = float(energies[index])
    upper = float(energies[index + 1])
    return {
        "particles": particles,
        "coupling": coupling,
        "sector": sector,
        "selector": selector,
        "lower_index": index,
        "lower_energy": lower,
        "upper_energy": upper,
        "midpoint_offset": 0.5 * (lower + upper) - critical_energy,
        "spacing": upper - lower,
    }


def local_separatrix_spacing(
    particles: int,
    coupling: float,
    sector: int = 0,
    *,
    energy_half_width: float = 10.0,
) -> float:
    """Return the midpoint-nearest gap without diagonalizing the full band.

    This is mathematically the same selector as ``separatrix_spacing`` but
    uses LAPACK's value-range mode.  It permits honest large-N convergence
    tests while retaining only a few eigenvalues around ``E_c``.
    """

    if energy_half_width <= 0.0:
        raise ValueError("energy_half_width must be positive")
    diagonal, off_diagonal = sector_diagonals(particles, coupling, sector)
    critical_energy = -particles / 2.0
    energies = eigh_tridiagonal(
        diagonal,
        off_diagonal,
        eigvals_only=True,
        select="v",
        select_range=(
            critical_energy - energy_half_width,
            critical_energy + energy_half_width,
        ),
    )
    if len(energies) < 2:
        raise RuntimeError("separatrix window contains fewer than two levels")
    midpoints = 0.5 * (energies[:-1] + energies[1:])
    index = int(np.argmin(np.abs(midpoints - critical_energy)))
    return float(energies[index + 1] - energies[index])


def critical_excitation_spectrum(
    particles: int,
    level_count: int = 500,
    sector: int = 0,
) -> tuple[np.ndarray, np.ndarray]:
    """Return ``k`` and excitation energies at the critical point ``lambda=1``."""

    energies = lmg_sector(particles, 1.0, sector).energies
    count = min(level_count, len(energies) - 1)
    k = np.arange(1, count + 1, dtype=int)
    excitation = energies[1 : count + 1] - energies[0]
    return k, excitation


def critical_excitation_spectra(
    particles: int,
    level_count: int = 500,
) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    """Return every reasonable parity/index convention for Main Fig. 2.

    The caption specifies ``N`` and the number of levels, but not whether
    ``k`` labels one parity block or the merged spectrum.  The literal merged
    interpretation and both invariant blocks are therefore frozen together.
    """

    sectors = {sector: lmg_sector(particles, 1.0, sector).energies for sector in (0, 1)}
    merged = np.sort(np.concatenate([sectors[0], sectors[1]]))
    output: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    for label, energies in (
        ("merged", merged),
        ("sector_0", sectors[0]),
        ("sector_1", sectors[1]),
    ):
        count = min(level_count, len(energies) - 1)
        k = np.arange(1, count + 1, dtype=int)
        output[label] = (k, energies[1 : count + 1] - energies[0])
    return output


def same_parity_spacing_profile(
    particles: int,
    coupling: float,
    sector: int,
    *,
    bin_count: int = 20,
) -> list[dict[str, float | int]]:
    """Bin every adjacent same-parity gap across the finite spectrum.

    The paper says that the normal-phase average spacing increases with
    energy.  A comparison between two hand-picked gaps cannot test that
    statement.  This routine keeps the entire band and makes the energy range
    explicit, so the increasing low-energy branch can be distinguished from
    the symmetry-related upper branch.
    """

    if bin_count < 4:
        raise ValueError("bin_count must be at least four")
    energies = lmg_sector(particles, coupling, sector).energies
    midpoints = 0.5 * (energies[:-1] + energies[1:])
    gaps = np.diff(energies)
    normalized = (midpoints - midpoints[0]) / (midpoints[-1] - midpoints[0])
    edges = np.linspace(0.0, 1.0, bin_count + 1)
    rows: list[dict[str, float | int]] = []
    for bin_index in range(bin_count):
        if bin_index == bin_count - 1:
            selected = (normalized >= edges[bin_index]) & (
                normalized <= edges[bin_index + 1]
            )
        else:
            selected = (normalized >= edges[bin_index]) & (
                normalized < edges[bin_index + 1]
            )
        if not np.any(selected):
            continue
        rows.append(
            {
                "particles": particles,
                "coupling": coupling,
                "sector": sector,
                "bin_index": bin_index,
                "normalized_energy": float(np.mean(normalized[selected])),
                "mean_energy": float(np.mean(midpoints[selected])),
                "mean_spacing": float(np.mean(gaps[selected])),
                "spacing_std": float(np.std(gaps[selected])),
                "level_pair_count": int(np.sum(selected)),
            }
        )
    return rows


def coordinate_ordered_sector(
    particles: int,
    coupling: float,
    sector: int,
    *,
    ordering: str,
) -> np.ndarray:
    """Quantize Eq. (15) with an explicit self-adjoint ordering.

    ``mu`` is diagonal and ``cos(2 phi)`` shifts ``m`` by two.  The two
    natural orderings below are both Hermitian but differ by sub-principal
    terms.  They are deliberately reported side by side because the paper
    does not identify a unique prescription.

    Returned eigenvalues use the normalized energy ``K=2H/N``.
    """

    m, _ = sector_diagonals(particles, 1.0, sector)
    mu = 2.0 * m / particles
    amplitude = np.maximum(1.0 - mu * mu, 0.0)
    if ordering == "symmetric":
        off_diagonal = coupling * (amplitude[:-1] + amplitude[1:]) / 8.0
    elif ordering == "sandwich":
        off_diagonal = coupling * np.sqrt(amplitude[:-1] * amplitude[1:]) / 4.0
    else:
        raise ValueError(f"unknown ordering: {ordering}")
    return eigh_tridiagonal(mu, off_diagonal, eigvals_only=True)


def characteristic_and_energy_derivative(
    particles: int,
    sector: int,
    energy: complex,
    coupling: complex,
) -> tuple[complex, complex]:
    """Evaluate ``det(H-E)`` and its energy derivative by recurrence.

    A complex exceptional point is a simultaneous root of these two
    quantities.  This avoids interpreting a small sampled avoided crossing as
    an exceptional point.
    """

    diagonal, unit_off_diagonal = sector_diagonals(particles, 1.0, sector)
    previous = 1.0 + 0.0j
    previous_derivative = 0.0 + 0.0j
    current = complex(diagonal[0] - energy)
    current_derivative = -1.0 + 0.0j
    for index in range(1, len(diagonal)):
        squared_off_diagonal = (coupling * unit_off_diagonal[index - 1]) ** 2
        following = (
            diagonal[index] - energy
        ) * current - squared_off_diagonal * previous
        following_derivative = (
            -current
            + (diagonal[index] - energy) * current_derivative
            - squared_off_diagonal * previous_derivative
        )
        previous, current = current, following
        previous_derivative, current_derivative = (
            current_derivative,
            following_derivative,
        )
    return current, current_derivative


def dense_complex_sector(
    particles: int,
    coupling: complex,
    sector: int,
) -> np.ndarray:
    """Return the finite parity block at complex coupling.

    This dense construction is deliberately separate from the characteristic
    recurrence.  It is used only to certify that a proposed double root also
    appears as a coalescing eigenvalue pair of the matrix itself.
    """

    diagonal, unit_off_diagonal = sector_diagonals(particles, 1.0, sector)
    off_diagonal = coupling * unit_off_diagonal
    return (
        np.diag(diagonal.astype(complex))
        + np.diag(off_diagonal, 1)
        + np.diag(off_diagonal, -1)
    )


def exceptional_point_certificate(
    particles: int,
    sector: int,
    energy: complex,
    coupling: complex,
) -> dict[str, float]:
    """Certify a proposed exceptional point by independent matrix evidence.

    A tiny determinant alone is not a useful certificate for a high-degree
    polynomial.  The returned quantities therefore combine scale-aware
    characteristic backward errors with a direct complex eigensolve.  At an
    exceptional point two eigenvalues coalesce while the eigenvector matrix
    becomes ill-conditioned.
    """

    matrix = dense_complex_sector(particles, coupling, sector)
    matrix_norm = max(float(np.linalg.norm(matrix, ord=2)), 1.0)
    eigenvalues, eigenvectors = np.linalg.eig(matrix)
    nearest = np.argsort(np.abs(eigenvalues - energy))[:2]
    first, second = eigenvalues[nearest]
    center = 0.5 * (first + second)
    determinant, derivative = characteristic_and_energy_derivative(
        particles, sector, energy, coupling
    )
    dimension = matrix.shape[0]
    determinant_scale = matrix_norm**dimension
    derivative_scale = dimension * matrix_norm ** (dimension - 1)
    return {
        "matrix_norm": matrix_norm,
        "relative_eigenvalue_gap": float(abs(first - second) / matrix_norm),
        "relative_energy_center_error": float(abs(center - energy) / matrix_norm),
        "eigenvector_condition_number": float(np.linalg.cond(eigenvectors)),
        "relative_characteristic_backward_error": float(
            abs(determinant) / determinant_scale
        ),
        "relative_derivative_backward_error": float(abs(derivative) / derivative_scale),
    }


def exceptional_point_candidates(
    particles: int,
    *,
    sectors: tuple[int, ...] = (0, 1),
    real_seeds: tuple[float, ...] = (0.6, 0.9, 1.2, 1.5, 1.8),
    imaginary_seeds: tuple[float, ...] = (0.02, 0.08, 0.25, 0.7),
    maximum_real_coupling: float = 3.0,
    residual_tolerance: float = 1.0e-10,
    eigenvalue_gap_tolerance: float = 1.0e-6,
    center_tolerance: float = 1.0e-6,
    minimum_eigenvector_condition: float = 1.0e6,
    duplicate_tolerance: float = 1.0e-5,
) -> list[dict[str, float | int]]:
    """Find finite-N complex-coupling exceptional points.

    Every seed is derived from an adjacent real-axis eigenvalue pair.  The
    nonlinear solve enforces both the characteristic equation and its energy
    derivative.  Results are de-duplicated but failed seeds remain ordinary
    failed searches; no nearest-approach point is promoted to an EP.
    """

    candidates: list[dict[str, float | int]] = []
    for sector in sectors:
        dimension = len(sector_diagonals(particles, 1.0, sector)[0])

        def residual(values: np.ndarray) -> np.ndarray:
            energy = complex(values[0], values[1])
            coupling = complex(values[2], values[3])
            determinant, derivative = characteristic_and_energy_derivative(
                particles, sector, energy, coupling
            )
            matrix = dense_complex_sector(particles, coupling, sector)
            matrix_norm = max(float(np.linalg.norm(matrix, ord=np.inf)), 1.0)
            return np.asarray(
                [
                    determinant.real / matrix_norm**dimension,
                    determinant.imag / matrix_norm**dimension,
                    derivative.real / (dimension * matrix_norm ** (dimension - 1)),
                    derivative.imag / (dimension * matrix_norm ** (dimension - 1)),
                ],
                dtype=float,
            )

        for real_seed in real_seeds:
            real_energies = lmg_sector(particles, real_seed, sector).energies
            for pair_index in range(len(real_energies) - 1):
                energy_seed = float(
                    0.5 * (real_energies[pair_index] + real_energies[pair_index + 1])
                )
                for imaginary_seed in imaginary_seeds:
                    solution = root(
                        residual,
                        [energy_seed, 0.0, real_seed, imaginary_seed],
                        tol=1.0e-10,
                    )
                    if (
                        not solution.success
                        or np.linalg.norm(residual(solution.x)) >= residual_tolerance
                    ):
                        continue
                    energy = complex(solution.x[0], solution.x[1])
                    coupling = complex(solution.x[2], solution.x[3])
                    if coupling.imag < 0.0:
                        coupling = coupling.conjugate()
                        energy = energy.conjugate()
                    if not (
                        coupling.imag > 1.0e-7
                        and 0.0 <= coupling.real <= maximum_real_coupling
                    ):
                        continue
                    if any(
                        int(row["sector"]) == sector
                        and abs(
                            coupling
                            - complex(
                                float(row["coupling_real"]),
                                float(row["coupling_imaginary"]),
                            )
                        )
                        < duplicate_tolerance
                        and abs(
                            energy
                            - complex(
                                float(row["energy_real"]),
                                float(row["energy_imaginary"]),
                            )
                        )
                        < duplicate_tolerance
                        for row in candidates
                    ):
                        continue
                    certificate = exceptional_point_certificate(
                        particles, sector, energy, coupling
                    )
                    if not (
                        certificate["relative_eigenvalue_gap"]
                        < eigenvalue_gap_tolerance
                        and certificate["relative_energy_center_error"]
                        < center_tolerance
                        and certificate["relative_characteristic_backward_error"]
                        < residual_tolerance
                        and certificate["relative_derivative_backward_error"]
                        < residual_tolerance
                        and certificate["eigenvector_condition_number"]
                        > minimum_eigenvector_condition
                    ):
                        continue
                    candidates.append(
                        {
                            "particles": particles,
                            "sector": sector,
                            "coupling_real": float(coupling.real),
                            "coupling_imaginary": float(coupling.imag),
                            "energy_real": float(energy.real),
                            "energy_imaginary": float(energy.imag),
                            "energy_per_particle_real": float(energy.real / particles),
                            **certificate,
                        }
                    )
    return sorted(
        candidates,
        key=lambda row: (
            float(row["coupling_imaginary"]),
            abs(float(row["coupling_real"]) - 1.0),
            int(row["sector"]),
        ),
    )


def separatrix_action(coupling: float) -> float:
    """Return the total two-lobe action of the ``K=-1`` separatrix.

    In the paper's Eq. (16), solving ``K(mu, phi)=-1`` gives the pole
    ``mu=-1`` and ``mu=1+2/(lambda*cos(2 phi))``.  Integrating the enclosed
    canonical area over both symmetry-related lobes evaluates the action used
    by the WKB condition instead of inferring it from a level index.
    """

    if coupling <= 1.0:
        raise ValueError("the deformed-phase separatrix requires coupling > 1")
    lower = 0.5 * np.arccos(-1.0 / coupling)
    upper = np.pi - lower

    def width(phi: float) -> float:
        return 2.0 + 2.0 / (coupling * np.cos(2.0 * phi))

    one_lobe, _ = quad(width, lower, upper, epsabs=1.0e-12, epsrel=1.0e-12)
    return float(2.0 * one_lobe)


def wkb_separatrix_index(particles: int, coupling: float) -> float:
    """Full-spectrum index predicted by the printed WKB condition."""

    return float(particles * separatrix_action(coupling) / (4.0 * np.pi) - 0.5)


def super_scar_record(
    particles: int,
    coupling: float,
    sector: int = 0,
    components: int = 20,
    *,
    local_pair_count: int = 7,
    mass_thresholds: tuple[float, ...] = (0.5, 0.75, 0.9, 0.99),
) -> dict[str, float | int]:
    """Compare the separatrix minimal-gap pair with states outside the pair.

    The publication refers to the *eigenvalues* at the minimal gap.  Treating
    the second member of that pair as an ordinary neighboring state reverses
    the intended test.  We first identify the local minimal-gap pair around
    ``E_c`` and only then compare its mean first-component weight with the two
    states immediately outside the pair.
    """

    spectrum = lmg_sector(particles, coupling, sector, eigenvectors=True)
    assert spectrum.eigenvectors is not None
    gaps = np.diff(spectrum.energies)
    midpoints = 0.5 * (spectrum.energies[:-1] + spectrum.energies[1:])
    nearest = np.argsort(np.abs(midpoints + particles / 2.0))[
        : min(local_pair_count, len(gaps))
    ]
    lower_index = int(nearest[np.argmin(gaps[nearest])])
    upper_index = lower_index + 1

    if not mass_thresholds or any(
        threshold <= 0.0 or threshold >= 1.0 for threshold in mass_thresholds
    ):
        raise ValueError("mass thresholds must lie strictly between zero and one")

    def probabilities(column: int) -> np.ndarray:
        return np.abs(spectrum.eigenvectors[:, column]) ** 2

    def weight(column: int) -> float:
        return float(np.sum(probabilities(column)[:components]))

    def adaptive_widths(column: int) -> dict[str, float | int]:
        cumulative = np.cumsum(probabilities(column))
        output: dict[str, float | int] = {}
        grid_step = (
            2.0 * float(spectrum.m[1] - spectrum.m[0]) / particles
            if len(spectrum.m) > 1
            else 2.0
        )
        for threshold in mass_thresholds:
            count = int(np.searchsorted(cumulative, threshold, side="left") + 1)
            physical_width = count * grid_step
            key = f"mass_{int(round(100 * threshold))}"
            output[f"{key}_component_count"] = count
            output[f"{key}_mu_width"] = physical_width
            output[f"{key}_achieved_mass"] = float(cumulative[count - 1])
        return output

    pair_lower = weight(lower_index)
    pair_upper = weight(upper_index)
    outside_lower = weight(lower_index - 1) if lower_index > 0 else float("nan")
    outside_upper = (
        weight(upper_index + 1)
        if upper_index + 1 < spectrum.eigenvectors.shape[1]
        else float("nan")
    )
    pair_mean = float(np.mean([pair_lower, pair_upper]))
    outside_mean = float(np.nanmean([outside_lower, outside_upper]))
    action = separatrix_action(coupling)
    predicted_index = wkb_separatrix_index(particles, coupling)
    return {
        "particles": particles,
        "coupling": coupling,
        "sector": sector,
        "pair_lower_sector_index": lower_index,
        "pair_upper_sector_index": upper_index,
        "full_spectrum_index_estimate": 2 * lower_index,
        "pair_midpoint_offset": float(midpoints[lower_index] + particles / 2.0),
        "pair_spacing": float(gaps[lower_index]),
        "first_component_count": components,
        "pair_lower_weight": pair_lower,
        "pair_upper_weight": pair_upper,
        "pair_mean_weight": pair_mean,
        "outside_lower_weight": outside_lower,
        "outside_upper_weight": outside_upper,
        "outside_mean_weight": outside_mean,
        "pair_minus_outside_mean": pair_mean - outside_mean,
        "basis_interval_fraction": components / spectrum.eigenvectors.shape[0],
        "fixed_component_mu_width": float(
            min(components, len(spectrum.m))
            * 2.0
            * (spectrum.m[1] - spectrum.m[0])
            / particles
        ),
        "separatrix_action": action,
        "wkb_full_spectrum_index": predicted_index,
        "wkb_index_relative_error": float(
            abs(2 * lower_index - predicted_index) / max(abs(predicted_index), 1.0)
        ),
        **{
            f"pair_lower_{key}": value
            for key, value in adaptive_widths(lower_index).items()
        },
        **{
            f"pair_upper_{key}": value
            for key, value in adaptive_widths(upper_index).items()
        },
    }
