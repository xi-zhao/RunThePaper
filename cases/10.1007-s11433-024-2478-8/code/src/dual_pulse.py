"""Pure numerical dual-pulse dynamics shared by science and render paths."""

from __future__ import annotations

import numpy as np
from scipy.integrate import solve_ivp

import coefficients as coefficients
import hamiltonians as hamiltonians
from waveforms import TAU_US, TWO_PI


PROTOCOL = coefficients.FIG5_SINGLE_PULSE
TOTAL_DURATION_US = 2.0 * TAU_US


def _doppler_sign(time_us: float, flip: bool) -> float:
    if not flip:
        return 1.0
    return 1.0 if time_us < TAU_US else -1.0


def _sector_phase(
    dimension: int,
    initial_index: int,
    hamiltonian_builder: object,
    output_points: int,
    doppler_mhz: float,
    *,
    flip: bool,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    blockade = TWO_PI * PROTOCOL.B_mhz
    doppler = TWO_PI * doppler_mhz

    def waveform(function: object, time_us: float) -> float:
        return float(np.asarray(function(time_us % TAU_US)))

    def rhs(time_us: float, state: np.ndarray) -> np.ndarray:
        sign = _doppler_sign(time_us, flip)
        omega1 = waveform(PROTOCOL.omega1, time_us)
        omega2 = waveform(PROTOCOL.omega2, time_us)
        delta1 = waveform(PROTOCOL.delta1, time_us) + sign * doppler
        delta2 = waveform(PROTOCOL.delta2, time_us) + sign * doppler
        matrix = hamiltonian_builder(omega1, omega2, delta1, delta2, blockade)
        psi = state[:dimension] + 1j * state[dimension:]
        derivative = -1j * (matrix @ psi)
        return np.concatenate([derivative.real, derivative.imag])

    initial = np.zeros(2 * dimension)
    initial[initial_index] = 1.0
    times = np.linspace(0.0, TOTAL_DURATION_US, output_points)
    solution = solve_ivp(
        rhs,
        (0.0, TOTAL_DURATION_US),
        initial,
        t_eval=times,
        method="DOP853",
        rtol=1e-11,
        atol=1e-13,
        max_step=TOTAL_DURATION_US / 4000,
    )
    amplitude = solution.y[initial_index] + 1j * solution.y[dimension + initial_index]
    return times, np.angle(amplitude), amplitude


SECTORS = {
    "00": (
        2,
        hamiltonians.SECTOR00_INIT,
        lambda omega1, omega2, delta1, delta2, blockade: hamiltonians.h_sector00(
            omega1, delta1
        ),
    ),
    "01": (
        5,
        hamiltonians.SECTOR01_INIT,
        lambda omega1, omega2, delta1, delta2, blockade: hamiltonians.h_sector01(
            omega1, omega2, delta1, delta2, blockade, 0.0
        ),
    ),
    "11": (
        9,
        hamiltonians.SECTOR11_INIT,
        lambda omega1, omega2, delta1, delta2, blockade: hamiltonians.h_sector11(
            omega1, omega2, delta1, delta2, blockade, 0.0
        ),
    ),
}


def run_dual_pulse(
    doppler_mhz: float, output_points: int = 401, *, flip: bool = True
) -> dict[str, tuple[np.ndarray, np.ndarray, np.ndarray]]:
    """Return phase/amplitude trajectories without rendering or reference access."""

    return {
        sector: _sector_phase(
            dimension,
            initial_index,
            builder,
            output_points,
            doppler_mhz,
            flip=flip,
        )
        for sector, (dimension, initial_index, builder) in SECTORS.items()
    }
