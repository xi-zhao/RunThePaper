"""Open-chain Ising dynamics derived from the equations in the paper.

The scientific path in this module reads no paper files, source figures, author
code, or author arrays.  It implements the printed open-chain Hamiltonian with a
Jordan-Wigner/Majorana covariance solver.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Iterable

import numpy as np
from scipy.integrate import solve_ivp


@dataclass(frozen=True)
class EvolutionResult:
    """Final covariance and numerical diagnostics for one quench."""

    n_spins: int
    rate_tau0_over_tauq: float
    tau_q: float
    covariance: np.ndarray
    nfev: int
    antisymmetry_error: float
    purity_error: float


def _validate_chain(n_spins: int) -> None:
    if n_spins < 2:
        raise ValueError("the open chain requires at least two spins")


def majorana_bands(n_spins: int, field_j: float, coupling_w: float = 1.0) -> np.ndarray:
    """Upper off-diagonal of the real antisymmetric Majorana generator."""

    _validate_chain(n_spins)
    if coupling_w <= 0:
        raise ValueError("coupling_w must be positive for the paper's ferromagnet")
    bands = np.empty(2 * n_spins - 1, dtype=float)
    bands[0::2] = -2.0 * float(field_j)
    bands[1::2] = -2.0 * float(coupling_w)
    return bands


def majorana_generator(
    n_spins: int, field_j: float, coupling_w: float = 1.0
) -> np.ndarray:
    """Return A for H=(i/4) a^T A a in the paper's open chain."""

    bands = majorana_bands(n_spins, field_j, coupling_w)
    size = 2 * n_spins
    generator = np.zeros((size, size), dtype=float)
    indices = np.arange(size - 1)
    generator[indices, indices + 1] = bands
    generator[indices + 1, indices] = -bands
    return generator


def ground_covariance(
    n_spins: int, field_j: float, coupling_w: float = 1.0
) -> np.ndarray:
    """Pure Gaussian ground covariance from the spectral sign of iA.

    This routine is intended for a non-degenerate ground state.  The production
    quench initializes at J/W=5, where the spectral gap is safely nonzero.
    """

    generator = majorana_generator(n_spins, field_j, coupling_w)
    values, vectors = np.linalg.eigh(1j * generator)
    scale = max(1.0, float(np.max(np.abs(values))))
    if float(np.min(np.abs(values))) < 1e-13 * scale:
        raise ValueError("ground covariance is ambiguous at a zero Majorana mode")
    signed = (vectors * np.sign(values)) @ vectors.conj().T
    covariance = np.asarray(np.real_if_close(1j * signed, tol=1000).real, dtype=float)
    return 0.5 * (covariance - covariance.T)


def _banded_commutator(covariance: np.ndarray, bands: np.ndarray) -> np.ndarray:
    """Evaluate A Gamma - Gamma A without dense matrix multiplication."""

    left = np.zeros_like(covariance)
    left[:-1] += bands[:, None] * covariance[1:]
    left[1:] -= bands[:, None] * covariance[:-1]

    right = np.zeros_like(covariance)
    right[:, 1:] += covariance[:, :-1] * bands[None, :]
    right[:, :-1] -= covariance[:, 1:] * bands[None, :]
    return left - right


def evolve_open_chain(
    n_spins: int,
    rate_tau0_over_tauq: float,
    *,
    field_start: float = 5.0,
    field_end: float = 0.0,
    coupling_w: float = 1.0,
    hbar: float = 1.0,
    rtol: float = 2e-6,
    atol: float = 2e-8,
) -> EvolutionResult:
    """Evolve the printed open chain through the linear field quench.

    ``rate_tau0_over_tauq`` is the horizontal variable of Figs. 1-3.  With
    tau_0=hbar/(2W), tau_Q=tau_0/rate and dJ/dt=-W/tau_Q.
    """

    _validate_chain(n_spins)
    rate = float(rate_tau0_over_tauq)
    if rate <= 0:
        raise ValueError("rate_tau0_over_tauq must be positive")
    if field_start <= field_end:
        raise ValueError("the paper's quench requires field_start > field_end")
    if hbar <= 0 or rtol <= 0 or atol <= 0:
        raise ValueError("hbar and ODE tolerances must be positive")

    tau_q = hbar / (2.0 * coupling_w * rate)
    duration = (field_start - field_end) * tau_q / coupling_w
    initial = ground_covariance(n_spins, field_start, coupling_w)
    size = 2 * n_spins

    def rhs(fraction: float, flat_covariance: np.ndarray) -> np.ndarray:
        covariance = flat_covariance.reshape(size, size)
        field = field_start + fraction * (field_end - field_start)
        bands = majorana_bands(n_spins, field, coupling_w)
        return (duration * _banded_commutator(covariance, bands) / hbar).ravel()

    solution = solve_ivp(
        rhs,
        (0.0, 1.0),
        initial.ravel(),
        method="DOP853",
        t_eval=[1.0],
        rtol=rtol,
        atol=atol,
    )
    if not solution.success:
        raise RuntimeError(f"open-chain evolution failed: {solution.message}")

    covariance = solution.y[:, -1].reshape(size, size)
    covariance = 0.5 * (covariance - covariance.T)
    norm = np.sqrt(float(size))
    antisymmetry_error = float(np.linalg.norm(covariance + covariance.T) / norm)
    purity_error = float(np.linalg.norm(covariance @ covariance + np.eye(size)) / norm)
    return EvolutionResult(
        n_spins=n_spins,
        rate_tau0_over_tauq=rate,
        tau_q=tau_q,
        covariance=covariance,
        nfev=int(solution.nfev),
        antisymmetry_error=antisymmetry_error,
        purity_error=purity_error,
    )


