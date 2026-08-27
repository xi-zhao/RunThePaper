"""Numerical kernels for the full arXiv:2005.12667 reproduction.

The functions in this module implement the discretizations declared in
``EQUATION_CARDS.json``.  Frequencies use one consistent angular-frequency
unit and ``hbar=1`` unless a plotting function explicitly uses GHz/MHz labels.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import factorial

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy.integrate import solve_ivp
from scipy.special import eval_genlaguerre, gammaln

from .cqed_reproduction import annihilation


ComplexArray = NDArray[np.complex128]
RealArray = NDArray[np.float64]


def transmon_charge_hamiltonian(
    charge_cutoff: int,
    charging_energy: float,
    josephson_energy: float,
    offset_charge: float,
) -> ComplexArray:
    """Eq. (20) in the integer Cooper-pair charge basis."""

    if charge_cutoff < 2:
        raise ValueError("charge_cutoff must be at least 2")
    if charging_energy <= 0 or josephson_energy < 0:
        raise ValueError("energies must be nonnegative and EC must be positive")
    charges = np.arange(-charge_cutoff, charge_cutoff + 1, dtype=float)
    hamiltonian = np.diag(4.0 * charging_energy * (charges - offset_charge) ** 2)
    hopping = -0.5 * josephson_energy
    hamiltonian += np.diag(np.full(len(charges) - 1, hopping), 1)
    hamiltonian += np.diag(np.full(len(charges) - 1, hopping), -1)
    return np.asarray(hamiltonian, dtype=np.complex128)


def transmon_eigensystem(
    charge_cutoff: int,
    charging_energy: float,
    josephson_energy: float,
    offset_charge: float,
) -> tuple[RealArray, ComplexArray]:
    """Return ordered transmon energies and charge-basis eigenvectors."""

    return np.linalg.eigh(
        transmon_charge_hamiltonian(
            charge_cutoff, charging_energy, josephson_energy, offset_charge
        )
    )


def transmon_phase_wavefunctions(
    eigenvectors: ComplexArray,
    phase: ArrayLike,
    levels: int,
) -> ComplexArray:
    """Fourier transform charge-basis eigenvectors to compact phase space."""

    phase_values = np.asarray(phase, dtype=float)
    dimension = eigenvectors.shape[0]
    cutoff = (dimension - 1) // 2
    charges = np.arange(-cutoff, cutoff + 1)
    basis = np.exp(1j * np.outer(phase_values, charges)) / np.sqrt(2.0 * np.pi)
    return np.asarray(basis @ eigenvectors[:, :levels], dtype=np.complex128)


def cpw_transmission(
    frequency: ArrayLike,
    fundamental: float = 10.0,
    quality_factor: float = 400.0,
    mode_count: int = 3,
) -> RealArray:
    """Separated passive Lorentzian CPW resonances used for Fig. 2(c)."""

    values = np.asarray(frequency, dtype=float)
    response = np.zeros_like(values)
    for mode in range(1, mode_count + 1):
        resonance = mode * fundamental
        linewidth = resonance / quality_factor
        response = np.maximum(
            response,
            1.0 / np.sqrt(1.0 + (2.0 * (values - resonance) / linewidth) ** 2),
        )
    return response


def dispersive_pointer_trajectory(
    time: ArrayLike,
    kappa: float,
    chi: float,
    drive: float,
    cavity_detuning: float = 0.0,
) -> tuple[ComplexArray, ComplexArray]:
    """Eqs. (109)-(110) for vacuum initial pointer states."""

    times = np.asarray(time, dtype=float)

    def branch(sign: float) -> ComplexArray:
        rate = 0.5 * kappa + 1j * (cavity_detuning + sign * chi)
        steady = -1j * drive / rate
        return np.asarray(steady * (1.0 - np.exp(-rate * times)), dtype=np.complex128)

    return branch(-1.0), branch(1.0)


def integrated_pointer_snr(
    time: ArrayLike,
    alpha_g: ArrayLike,
    alpha_e: ArrayLike,
    kappa: float,
    efficiency: float = 1.0,
) -> float:
    """Matched-filter SNR from the finite-time pointer-state separation."""

    times = np.asarray(time, dtype=float)
    separation = np.abs(np.asarray(alpha_e) - np.asarray(alpha_g)) ** 2
    return float(np.sqrt(2.0 * efficiency * kappa * np.trapezoid(separation, times)))


def dispersive_steady_response(
    detuning: ArrayLike, kappa: float, chi: float, drive: float = 1.0
) -> tuple[ComplexArray, ComplexArray]:
    """Eq. (110) evaluated for both qubit states."""

    values = np.asarray(detuning, dtype=float)
    alpha_g = -1j * drive / (0.5 * kappa + 1j * (values - chi))
    alpha_e = -1j * drive / (0.5 * kappa + 1j * (values + chi))
    return np.asarray(alpha_g), np.asarray(alpha_e)


def phase_preserving_amplifier_metrics(
    gain: float, input_variance: float = 0.5, idler_variance: float = 0.5
) -> dict[str, float]:
    """Eqs. (88)-(92): commutator and input-referred added noise."""

    if gain < 1.0:
        raise ValueError("phase-preserving power gain must be at least one")
    output_variance = gain * input_variance + (gain - 1.0) * idler_variance
    return {
        "output_commutator": gain - (gain - 1.0),
        "output_variance": output_variance,
        "input_referred_added_noise": output_variance / gain - input_variance,
        "quantum_efficiency": 1.0 / (1.0 + 2.0 * (output_variance / gain - input_variance)),
    }


def linear_cqed_response(
    probe_detuning: ArrayLike,
    qubit_cavity_detuning: ArrayLike | float,
    coupling: float,
    kappa: float,
    gamma2: float,
    drive: float = 1.0,
) -> ComplexArray:
    """Eq. (124) weak-drive cavity amplitude.

    ``probe_detuning`` is ``omega_r-omega_d`` and
    ``qubit_cavity_detuning`` is ``omega_q-omega_r``.
    """

    delta_r = np.asarray(probe_detuning, dtype=float)
    delta_q = delta_r + np.asarray(qubit_cavity_detuning, dtype=float)
    denominator = 1j * delta_r + 0.5 * kappa + coupling**2 / (1j * delta_q + gamma2)
    return np.asarray(-1j * drive / denominator, dtype=np.complex128)


def one_excitation_dynamics(
    time: ArrayLike,
    coupling: float,
    kappa: float,
    gamma1: float,
    initial: str,
) -> tuple[RealArray, RealArray]:
    """Exact resonant one-excitation populations including irreversible loss."""

    if initial not in {"qubit", "cavity"}:
        raise ValueError("initial must be 'qubit' or 'cavity'")
    times = np.asarray(time, dtype=float)
    matrix = np.array(
        [[-0.5 * gamma1, -1j * coupling], [-1j * coupling, -0.5 * kappa]],
        dtype=np.complex128,
    )
    initial_state = np.array([1.0, 0.0], dtype=np.complex128)
    if initial == "cavity":
        initial_state = initial_state[::-1]
    eigenvalues, eigenvectors = np.linalg.eig(matrix)
    coefficients = np.linalg.solve(eigenvectors, initial_state)
    amplitudes = np.asarray(
        [eigenvectors @ (np.exp(eigenvalues * t) * coefficients) for t in times]
    )
    return np.abs(amplitudes[:, 0]) ** 2, np.abs(amplitudes[:, 1]) ** 2


def thermal_jc_spectrum(
    probe_detuning: ArrayLike,
    coupling: float,
    linewidth: float,
    thermal_occupation: float,
    maximum_manifold: int = 5,
) -> RealArray:
    """Resolved JC transition model showing thermally activated inner peaks."""

    detuning = np.asarray(probe_detuning, dtype=float)
    spectrum = np.zeros_like(detuning)
    thermal_ratio = thermal_occupation / (1.0 + thermal_occupation)
    weights = np.asarray([(1.0 - thermal_ratio) * thermal_ratio**n for n in range(maximum_manifold)])
    weights /= np.sum(weights)

    def lorentz(center: float, width: float) -> RealArray:
        return 1.0 / (1.0 + (2.0 * (detuning - center) / width) ** 2)

    spectrum += 0.5 * weights[0] * (lorentz(-coupling, linewidth) + lorentz(coupling, linewidth))
    for n in range(1, maximum_manifold):
        inner = coupling * (np.sqrt(n + 1.0) - np.sqrt(float(n)))
        spectrum += 0.5 * weights[n] * (lorentz(-inner, linewidth) + lorentz(inner, linewidth))
    peak = float(np.max(spectrum))
    return spectrum / peak if peak > 0 else spectrum


def bloch_excited_population(
    detuning: ArrayLike,
    rabi_frequency: float,
    gamma1: float,
    gamma2: float,
) -> RealArray:
    """Eq. (127): steady-state excited population."""

    delta = np.asarray(detuning, dtype=float)
    numerator = 0.5 * rabi_frequency**2
    denominator = gamma1 * gamma2 + delta**2 * gamma1 / gamma2 + rabi_frequency**2
    return np.asarray(numerator / denominator, dtype=float)


def photon_number_split_spectrum(
    detuning: ArrayLike,
    chi: float,
    rabi_frequency: float,
    gamma1: float,
    gamma_phi: float,
    kappa: float,
    mean_photons: float,
    maximum_photon: int = 30,
) -> RealArray:
    """Poisson-weighted number-conditioned qubit spectrum."""

    delta = np.asarray(detuning, dtype=float)
    weights = np.asarray(
        [np.exp(-mean_photons) * mean_photons**n / factorial(n) for n in range(maximum_photon + 1)]
    )
    weights /= np.sum(weights)
    population = np.zeros_like(delta)
    for n, weight in enumerate(weights):
        gamma2 = 0.5 * gamma1 + gamma_phi + 0.5 * (mean_photons + n) * kappa
        population += weight * bloch_excited_population(
            delta - 2.0 * chi * n, rabi_frequency, gamma1, gamma2
        )
    return population


def duffing_cavity_pull(
    cavity_dimension: int,
    transmon_dimension: int,
    omega_r: float,
    omega_q: float,
    coupling: float,
    anharmonicity: float,
    maximum_photon: int,
) -> dict[int, RealArray]:
    """Photon-number-dependent cavity frequency from exact dressed energies."""

    del cavity_dimension  # Total-excitation blocks avoid an unnecessary tensor cutoff.

    def labelled_block(total_excitation: int) -> dict[int, float]:
        maximum_level = min(total_excitation, transmon_dimension - 1)
        levels = np.arange(maximum_level + 1)
        photons = total_excitation - levels
        block = np.diag(
            photons * omega_r
            + levels * omega_q
            - 0.5 * anharmonicity * levels * (levels - 1)
        ).astype(np.complex128)
        for level in range(maximum_level):
            matrix_element = coupling * np.sqrt(photons[level]) * np.sqrt(level + 1.0)
            block[level, level + 1] = matrix_element
            block[level + 1, level] = matrix_element
        eigenvalues, eigenvectors = np.linalg.eigh(block)
        probabilities = np.abs(eigenvectors) ** 2
        from scipy.optimize import linear_sum_assignment

        bare_indices, eigen_indices = linear_sum_assignment(-probabilities)
        return {int(bare): float(eigenvalues[eigen]) for bare, eigen in zip(bare_indices, eigen_indices, strict=True)}

    blocks = {
        total: labelled_block(total)
        for total in range(maximum_photon + min(3, transmon_dimension) + 1)
    }
    result: dict[int, RealArray] = {}
    for level in range(min(3, transmon_dimension)):
        spacings = []
        for photon in range(maximum_photon + 1):
            lower_total = photon + level
            upper_total = photon + level + 1
            spacings.append(blocks[upper_total][level] - blocks[lower_total][level])
        result[level] = np.asarray(spacings)
    return result


@dataclass(frozen=True)
class DragResult:
    final_state: ComplexArray
    leakage: float
    target_population: float
    norm_error: float


def drag_pi_pulse(
    gate_time: float,
    anharmonicity: float,
    use_drag: bool,
    dimension: int = 3,
    time_steps: int = 501,
) -> DragResult:
    """Propagate a resonant Gaussian pi pulse with optional first-order DRAG."""

    if gate_time <= 0 or anharmonicity <= 0 or dimension < 2:
        raise ValueError("gate_time, anharmonicity, and dimension are invalid")
    if use_drag and dimension < 3:
        raise ValueError("DRAG requires at least three levels")
    b = annihilation(dimension)
    number = b.conj().T @ b
    quartic = b.conj().T @ b.conj().T @ b @ b
    sigma = gate_time / 4.0
    center = gate_time / 2.0
    edge = np.exp(-0.5 * (center / sigma) ** 2)

    grid = np.linspace(0.0, gate_time, 4001)
    raw = np.exp(-0.5 * ((grid - center) / sigma) ** 2) - edge
    amplitude = np.pi / np.trapezoid(raw, grid)

    def pulse(t: float) -> tuple[float, float, float]:
        gaussian = np.exp(-0.5 * ((t - center) / sigma) ** 2)
        omega_x = amplitude * (gaussian - edge)
        derivative = -amplitude * (t - center) * gaussian / sigma**2
        omega_y = derivative / anharmonicity if use_drag else 0.0
        detuning = -(omega_x**2) / (4.0 * anharmonicity) if use_drag else 0.0
        return omega_x, omega_y, detuning

    def rhs(t: float, state: ComplexArray) -> ComplexArray:
        omega_x, omega_y, detuning = pulse(t)
        hamiltonian = (
            -detuning * number
            - 0.5 * anharmonicity * quartic
            + 0.5 * omega_x * (b + b.conj().T)
            - 0.5j * omega_y * (b - b.conj().T)
        )
        return np.asarray(-1j * hamiltonian @ state, dtype=np.complex128)

    initial = np.zeros(dimension, dtype=np.complex128)
    initial[0] = 1.0
    times = np.linspace(0.0, gate_time, time_steps)
    solution = solve_ivp(
        rhs,
        (0.0, gate_time),
        initial,
        t_eval=times,
        rtol=2e-9,
        atol=2e-11,
    )
    final = solution.y[:, -1]
    probabilities = np.abs(final) ** 2
    return DragResult(
        final_state=final,
        leakage=float(np.sum(probabilities[2:])),
        target_population=float(probabilities[1]),
        norm_error=float(abs(np.sum(probabilities) - 1.0)),
    )


def coherent_coefficients(alpha: complex, dimension: int) -> ComplexArray:
    """Normalized coherent state in a finite Fock basis."""

    if dimension < 1:
        raise ValueError("dimension must be positive")
    if alpha == 0:
        vacuum = np.zeros(dimension, dtype=np.complex128)
        vacuum[0] = 1.0
        return vacuum
    indices = np.arange(dimension)
    log_factorial = gammaln(indices + 1.0)
    coefficients = np.exp(-0.5 * abs(alpha) ** 2 + indices * np.log(alpha + 0j) - 0.5 * log_factorial)
    norm = np.linalg.norm(coefficients)
    return np.asarray(coefficients / norm, dtype=np.complex128)


def normalize_state(coefficients: ArrayLike) -> ComplexArray:
    state = np.asarray(coefficients, dtype=np.complex128)
    norm = np.linalg.norm(state)
    if norm == 0:
        raise ValueError("state cannot be zero")
    return state / norm


def fock_state_wigner(
    coefficients: ArrayLike, x: ArrayLike, p: ArrayLike
) -> RealArray:
    """Analytic Wigner function for a pure finite Fock superposition.

    The returned density uses ``alpha=(x+ip)/sqrt(2)`` and integrates to one
    over ``dx dp``.  Vacuum is ``exp(-x^2-p^2)/pi``.
    """

    state = normalize_state(coefficients)
    x_values = np.asarray(x, dtype=float)
    p_values = np.asarray(p, dtype=float)
    xx, pp = np.meshgrid(x_values, p_values)
    alpha = (xx + 1j * pp) / np.sqrt(2.0)
    radius = np.abs(alpha) ** 2
    envelope = np.exp(-2.0 * radius) / np.pi
    wigner = np.zeros_like(radius, dtype=np.complex128)
    dimension = len(state)
    for n in range(dimension):
        wigner += (
            abs(state[n]) ** 2
            * (-1) ** n
            * eval_genlaguerre(n, 0, 4.0 * radius)
        )
        for m in range(n + 1, dimension):
            prefactor = (-1) ** n * np.sqrt(np.exp(gammaln(n + 1) - gammaln(m + 1)))
            kernel = (
                prefactor
                * (2.0 * alpha) ** (m - n)
                * eval_genlaguerre(n, m - n, 4.0 * radius)
            )
            wigner += 2.0 * np.real(np.conj(state[n]) * state[m] * kernel)
    return np.asarray(envelope * np.real(wigner), dtype=float)


def cat_state_coefficients(
    alpha: complex, dimension: int, components: int
) -> ComplexArray:
    """Four- or two-component even cat codeword used in Fig. 31."""

    if components == 4:
        phases = [1.0, 1.0j, -1.0, -1.0j]
    elif components == 2:
        phases = [1.0, -1.0]
    else:
        raise ValueError("components must be 2 or 4")
    state = sum(coherent_coefficients(alpha * phase, dimension) for phase in phases)
    return normalize_state(state)


def squeezed_vacuum_wigner(
    x: ArrayLike, p: ArrayLike, squeezing: float, angle: float
) -> RealArray:
    """Exact Gaussian Wigner function for a pure squeezed vacuum."""

    x_values = np.asarray(x, dtype=float)
    p_values = np.asarray(p, dtype=float)
    xx, pp = np.meshgrid(x_values, p_values)
    rotation = np.array(
        [[np.cos(angle / 2.0), -np.sin(angle / 2.0)],
         [np.sin(angle / 2.0), np.cos(angle / 2.0)]]
    )
    covariance = rotation @ np.diag(
        [0.5 * np.exp(-2.0 * squeezing), 0.5 * np.exp(2.0 * squeezing)]
    ) @ rotation.T
    inverse = np.linalg.inv(covariance)
    quadratic = inverse[0, 0] * xx**2 + 2.0 * inverse[0, 1] * xx * pp + inverse[1, 1] * pp**2
    return np.asarray(
        np.exp(-0.5 * quadratic) / (2.0 * np.pi * np.sqrt(np.linalg.det(covariance))),
        dtype=float,
    )


def squeezed_quadrature_variance(
    phase: ArrayLike, squeezing: float, angle: float
) -> RealArray:
    """Review expression for squeezed-state quadrature variance."""

    shifted = np.asarray(phase, dtype=float) - angle / 2.0
    return 0.5 * (
        np.exp(2.0 * squeezing) * np.sin(shifted) ** 2
        + np.exp(-2.0 * squeezing) * np.cos(shifted) ** 2
    )


def binomial_code_metrics() -> dict[str, float]:
    """First-order amplitude-damping checks for Eq. (154)."""

    dimension = 5
    zero = np.zeros(dimension, dtype=np.complex128)
    zero[[0, 4]] = 1.0 / np.sqrt(2.0)
    one = np.zeros(dimension, dtype=np.complex128)
    one[2] = 1.0
    code = np.column_stack([zero, one])
    a = annihilation(dimension)
    number = a.conj().T @ a
    gram_identity = code.conj().T @ code
    gram_number = code.conj().T @ number @ code
    gram_loss = code.conj().T @ a @ code
    loss_states = a @ code
    loss_gram = loss_states.conj().T @ loss_states
    return {
        "identity_residual": float(np.linalg.norm(gram_identity - np.eye(2))),
        "equal_loss_residual": float(np.linalg.norm(gram_number - 2.0 * np.eye(2))),
        "logical_loss_residual": float(np.linalg.norm(gram_loss)),
        "normalized_loss_orthogonality": float(
            abs(loss_gram[0, 1]) / np.sqrt(loss_gram[0, 0].real * loss_gram[1, 1].real)
        ),
        "mean_excitation_zero": float(gram_number[0, 0].real),
        "mean_excitation_one": float(gram_number[1, 1].real),
    }
