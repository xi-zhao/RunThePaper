"""Independent absorbing-boundary solver for the -C4/r^4 potential."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.integrate import solve_ivp
from scipy.special import spherical_jn, spherical_yn


def barrier_energy(partial_wave: int) -> float:
    if partial_wave < 0:
        raise ValueError("partial wave must be nonnegative")
    angular = partial_wave * (partial_wave + 1)
    return float(angular**2 / 4.0)


def _incoming_boundary(x: float) -> tuple[complex, complex]:
    """Incoming WKB solution x exp(+i/x), carrying flux toward short range."""

    phase = np.exp(1j / x)
    return x * phase, phase * (1.0 - 1j / x)


def _riccati_hankel(partial_wave: int, z: float, k: float) -> tuple[complex, ...]:
    j = spherical_jn(partial_wave, z)
    y = spherical_yn(partial_wave, z)
    jp = spherical_jn(partial_wave, z, derivative=True)
    yp = spherical_yn(partial_wave, z, derivative=True)
    outgoing = z * (j + 1j * y)
    incoming = z * (j - 1j * y)
    outgoing_prime = k * ((j + 1j * y) + z * (jp + 1j * yp))
    incoming_prime = k * ((j - 1j * y) + z * (jp - 1j * yp))
    return incoming, outgoing, incoming_prime, outgoing_prime


def capture_probability(
    energy_es: float,
    partial_wave: int,
    *,
    x_min: float = 0.08,
    asymptotic_cycles: float = 35.0,
    x_floor: float = 80.0,
    rtol: float = 2.0e-8,
    atol: float = 2.0e-10,
) -> float:
    """Short-range flux loss 1-|S_l|^2 in dimensionless polarization units."""

    if energy_es <= 0 or partial_wave < 0 or x_min <= 0:
        raise ValueError("energy, partial wave, and boundary must be physical")
    k = float(np.sqrt(energy_es))
    x_max = max(x_floor, asymptotic_cycles / k)
    u0, up0 = _incoming_boundary(x_min)

    def radial_equation(x: float, state: np.ndarray) -> np.ndarray:
        potential = energy_es - partial_wave * (partial_wave + 1) / x**2 + 1.0 / x**4
        return np.asarray([state[1], -potential * state[0]], dtype=complex)

    solution = solve_ivp(
        radial_equation,
        (x_min, x_max),
        np.asarray([u0, up0], dtype=complex),
        method="DOP853",
        rtol=rtol,
        atol=atol,
    )
    if not solution.success:
        raise RuntimeError(f"radial integration failed: {solution.message}")
    wave, derivative = solution.y[:, -1]
    incoming, outgoing, incoming_prime, outgoing_prime = _riccati_hankel(
        partial_wave, k * x_max, k
    )
    matrix = np.asarray(
        [[incoming, outgoing], [incoming_prime, outgoing_prime]], dtype=complex
    )
    amplitude_in, amplitude_out = np.linalg.solve(
        matrix, np.asarray([wave, derivative], dtype=complex)
    )
    scattering = amplitude_out / amplitude_in
    probability = 1.0 - abs(scattering) ** 2
    if probability < -2e-7 or probability > 1.0 + 2e-7:
        raise RuntimeError(f"nonphysical capture probability {probability}")
    return float(np.clip(probability, 0.0, 1.0))


@dataclass(frozen=True)
class CaptureTable:
    energies_es: np.ndarray
    probabilities: np.ndarray

    def __post_init__(self) -> None:
        energies = np.asarray(self.energies_es, dtype=float)
        values = np.asarray(self.probabilities, dtype=float)
        if energies.ndim != 1 or values.ndim != 2:
            raise ValueError("energies must be 1D and probabilities must be 2D")
        if values.shape[1] != energies.size:
            raise ValueError("probability columns must match energy grid")
        if np.any(np.diff(energies) <= 0) or np.any(energies <= 0):
            raise ValueError("energy grid must be strictly increasing and positive")
        if np.any(values < 0) or np.any(values > 1):
            raise ValueError("capture probabilities must lie in [0,1]")

    @property
    def partial_waves(self) -> int:
        return int(self.probabilities.shape[0])

    def evaluate(self, energy_es: np.ndarray | float, partial_wave: int) -> np.ndarray:
        if not 0 <= partial_wave < self.partial_waves:
            raise ValueError("partial wave outside capture table")
        energy = np.asarray(energy_es, dtype=float)
        if np.any(energy <= 0):
            raise ValueError("energy must be positive")
        source = np.maximum(self.probabilities[partial_wave], 1e-300)
        log_result = np.interp(
            np.log(energy),
            np.log(self.energies_es),
            np.log(source),
            left=np.nan,
            right=np.nan,
        )
        low = energy < self.energies_es[0]
        high = energy > self.energies_es[-1]
        result = np.exp(log_result)
        if np.any(low):
            exponent = partial_wave + 0.5
            anchor = self.probabilities[partial_wave, 0]
            result = np.where(
                low,
                anchor * (energy / self.energies_es[0]) ** exponent,
                result,
            )
        if np.any(high):
            result = np.where(
                high,
                1.0
                - (1.0 - self.probabilities[partial_wave, -1])
                * np.sqrt(self.energies_es[-1] / energy),
                result,
            )
        return np.clip(result, 0.0, 1.0)


def build_capture_table(
    energies_es: np.ndarray,
    max_partial_wave: int = 3,
    **solver_options: float,
) -> CaptureTable:
    energies = np.asarray(energies_es, dtype=float)
    rows = []
    for partial_wave in range(max_partial_wave + 1):
        rows.append(
            np.asarray(
                [
                    capture_probability(float(energy), partial_wave, **solver_options)
                    for energy in energies
                ],
                dtype=float,
            )
        )
    return CaptureTable(energies, np.vstack(rows))
