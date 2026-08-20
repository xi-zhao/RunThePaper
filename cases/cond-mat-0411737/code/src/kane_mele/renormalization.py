"""Independent one-loop Coulomb shell integration for the Kane-Mele RG."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import constants, integrate, optimize


@dataclass(frozen=True)
class RGFlowCoefficients:
    """Coefficients derived from the self-energy and vertex shell integrals."""

    coupling_decay: float
    gap_growth: float
    velocity_projection_residual: float
    gap_projection_residual: float
    shell_ell: float


def _pauli() -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    identity = np.eye(2, dtype=np.complex128)
    sigma_x = np.asarray([[0, 1], [1, 0]], dtype=np.complex128)
    sigma_y = np.asarray([[0, -1j], [1j, 0]], dtype=np.complex128)
    sigma_z = np.asarray([[1, 0], [0, -1]], dtype=np.complex128)
    return identity, sigma_x, sigma_y, sigma_z


def _exchange_self_energy(
    momentum_x: float,
    mass: float,
    *,
    shell_ell: float,
    radial_points: int,
    angular_points: int,
) -> np.ndarray:
    """Integrate ``(1/2) int V(q) H(q+k)/E(q+k)`` over a log shell.

    Dimensionless units set ``v_F=e^2=Lambda=1``.  The instantaneous Coulomb
    Fourier transform is ``V(q)=2 pi/q``.  The omitted identity Fock shift does
    not contribute to either the velocity or mass projection.
    """

    if shell_ell <= 0 or radial_points < 8 or angular_points < 24:
        raise ValueError("positive shell and resolved radial/angular grids required")
    nodes, weights = np.polynomial.legendre.leggauss(radial_points)
    log_q = 0.5 * shell_ell * (nodes - 1.0)
    log_weights = 0.5 * shell_ell * weights
    q_values = np.exp(log_q)
    theta = 2.0 * np.pi * (np.arange(angular_points) + 0.5) / angular_points
    theta_weight = 2.0 * np.pi / angular_points
    _identity, sigma_x, sigma_y, sigma_z = _pauli()
    result = np.zeros((2, 2), dtype=np.complex128)
    for q_value, radial_weight in zip(q_values, log_weights):
        px = q_value * np.cos(theta) + momentum_x
        py = q_value * np.sin(theta)
        energy = np.sqrt(px**2 + py**2 + mass**2)
        normalized_x = float(np.sum(px / energy) * theta_weight)
        normalized_y = float(np.sum(py / energy) * theta_weight)
        normalized_mass = float(np.sum(mass / energy) * theta_weight)
        normalized_hamiltonian = (
            normalized_x * sigma_x + normalized_y * sigma_y + normalized_mass * sigma_z
        )
        # d^2q/(2pi)^2 * (1/2)*(2pi/q), with q dq=q^2 d(log q),
        # reduces to q d(log q)/(4pi).
        result += radial_weight * q_value / (4.0 * np.pi) * normalized_hamiltonian
    return result


def derive_one_loop_flow_coefficients(
    *,
    shell_ell: float = 1.5,
    radial_points: int = 48,
    angular_points: int = 192,
    finite_difference_step: float = 1e-4,
) -> RGFlowCoefficients:
    """Derive the ``1/4`` and ``1/2`` coefficients without reusing them."""

    if finite_difference_step <= 0:
        raise ValueError("finite_difference_step must be positive")
    _identity, sigma_x, sigma_y, sigma_z = _pauli()
    velocity_plus = _exchange_self_energy(
        finite_difference_step,
        0.0,
        shell_ell=shell_ell,
        radial_points=radial_points,
        angular_points=angular_points,
    )
    velocity_minus = _exchange_self_energy(
        -finite_difference_step,
        0.0,
        shell_ell=shell_ell,
        radial_points=radial_points,
        angular_points=angular_points,
    )
    velocity_derivative = (velocity_plus - velocity_minus) / (
        2.0 * finite_difference_step
    )
    velocity_coefficient = float(
        np.trace(sigma_x @ velocity_derivative).real / 2.0 / shell_ell
    )
    velocity_reconstructed = shell_ell * velocity_coefficient * sigma_x

    mass_plus = _exchange_self_energy(
        0.0,
        finite_difference_step,
        shell_ell=shell_ell,
        radial_points=radial_points,
        angular_points=angular_points,
    )
    mass_minus = _exchange_self_energy(
        0.0,
        -finite_difference_step,
        shell_ell=shell_ell,
        radial_points=radial_points,
        angular_points=angular_points,
    )
    mass_derivative = (mass_plus - mass_minus) / (2.0 * finite_difference_step)
    mass_coefficient = float(np.trace(sigma_z @ mass_derivative).real / 2.0 / shell_ell)
    mass_reconstructed = shell_ell * mass_coefficient * sigma_z
    return RGFlowCoefficients(
        coupling_decay=velocity_coefficient,
        gap_growth=mass_coefficient,
        velocity_projection_residual=float(
            np.max(np.abs(velocity_derivative - velocity_reconstructed))
        ),
        gap_projection_residual=float(
            np.max(np.abs(mass_derivative - mass_reconstructed))
        ),
        shell_ell=shell_ell,
    )


def exchange_log_sweep(
    shell_ells: np.ndarray,
    *,
    radial_points: int = 40,
    angular_points: int = 144,
) -> tuple[list[dict[str, float]], dict[str, float]]:
    """Sweep shell width and fit the logarithmic self-energy/vertex growth."""

    ells = np.asarray(shell_ells, dtype=float)
    if ells.ndim != 1 or len(ells) < 4 or np.any(ells <= 0):
        raise ValueError("shell_ells must contain at least four positive values")
    rows: list[dict[str, float]] = []
    for ell in ells:
        coefficients = derive_one_loop_flow_coefficients(
            shell_ell=float(ell),
            radial_points=radial_points,
            angular_points=angular_points,
        )
        rows.append(
            {
                "shell_ell": float(ell),
                "velocity_log_correction": coefficients.coupling_decay * ell,
                "gap_log_correction": coefficients.gap_growth * ell,
                "velocity_coefficient": coefficients.coupling_decay,
                "gap_coefficient": coefficients.gap_growth,
            }
        )
    velocity_slope = float(
        np.polyfit(
            [row["shell_ell"] for row in rows],
            [row["velocity_log_correction"] for row in rows],
            1,
        )[0]
    )
    gap_slope = float(
        np.polyfit(
            [row["shell_ell"] for row in rows],
            [row["gap_log_correction"] for row in rows],
            1,
        )[0]
    )
    return rows, {
        "fitted_velocity_log_slope": velocity_slope,
        "fitted_gap_log_slope": gap_slope,
    }


def _static_dirac_polarization_coefficient(
    cutoff_ratio: float, *, angular_points: int, integration_tolerance: float
) -> tuple[float, float]:
    """Numerically integrate ``-Pi(q)/q`` for four neutral Dirac flavors.

    Momentum is scaled by the external ``q`` only after writing the interband
    Lindhard integral.  The coefficient is therefore an output of the spinor
    overlap and energy denominator, not the analytic ``1/4`` result inserted
    into the generator.
    """

    if cutoff_ratio <= 1 or angular_points < 64 or integration_tolerance <= 0:
        raise ValueError("resolved angular grid, cutoff_ratio>1 and tolerance required")
    angles = 2.0 * np.pi * (np.arange(angular_points) + 0.5) / angular_points
    cosines = np.cos(angles)

    def radial_integrand(scaled_momentum: float) -> float:
        shifted = np.sqrt(scaled_momentum**2 + 1.0 + 2.0 * scaled_momentum * cosines)
        cosine_between = np.where(
            scaled_momentum * shifted > 0,
            (scaled_momentum + cosines) / shifted,
            1.0,
        )
        interband_overlap = 0.5 * (1.0 - cosine_between)
        return float(
            scaled_momentum
            * np.mean(interband_overlap / (scaled_momentum + shifted))
            * 2.0
            * np.pi
        )

    integral, error = integrate.quad(
        radial_integrand,
        0.0,
        cutoff_ratio,
        points=[1.0],
        epsabs=integration_tolerance,
        epsrel=integration_tolerance,
        limit=300,
    )
    degeneracy = 4.0
    coefficient = 2.0 * degeneracy * integral / (2.0 * np.pi) ** 2
    return float(coefficient), float(error)


def screened_coulomb_diagnostics(
    momenta: np.ndarray,
    *,
    coulomb_g: float,
    ultraviolet_cutoff: float = 1.0,
    angular_points: int = 256,
    integration_tolerance: float = 1e-8,
) -> tuple[list[dict[str, float]], dict[str, float]]:
    """Compute neutral-Dirac polarization and then test the screened power."""

    q_values = np.asarray(momenta, dtype=float)
    if q_values.ndim != 1 or len(q_values) < 4 or np.any(q_values <= 0):
        raise ValueError("positive momentum sweep required")
    if coulomb_g <= 0:
        raise ValueError("coulomb_g must be positive")
    if ultraviolet_cutoff <= max(q_values):
        raise ValueError("ultraviolet cutoff must exceed every external momentum")
    rows: list[dict[str, float]] = []
    for momentum in q_values:
        cutoff_ratio = ultraviolet_cutoff / float(momentum)
        coefficient, quadrature_error = _static_dirac_polarization_coefficient(
            cutoff_ratio,
            angular_points=angular_points,
            integration_tolerance=integration_tolerance,
        )
        angular_coarse, _coarse_error = _static_dirac_polarization_coefficient(
            cutoff_ratio,
            angular_points=angular_points // 2,
            integration_tolerance=2.0 * integration_tolerance,
        )
        doubled_cutoff, _cutoff_error = _static_dirac_polarization_coefficient(
            2.0 * cutoff_ratio,
            angular_points=angular_points,
            integration_tolerance=integration_tolerance,
        )
        polarization = -coefficient * float(momentum)
        dielectric = 1.0 + 2.0 * np.pi * coulomb_g * coefficient
        potential = 1.0 / (dielectric * float(momentum))
        rows.append(
            {
                "momentum_over_cutoff": float(momentum / ultraviolet_cutoff),
                "polarization_over_cutoff": float(polarization / ultraviolet_cutoff),
                "minus_polarization_over_q": coefficient,
                "analytic_dirac_limit": 0.25,
                "quadrature_error_estimate": quadrature_error,
                "angular_convergence_delta": abs(coefficient - angular_coarse),
                "uv_cutoff_doubling_delta": abs(coefficient - doubled_cutoff),
                "dielectric_factor": float(dielectric),
                "screened_potential_in_2pi_e2": float(potential),
                "q_times_screened_potential_in_2pi_e2": float(momentum * potential),
            }
        )
    products = np.asarray([row["q_times_screened_potential_in_2pi_e2"] for row in rows])
    polarization_power = float(
        np.polyfit(
            np.log(q_values),
            np.log([-row["polarization_over_cutoff"] for row in rows]),
            1,
        )[0]
    )
    fitted_power = float(
        np.polyfit(
            np.log(q_values),
            np.log([row["screened_potential_in_2pi_e2"] for row in rows]),
            1,
        )[0]
    )
    return rows, {
        "polarization_fitted_momentum_power": polarization_power,
        "max_abs_coefficient_error_from_quarter": float(
            max(abs(row["minus_polarization_over_q"] - 0.25) for row in rows)
        ),
        "max_angular_convergence_delta": float(
            max(row["angular_convergence_delta"] for row in rows)
        ),
        "max_uv_cutoff_doubling_delta": float(
            max(row["uv_cutoff_doubling_delta"] for row in rows)
        ),
        "dielectric_factor_range": [
            float(min(row["dielectric_factor"] for row in rows)),
            float(max(row["dielectric_factor"] for row in rows)),
        ],
        "fitted_momentum_power": fitted_power,
        "qV_relative_spread": float(np.ptp(products) / np.mean(products)),
    }


def rg_running_values(
    ell: float,
    *,
    coulomb_g0: float,
    bare_half_gap: float,
    coefficients: RGFlowCoefficients,
) -> tuple[float, float]:
    """Integrate the flows using independently derived coefficients."""

    if ell < 0 or coulomb_g0 <= 0 or bare_half_gap <= 0:
        raise ValueError("RG inputs must satisfy ell>=0, g0>0 and Delta0>0")
    scale = 1.0 + coefficients.coupling_decay * coulomb_g0 * ell
    exponent = coefficients.gap_growth / coefficients.coupling_decay
    return coulomb_g0 / scale, bare_half_gap * scale**exponent


def renormalized_gap_kelvin(
    *,
    bare_full_gap_kelvin: float,
    coulomb_g0: float,
    cutoff_ev: float,
    coefficients: RGFlowCoefficients,
) -> float:
    """Solve the self-consistent infrared stopping condition."""

    if bare_full_gap_kelvin <= 0 or coulomb_g0 <= 0 or cutoff_ev <= 0:
        raise ValueError("RG inputs must be positive")
    bare_half_gap = bare_full_gap_kelvin / 2.0
    cutoff_kelvin = cutoff_ev * constants.elementary_charge / constants.k
    exponent = coefficients.gap_growth / coefficients.coupling_decay

    def residual(half_gap: float) -> float:
        scale = 1.0 + coefficients.coupling_decay * coulomb_g0 * np.log(
            cutoff_kelvin / half_gap
        )
        return float(half_gap - bare_half_gap * scale**exponent)

    renormalized_half_gap = optimize.brentq(
        residual, bare_half_gap, cutoff_kelvin, xtol=1e-13, rtol=1e-13
    )
    return float(2.0 * renormalized_half_gap)
