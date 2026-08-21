"""Clean-room numerical forms of the equations in arXiv:cond-mat/0509490.

The module contains no paper pixels, digitized curves, author arrays, or author
implementation.  Every routine follows a printed equation or an independently
derived equivalent form documented in ``EQUATION_CARDS.json``.
"""

from __future__ import annotations

import math

import numpy as np
from scipy.integrate import solve_ivp


def positive_momenta(chain_length: int, lattice_spacing: float = 1.0) -> np.ndarray:
    """Positive antiperiodic momenta, Eq. (10), for an even periodic chain."""

    if chain_length <= 0 or chain_length % 2:
        raise ValueError("chain_length must be a positive even integer")
    indices = np.arange(chain_length // 2, dtype=float)
    return (2.0 * indices + 1.0) * math.pi / (chain_length * lattice_spacing)


def dispersion(
    momentum: np.ndarray | float,
    field: float,
    coupling_j: float = 1.0,
    lattice_spacing: float = 1.0,
) -> np.ndarray:
    """Positive Bogoliubov dispersion printed below Eq. (12)."""

    k = np.asarray(momentum, dtype=float) * lattice_spacing
    return 2.0 * coupling_j * np.sqrt(
        (field - np.cos(k)) ** 2 + np.sin(k) ** 2
    )


def landau_zener_probability(
    momentum: np.ndarray | float,
    quench_time: float,
    coupling_j: float = 1.0,
    hbar: float = 1.0,
    lattice_spacing: float = 1.0,
    *,
    long_wavelength: bool = False,
) -> np.ndarray:
    """Pair-excitation probability from Eq. (23).

    ``long_wavelength=False`` keeps ``sin(ka)^2`` from the mapped LZ problem.
    ``long_wavelength=True`` evaluates the second, Gaussian approximation in
    Eq. (23), which is the form used in the density and finite-size derivations.
    """

    if quench_time < 0.0:
        raise ValueError("quench_time must be nonnegative")
    ka = np.asarray(momentum, dtype=float) * lattice_spacing
    wave_factor = ka**2 if long_wavelength else np.sin(ka) ** 2
    exponent = -2.0 * math.pi * coupling_j * quench_time * wave_factor / hbar
    return np.exp(exponent)


def asymptotic_defect_density(
    quench_time: np.ndarray | float,
    coupling_j: float = 1.0,
    hbar: float = 1.0,
) -> np.ndarray:
    """Thermodynamic slow-quench density, Eq. (25)."""

    tau = np.asarray(quench_time, dtype=float)
    if np.any(tau <= 0.0):
        raise ValueError("quench_time must be positive")
    return 1.0 / (2.0 * math.pi * np.sqrt(2.0 * coupling_j * tau / hbar))


def finite_chain_defect_density(
    chain_length: int,
    quench_time: float,
    coupling_j: float = 1.0,
    hbar: float = 1.0,
    lattice_spacing: float = 1.0,
) -> float:
    """Finite-N evaluation of Eqs. (24)-(25) using the Gaussian LZ regime."""

    k = positive_momenta(chain_length, lattice_spacing)
    pair_probabilities = landau_zener_probability(
        k,
        quench_time,
        coupling_j,
        hbar,
        lattice_spacing,
        long_wavelength=True,
    )
    return float(2.0 * np.sum(pair_probabilities) / chain_length)


def ground_state_probability(
    chain_length: int,
    quench_time: float,
    coupling_j: float = 1.0,
    hbar: float = 1.0,
    lattice_spacing: float = 1.0,
) -> float:
    """Finite-chain ground-state probability, Eq. (26)."""

    k = positive_momenta(chain_length, lattice_spacing)
    p = landau_zener_probability(
        k,
        quench_time,
        coupling_j,
        hbar,
        lattice_spacing,
        long_wavelength=True,
    )
    # log1p keeps the adiabatic product stable when p is tiny.
    return float(np.exp(np.sum(np.log1p(-np.clip(p, 0.0, 1.0 - 1e-16)))))


def _bdg_hamiltonian(
    field: float,
    momentum: float,
    coupling_j: float,
    lattice_spacing: float,
) -> np.ndarray:
    ka = momentum * lattice_spacing
    diagonal = 2.0 * coupling_j * (field - math.cos(ka))
    off_diagonal = 2.0 * coupling_j * math.sin(ka)
    return np.array(
        [[diagonal, off_diagonal], [off_diagonal, -diagonal]],
        dtype=np.complex128,
    )


def bdg_sweep_excitation_probability(
    momentum: float,
    quench_time: float,
    *,
    field_start: float,
    field_end: float,
    coupling_j: float = 1.0,
    hbar: float = 1.0,
    lattice_spacing: float = 1.0,
    rtol: float = 2e-10,
    atol: float = 2e-12,
) -> tuple[float, float]:
    """Integrate the printed BdG equation for either linear sweep direction.

    The physical ramp has ``|dg/dt| = 1/tau_Q``.  With ``g`` as the independent
    variable,

    ``d psi / dg = -i sign(field_end-field_start) tau_Q H(g) psi / hbar``.

    Starting from the positive-energy instantaneous mode, the function projects
    onto the negative-energy mode at the opposite endpoint.  Thus the same core
    routine implements both the paramagnet-to-ferromagnet and reverse quench;
    neither direction can be replaced by a copied analytic array.
    """

    if quench_time <= 0.0:
        raise ValueError("quench_time must be positive")
    if field_start == field_end:
        raise ValueError("field_start and field_end must differ")

    initial_h = _bdg_hamiltonian(
        field_start, momentum, coupling_j, lattice_spacing
    )
    _, initial_vectors = np.linalg.eigh(initial_h)
    psi0 = initial_vectors[:, 1].astype(np.complex128)  # positive-energy mode

    sweep_sign = math.copysign(1.0, field_end - field_start)

    def rhs(field: float, state: np.ndarray) -> np.ndarray:
        return (
            -1j
            * sweep_sign
            * quench_time
            * _bdg_hamiltonian(field, momentum, coupling_j, lattice_spacing)
            @ state
            / hbar
        )

    solution = solve_ivp(
        rhs,
        (field_start, field_end),
        psi0,
        method="DOP853",
        rtol=rtol,
        atol=atol,
    )
    if not solution.success:
        raise RuntimeError(solution.message)
    final_state = solution.y[:, -1]
    final_h = _bdg_hamiltonian(field_end, momentum, coupling_j, lattice_spacing)
    _, final_vectors = np.linalg.eigh(final_h)
    negative_mode = final_vectors[:, 0]
    probability = float(abs(np.vdot(negative_mode, final_state)) ** 2)
    norm = float(np.vdot(final_state, final_state).real)
    return probability, norm


def bdg_excitation_probability(
    momentum: float,
    quench_time: float,
    *,
    field_initial: float = 8.0,
    coupling_j: float = 1.0,
    hbar: float = 1.0,
    lattice_spacing: float = 1.0,
    rtol: float = 2e-10,
    atol: float = 2e-12,
) -> tuple[float, float]:
    """Integrate the paramagnet-to-ferromagnet sweep from ``g>>1`` to zero."""

    if field_initial <= 1.0:
        raise ValueError("field_initial must begin in the paramagnetic phase")
    return bdg_sweep_excitation_probability(
        momentum,
        quench_time,
        field_start=field_initial,
        field_end=0.0,
        coupling_j=coupling_j,
        hbar=hbar,
        lattice_spacing=lattice_spacing,
        rtol=rtol,
        atol=atol,
    )


def reverse_bdg_excitation_probability(
    momentum: float,
    quench_time: float,
    *,
    field_final: float = 8.0,
    coupling_j: float = 1.0,
    hbar: float = 1.0,
    lattice_spacing: float = 1.0,
    rtol: float = 2e-10,
    atol: float = 2e-12,
) -> tuple[float, float]:
    """Integrate Eqs. (28)-(29) from the ferromagnet to ``g>>1``."""

    if field_final <= 1.0:
        raise ValueError("field_final must end in the paramagnetic phase")
    return bdg_sweep_excitation_probability(
        momentum,
        quench_time,
        field_start=0.0,
        field_end=field_final,
        coupling_j=coupling_j,
        hbar=hbar,
        lattice_spacing=lattice_spacing,
        rtol=rtol,
        atol=atol,
    )