def final_mode_pairs(n_spins: int) -> list[tuple[int, int]]:
    """Canonical J=0 modes: even-parity edge mode followed by N-1 bonds."""

    _validate_chain(n_spins)
    pairs = [(0, 2 * n_spins - 1)]
    pairs.extend((2 * site - 1, 2 * site) for site in range(1, n_spins))
    return pairs


def final_target_covariance(n_spins: int) -> np.ndarray:
    """Even cat-state covariance at J=0."""

    target = np.zeros((2 * n_spins, 2 * n_spins), dtype=float)
    for first, second in final_mode_pairs(n_spins):
        target[first, second] = 1.0
        target[second, first] = -1.0
    return target


def _mode_number_moments(
    covariance: np.ndarray, pairs: list[tuple[int, int]]
) -> tuple[float, float]:
    q_mean = np.array([covariance[first, second] for first, second in pairs])
    occupations = 0.5 * (1.0 - q_mean)
    first_moment = float(np.sum(occupations))

    pair_sum = 0.0
    for left in range(len(pairs)):
        a, b = pairs[left]
        for right in range(left + 1, len(pairs)):
            c, d = pairs[right]
            q_product = (
                covariance[a, b] * covariance[c, d]
                - covariance[a, c] * covariance[b, d]
                + covariance[a, d] * covariance[b, c]
            )
            pair_sum += 0.25 * (1.0 - q_mean[left] - q_mean[right] + q_product)
    second_moment = first_moment + 2.0 * pair_sum
    return first_moment, float(second_moment)


def gaussian_fidelity(covariance: np.ndarray, target: np.ndarray) -> float:
    """Squared overlap of two pure, same-parity Gaussian states."""

    size = covariance.shape[0]
    matrix = 0.5 * (np.eye(size) - covariance @ target)
    with np.errstate(all="ignore"):
        sign, log_abs_det = np.linalg.slogdet(matrix)
    if sign == 0 or not np.isfinite(log_abs_det):
        return 0.0
    if sign <= 0 and log_abs_det > -50:
        raise ValueError("Gaussian overlap determinant is not positive")
    fidelity = float(np.exp(0.5 * log_abs_det))
    return float(np.clip(fidelity, 0.0, 1.0))


def final_observables(covariance: np.ndarray) -> dict[str, float]:
    """Kinks, exact fidelity, and the paper's F1/F2 moment bounds."""

    if (
        covariance.ndim != 2
        or covariance.shape[0] != covariance.shape[1]
        or covariance.shape[0] % 2
    ):
        raise ValueError("covariance must be a square even-dimensional matrix")
    n_spins = covariance.shape[0] // 2
    pairs = final_mode_pairs(n_spins)
    bulk_pairs = pairs[1:]
    kink_count = float(sum(0.5 * (1.0 - covariance[a, b]) for a, b in bulk_pairs))
    first_moment, second_moment = _mode_number_moments(covariance, pairs)
    lower_bound = 1.0 - first_moment
    upper_bound = 1.0 - 0.5 * (3.0 * first_moment - second_moment)
    exact_fidelity = gaussian_fidelity(covariance, final_target_covariance(n_spins))
    return {
        "kink_count": kink_count,
        "kink_density_per_spin": kink_count / n_spins,
        "quasiparticle_first_moment": first_moment,
        "quasiparticle_second_moment": second_moment,
        "fidelity_lower_bound": lower_bound,
        "fidelity_upper_bound": upper_bound,
        "fidelity_exact": exact_fidelity,
    }


def kzm_density(rate_tau0_over_tauq: float | np.ndarray) -> float | np.ndarray:
    """Raw Kibble-Zurek density from paper Eq. (10)."""

    return np.sqrt(rate_tau0_over_tauq)


