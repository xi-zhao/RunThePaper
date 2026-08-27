from __future__ import annotations

from dataclasses import dataclass
from math import erf, factorial, pi, sqrt

import numpy as np
from numpy.typing import NDArray

from .cqed_reproduction import (
    generic_multilevel_shifts,
)
from .full_rmp_reproduction import (
    coherent_coefficients,
    dispersive_pointer_trajectory,
    fock_state_wigner,
    one_excitation_dynamics,
    phase_preserving_amplifier_metrics,
    photon_number_split_spectrum,
)


RealArray = NDArray[np.float64]
ComplexArray = NDArray[np.complex128]


@dataclass(frozen=True)
class GaussianMarginals:
    x: RealArray
    ground: RealArray
    excited: RealArray
    overlap_area: float
    assignment_error: float


def lc_harmonic_reference(x: RealArray, omega: float = 1.0) -> tuple[RealArray, RealArray]:
    potential = 0.5 * omega**2 * x**2
    energies = omega * (np.arange(5, dtype=float) + 0.5)
    return potential, energies


def normalized_damped_response(detuning_over_kappa: RealArray) -> RealArray:
    detuning = np.asarray(detuning_over_kappa, dtype=float)
    return np.asarray(1.0 / np.sqrt(1.0 + 4.0 * detuning**2), dtype=float)


def quadrature_marginals(
    two_chi_over_kappa: float,
    integration_time: float,
    points: int = 1201,
) -> GaussianMarginals:
    kappa = 1.0
    chi = 0.5 * two_chi_over_kappa * kappa
    drive = sqrt(chi**2 + (kappa / 2.0) ** 2)
    times = np.linspace(0.0, integration_time, points)
    alpha_g, alpha_e = dispersive_pointer_trajectory(times, kappa, chi, drive)
    mu_g = sqrt(2.0) * alpha_g[-1].real
    mu_e = sqrt(2.0) * alpha_e[-1].real
    sigma = sqrt(0.5)
    x = np.linspace(min(mu_g, mu_e) - 6.0 * sigma, max(mu_g, mu_e) + 6.0 * sigma, 801)
    prefactor = 1.0 / sqrt(pi)
    ground = prefactor * np.exp(-(x - mu_g) ** 2)
    excited = prefactor * np.exp(-(x - mu_e) ** 2)
    overlap = float(np.trapezoid(np.minimum(ground, excited), x))
    separation = abs(mu_e - mu_g)
    assignment_error = 0.5 * (1.0 - erf(separation / (2.0 * sigma)))
    return GaussianMarginals(
        x=x,
        ground=ground,
        excited=excited,
        overlap_area=overlap,
        assignment_error=assignment_error,
    )


def transmon_harmonic_comparator(
    phase: RealArray,
    ej_over_ec: float,
    charging_energy: float = 1.0,
) -> tuple[RealArray, RealArray]:
    josephson_energy = ej_over_ec * charging_energy
    cosine = -josephson_energy * np.cos(phase)
    harmonic = -josephson_energy + 0.5 * josephson_energy * phase**2
    return cosine, harmonic


def low_damping_exchange(
    coupling: float,
    kappa: float,
    gamma1: float,
    time_stop: float,
    points: int = 1001,
) -> tuple[RealArray, RealArray, RealArray, RealArray, RealArray]:
    time = np.linspace(0.0, time_stop, points)
    q_from_q, c_from_q = one_excitation_dynamics(time, coupling, kappa, gamma1, "qubit")
    q_from_c, c_from_c = one_excitation_dynamics(time, coupling, kappa, gamma1, "cavity")
    return time, q_from_q, c_from_q, q_from_c, c_from_c


def epsilon_driven_strong_dispersive(
    detuning: RealArray,
    *,
    chi: float,
    rabi_frequency: float,
    gamma1: float,
    gamma_phi: float,
    kappa: float,
    epsilon: float,
    cavity_drive_detuning: float,
) -> tuple[RealArray, float]:
    """Return the number-split spectrum for a declared cavity-drive detuning.

    ``cavity_drive_detuning`` is measured from the pulled cavity resonance.
    Keeping it explicit prevents the previous bug where ``chi`` was silently
    used as the detuning even for Fig. 25(b), whose caption places the drive on
    the pulled resonance.
    """

    if kappa <= 0:
        raise ValueError("kappa must be positive")
    mean_photons = epsilon**2 / (
        cavity_drive_detuning**2 + (kappa / 2.0) ** 2
    )
    spectrum = photon_number_split_spectrum(
        detuning,
        chi,
        rabi_frequency,
        gamma1,
        gamma_phi,
        kappa,
        mean_photons,
    )
    return spectrum, float(mean_photons)


def small_matrix_multilevel_shift_check() -> dict[str, float]:
    omega_r = 5.0
    levels = np.array([0.0, 7.0, 13.2], dtype=float)
    couplings = np.zeros((3, 3), dtype=np.complex128)
    couplings[0, 1] = couplings[1, 0] = 0.08
    couplings[1, 2] = couplings[2, 1] = 0.11
    lamb, chi = generic_multilevel_shifts(levels, couplings, omega_r)

    cavity_dimension = 4
    atom_dimension = len(levels)
    h = np.zeros((cavity_dimension * atom_dimension, cavity_dimension * atom_dimension), dtype=np.complex128)

    def basis_index(photon: int, level: int) -> int:
        return photon * atom_dimension + level

    for photon in range(cavity_dimension):
        for level in range(atom_dimension):
            h[basis_index(photon, level), basis_index(photon, level)] = photon * omega_r + levels[level]
        for level in range(atom_dimension - 1):
            coupling = couplings[level, level + 1]
            if photon + 1 >= cavity_dimension or coupling == 0.0:
                continue
            strength = coupling * sqrt(photon + 1.0)
            left = basis_index(photon + 1, level)
            right = basis_index(photon, level + 1)
            h[left, right] = strength
            h[right, left] = np.conjugate(strength)

    eigenvalues, eigenvectors = np.linalg.eigh(h)
    assigned: dict[tuple[int, int], float] = {}
    for photon in range(cavity_dimension):
        for level in range(atom_dimension):
            bare = np.zeros(cavity_dimension * atom_dimension)
            bare[basis_index(photon, level)] = 1.0
            weights = np.abs(eigenvectors.conj().T @ bare) ** 2
            assigned[(photon, level)] = float(eigenvalues[int(np.argmax(weights))])

    spacing_errors = []
    for level in range(atom_dimension):
        exact_spacing = assigned[(1, level)] - assigned[(0, level)]
        predicted_spacing = omega_r + chi[level]
        spacing_errors.append(abs(exact_spacing - predicted_spacing))
    return {
        "max_spacing_error": float(max(spacing_errors)),
        "max_lamb_magnitude": float(np.max(np.abs(lamb))),
        "max_chi_magnitude": float(np.max(np.abs(chi))),
    }


def finite_line_mode_checks(mode_count: int = 6, grid_points: int = 4001) -> dict[str, float]:
    x = np.linspace(0.0, 1.0, grid_points)
    modes = [
        sqrt(2.0) * np.sin((index + 1) * pi * x)
        for index in range(mode_count)
    ]
    derivatives = [
        sqrt(2.0) * (index + 1) * pi * np.cos((index + 1) * pi * x)
        for index in range(mode_count)
    ]
    gram = np.array(
        [
            [np.trapezoid(left * right, x) for right in modes]
            for left in modes
        ]
    )
    orth_error = float(np.max(np.abs(gram - np.eye(mode_count))))

    kernel = sum(np.outer(mode, mode) for mode in modes) / mode_count
    completeness_trace = float(np.mean(np.diag(kernel)))

    end_current = max(abs(derivative[0]) for derivative in derivatives)
    magnetic_energy = [
        float(np.trapezoid(derivative**2, x) / ((index + 1) * pi) ** 2)
        for index, derivative in enumerate(derivatives)
    ]
    electric_energy = [
        float(np.trapezoid(mode**2, x))
        for mode in modes
    ]
    energy_balance_error = float(
        max(abs(electric - magnetic) for electric, magnetic in zip(electric_energy, magnetic_energy, strict=True))
    )
    return {
        "orthonormality_error": orth_error,
        "completeness_trace": completeness_trace,
        "boundary_current_magnitude": end_current,
        "energy_balance_error": energy_balance_error,
    }