def landau_zener_fidelity(
    n_spins: int,
    tau_q: float | np.ndarray,
    *,
    coefficient_a: float = 2.0 * np.pi**3,
    coupling_w: float = 1.0,
    hbar: float = 1.0,
) -> float | np.ndarray:
    """Paper's finite-size Landau-Zener fidelity ansatz."""

    exponent = -coefficient_a * coupling_w * np.asarray(tau_q) / (hbar * n_spins**2)
    result = 1.0 - np.exp(exponent)
    return float(result) if result.ndim == 0 else result


def low_excitation_spectrum(
    n_spins: int,
    field_values: Iterable[float],
    *,
    coupling_w: float = 1.0,
    max_particles: int = 3,
    max_energy: float = 6.1,
) -> list[dict[str, object]]:
    """Enumerate low many-body energy curves and their fermion parity."""

    fields = np.asarray(list(field_values), dtype=float)
    if fields.ndim != 1 or fields.size == 0:
        raise ValueError("field_values must be a nonempty one-dimensional sequence")
    if max_particles < 0 or max_particles > n_spins:
        raise ValueError("invalid max_particles")

    elementary = []
    for field in fields:
        values = np.linalg.eigvalsh(1j * majorana_generator(n_spins, field, coupling_w))
        elementary.append(np.asarray(values[n_spins:], dtype=float))
    energies = np.stack(elementary, axis=0)

    curves: list[dict[str, object]] = []
    for particle_count in range(max_particles + 1):
        for subset in combinations(range(n_spins), particle_count):
            curve = (
                np.sum(energies[:, subset], axis=1) if subset else np.zeros(fields.size)
            )
            if float(np.min(curve)) > max_energy:
                continue
            curves.append(
                {
                    "subset": subset,
                    "particle_count": particle_count,
                    "parity": (
                        "accessible_even"
                        if particle_count % 2 == 0
                        else "inaccessible_odd"
                    ),
                    "field_values": fields.copy(),
                    "energies": curve,
                }
            )
    return curves


def periodic_mode_observables(
    n_spins: int,
    rate_tau0_over_tauq: float,
    *,
    field_start: float = 5.0,
    field_end: float = 0.0,
    coupling_w: float = 1.0,
    hbar: float = 1.0,
    rtol: float = 1e-9,
    atol: float = 1e-11,
) -> dict[str, float]:
    """Independent periodic-chain momentum-mode cross-check.

    This is deliberately separate from the open-chain production solver and is
    used only for thermodynamic-limit falsification checks.
    """

    if n_spins % 2:
        raise ValueError("periodic even-parity momentum grid requires even N")
    rate = float(rate_tau0_over_tauq)
    tau_q = hbar / (2.0 * coupling_w * rate)
    duration = (field_start - field_end) * tau_q / coupling_w
    momenta = (2 * np.arange(n_spins // 2) + 1) * np.pi / n_spins

    def hamiltonians(field: float) -> np.ndarray:
        result = np.zeros((momenta.size, 2, 2), dtype=complex)
        diagonal = 2.0 * (field - coupling_w * np.cos(momenta))
        off_diagonal = 2.0 * coupling_w * np.sin(momenta)
        result[:, 0, 0] = diagonal
        result[:, 1, 1] = -diagonal
        result[:, 0, 1] = off_diagonal
        result[:, 1, 0] = off_diagonal
        return result

    initial_hamiltonians = hamiltonians(field_start)
    initial_states = np.empty((momenta.size, 2), dtype=complex)
    for index, matrix in enumerate(initial_hamiltonians):
        values, vectors = np.linalg.eigh(matrix)
        initial_states[index] = vectors[:, int(np.argmin(values))]

    def rhs(fraction: float, flat_states: np.ndarray) -> np.ndarray:
        states = flat_states.reshape(momenta.size, 2)
        field = field_start + fraction * (field_end - field_start)
        return (
            -1j * duration / hbar * np.einsum("kij,kj->ki", hamiltonians(field), states)
        ).ravel()

    solution = solve_ivp(
        rhs,
        (0.0, 1.0),
        initial_states.ravel(),
        method="DOP853",
        t_eval=[1.0],
        rtol=rtol,
        atol=atol,
    )
    if not solution.success:
        raise RuntimeError(f"periodic mode evolution failed: {solution.message}")
    final_states = solution.y[:, -1].reshape(momenta.size, 2)
    final_hamiltonians = hamiltonians(field_end)
    probabilities = np.empty(momenta.size, dtype=float)
    for index, matrix in enumerate(final_hamiltonians):
        values, vectors = np.linalg.eigh(matrix)
        excited = vectors[:, int(np.argmax(values))]
        probabilities[index] = float(abs(np.vdot(excited, final_states[index])) ** 2)
    return {
        "kink_density_per_spin": float(2.0 * np.sum(probabilities) / n_spins),
        "fidelity_exact": float(np.prod(1.0 - probabilities)),
        "normalization_error": float(
            np.max(np.abs(np.sum(abs(final_states) ** 2, axis=1) - 1.0))
        ),
        "nfev": int(solution.nfev),
    }