def gaussian_wavepacket_time_mode_checks(
    omega0: float = 25.0,
    sigma: float = 4.0,
) -> dict[str, float]:
    omega = np.linspace(max(1e-3, omega0 - 8.0 * sigma), omega0 + 8.0 * sigma, 8001)
    envelope = np.exp(-0.5 * ((omega - omega0) / sigma) ** 2)
    norm = sqrt(np.trapezoid(np.abs(envelope) ** 2, omega))
    envelope /= norm

    def overlap(delay: float) -> complex:
        shifted = envelope * np.exp(-1j * omega * delay)
        return complex(np.trapezoid(np.conjugate(envelope) * shifted, omega))

    zero = abs(overlap(0.0))
    moderate = abs(overlap(2.0 / sigma))
    far = abs(overlap(4.0 / sigma))
    return {
        "overlap_zero_delay": float(zero),
        "overlap_two_sigma_delay": float(moderate),
        "overlap_four_sigma_delay": float(far),
    }


def rectangular_te_mode_features(
    modes: tuple[tuple[int, int, int], ...] = (
        (1, 1, 0),
        (2, 1, 0),
        (1, 2, 0),
        (2, 2, 0),
    ),
    points: int = 121,
) -> dict[str, object]:
    """Solve normalized ideal-rectangular-cavity TE mode patterns.

    The paper's Fig. 4(b-e) COMSOL project is not published.  This clean-room
    calculation therefore reproduces the equation-defined nodal topology on a
    unit rectangle, without pretending to recover the unpublished chip,
    connector, material, or mesh realization.  A finite-difference Helmholtz
    residual and the numerical mode Gram matrix make the proxy falsifiable.
    """

    if points < 21:
        raise ValueError("points must be at least 21")
    x = np.linspace(0.0, 1.0, points)
    y = np.linspace(0.0, 1.0, points)
    xx, yy = np.meshgrid(x, y, indexing="xy")
    dx = float(x[1] - x[0])
    dy = float(y[1] - y[0])
    fields: dict[str, RealArray] = {}
    helmholtz_residuals: list[float] = []
    flattened: list[RealArray] = []
    for m, n, longitudinal in modes:
        if m < 0 or n < 0 or (m == 0 and n == 0) or longitudinal != 0:
            raise ValueError("this proxy expects transverse TE(m,n,0) modes")
        field = np.cos(m * pi * xx) * np.cos(n * pi * yy)
        norm = sqrt(float(np.trapezoid(np.trapezoid(field**2, x, axis=1), y)))
        field = np.asarray(field / norm, dtype=float)
        label = f"TE{m}{n}{longitudinal}"
        fields[label] = field
        flattened.append(field)

        laplacian = (
            (field[1:-1, 2:] - 2.0 * field[1:-1, 1:-1] + field[1:-1, :-2])
            / dx**2
            + (field[2:, 1:-1] - 2.0 * field[1:-1, 1:-1] + field[:-2, 1:-1])
            / dy**2
        )
        wave_number_squared = pi**2 * (m**2 + n**2)
        residual = laplacian + wave_number_squared * field[1:-1, 1:-1]
        helmholtz_residuals.append(
            float(np.max(np.abs(residual)) / np.max(np.abs(field)))
        )

    gram = np.asarray(
        [
            [
                np.trapezoid(np.trapezoid(left * right, x, axis=1), y)
                for right in flattened
            ]
            for left in flattened
        ],
        dtype=float,
    )
    return {
        "x": x,
        "y": y,
        "fields": fields,
        "mode_labels": list(fields),
        "max_helmholtz_residual": float(max(helmholtz_residuals)),
        "max_orthonormality_error": float(np.max(np.abs(gram - np.eye(len(modes))))),
        "boundary_condition": "normalized ideal PEC rectangle; source pixels are not inputs",
    }


def dissipation_drive_claim_checks() -> dict[str, float]:
    t1 = 22.0
    tphi = 35.0
    t2 = 1.0 / (0.5 / t1 + 1.0 / tphi)
    t2_identity_residual = abs(1.0 / t2 - (0.5 / t1 + 1.0 / tphi))

    coupling = 0.09
    detuning = 1.8
    kappa = 0.04
    purcell_exact = kappa * coupling**2 / detuning**2
    purcell_scaling_residual = abs(purcell_exact / kappa - (coupling / detuning) ** 2)

    alpha = 1.3
    coefficients = coherent_coefficients(alpha, 30)
    probabilities = np.abs(coefficients) ** 2
    poisson = np.array(
        [
            np.exp(-abs(alpha) ** 2) * abs(alpha) ** (2 * n) / factorial(n)
            for n in range(30)
        ],
        dtype=float,
    )
    poisson /= np.sum(poisson)
    poisson_residual = float(np.max(np.abs(probabilities - poisson)))
    mean_excitation_residual = abs(float(np.sum(np.arange(30) * probabilities)) - abs(alpha) ** 2)
    return {
        "t2_identity_residual": float(t2_identity_residual),
        "purcell_scaling_residual": float(purcell_scaling_residual),
        "coherent_poisson_residual": poisson_residual,
        "mean_excitation_residual": float(mean_excitation_residual),
    }


def amplifier_iq_claim_checks() -> dict[str, float]:
    gains = [2.0, 10.0, 1000.0]
    commutator_errors = []
    added_noise_errors = []
    for gain in gains:
        metrics = phase_preserving_amplifier_metrics(gain)
        commutator_errors.append(abs(metrics["output_commutator"] - 1.0))
        expected_added = 0.5 * (1.0 - 1.0 / gain)
        added_noise_errors.append(abs(metrics["input_referred_added_noise"] - expected_added))

    time = np.linspace(0.0, 8.0 * pi, 8001)
    i_overlap = float(
        np.trapezoid(np.cos(time) * np.sin(time), time) / np.trapezoid(np.cos(time) ** 2, time)
    )
    return {
        "max_commutator_error": float(max(commutator_errors)),
        "max_added_noise_error": float(max(added_noise_errors)),
        "iq_orthogonality_overlap": abs(i_overlap),
    }


def tomography_claim_checks() -> dict[str, float]:
    grid = np.linspace(-6.0, 6.0, 401)
    vacuum = coherent_coefficients(0.0, 24)
    wigner = fock_state_wigner(vacuum, grid, grid)
    wigner_integral = float(np.trapezoid(np.trapezoid(wigner, grid, axis=1), grid))
    x_marginal = np.trapezoid(wigner, grid, axis=0)
    vacuum_probability = np.exp(-grid**2) / sqrt(pi)
    marginal_residual = float(np.max(np.abs(x_marginal - vacuum_probability)))

    alpha = 0.7 + 0.4j
    q = np.exp(-np.abs(grid[:, None] + 1j * grid[None, :] - alpha) ** 2) / pi
    q_integral = float(np.trapezoid(np.trapezoid(q, grid, axis=1), grid))
    return {
        "wigner_integral_error": abs(wigner_integral - 1.0),
        "marginal_residual": marginal_residual,
        "q_integral_error": abs(q_integral - 1.0),
    }
