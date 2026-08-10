"""Two-parameter TDVP flow and independently evaluated variational residual."""

from __future__ import annotations

from dataclasses import dataclass
from math import comb, pi, sqrt

import numpy as np
from scipy.integrate import solve_ivp

from .constrained import constrained_states, full_hamiltonian


def tdvp_flow(theta: float | np.ndarray, other: float | np.ndarray, spin: float) -> np.ndarray:
    """Main Eq. (4), with Omega set to one."""

    theta = np.asarray(theta)
    other = np.asarray(other)
    cosine = np.cos(theta / 2.0)
    exponent_a = int(round(4 * spin - 2))
    exponent_b = int(round(2 * spin))
    exponent_c = int(round(6 * spin - 1))
    with np.errstate(divide="ignore", invalid="ignore", over="ignore"):
        result = (
            1.0
            - cosine**exponent_a
            + cosine**exponent_a * np.cos(other / 2.0) ** exponent_b
            + 2.0
            * spin
            * np.sin(theta / 2.0)
            * cosine**exponent_c
            * np.tan(other / 2.0)
        )
    return result


def deformed_flow(
    theta: float | np.ndarray, other: float | np.ndarray, deformation: float
) -> np.ndarray:
    """Supplement V flow for spin 1/2 and Omega=1."""

    theta = np.asarray(theta)
    other = np.asarray(other)
    with np.errstate(divide="ignore", invalid="ignore", over="ignore"):
        secant = 1.0 / np.cos(other / 2.0)
        undeformed = secant * (
            np.cos(other / 2.0) ** 2
            + np.cos(theta / 2.0) ** 2
            * np.sin(theta / 2.0)
            * np.sin(other / 2.0)
        )
        perturbation = secant * (
            np.cos(theta) * np.cos(other / 2.0) ** 2
            + np.cos(theta / 2.0) ** 2
            * np.cos(other)
            * np.sin(theta / 2.0)
            * np.sin(other / 2.0)
        )
    return undeformed + deformation * perturbation


def integrate_orbit_segment(
    spin: float,
    *,
    deformation: float = 0.0,
    samples: int = 480,
    endpoint_cutoff: float = 1e-3,
) -> tuple[np.ndarray, np.ndarray, float]:
    """Integrate from Z2 to the coordinate chart boundary at Z2'."""

    def rhs(_time: float, state: np.ndarray) -> tuple[float, float]:
        if deformation:
            return (
                float(deformed_flow(state[0], state[1], deformation)),
                float(deformed_flow(state[1], state[0], deformation)),
            )
        return (
            float(tdvp_flow(state[0], state[1], spin)),
            float(tdvp_flow(state[1], state[0], spin)),
        )

    def chart_boundary(_time: float, state: np.ndarray) -> float:
        return float(np.cos(state[1] / 2.0) - endpoint_cutoff)

    chart_boundary.terminal = True  # type: ignore[attr-defined]
    chart_boundary.direction = -1  # type: ignore[attr-defined]
    solution = solve_ivp(
        rhs,
        (0.0, 8.0),
        (-pi + 1e-4, 0.0),
        events=chart_boundary,
        max_step=0.01,
        rtol=2e-9,
        atol=2e-11,
        dense_output=True,
    )
    if not solution.t_events[0].size:
        raise RuntimeError("periodic orbit did not reach the expected chart boundary")
    half_period = float(solution.t_events[0][0])
    times = np.linspace(0.0, half_period, samples)
    coordinates = solution.sol(times).T
    return times, coordinates, 2.0 * half_period


def _power_derivative(
    cosine: float, sine: float, cosine_power: np.ndarray, sine_power: np.ndarray
) -> np.ndarray:
    result = np.zeros_like(cosine_power, dtype=float)
    mask = cosine_power > 0
    result[mask] -= (
        0.5
        * cosine_power[mask]
        * cosine ** (cosine_power[mask] - 1)
        * sine ** (sine_power[mask] + 1)
    )
    mask = sine_power > 0
    result[mask] += (
        0.5
        * sine_power[mask]
        * cosine ** (cosine_power[mask] + 1)
        * sine ** (sine_power[mask] - 1)
    )
    return result


@dataclass
class VariationalManifold:
    """Finite-ring MPS state, tangents, Hamiltonian, and residual norm."""

    length: int
    spin: float

    def __post_init__(self) -> None:
        self.max_occupation = int(round(2 * self.spin))
        self.states = constrained_states(self.length, self.max_occupation)
        count = len(self.states)
        self.cosine_powers = np.zeros((count, 2), dtype=int)
        self.sine_powers = np.zeros((count, 2), dtype=int)
        self.prefactors = np.ones(count, dtype=complex)
        binomials = np.sqrt(
            np.asarray([comb(self.max_occupation, n) for n in range(self.max_occupation + 1)])
        )
        for state_index, state in enumerate(self.states):
            phase = 0
            for site, occupation in enumerate(state):
                sublattice = site % 2
                if occupation:
                    self.cosine_powers[state_index, sublattice] += (
                        self.max_occupation - occupation
                    )
                    self.sine_powers[state_index, sublattice] += occupation
                    self.prefactors[state_index] *= binomials[occupation]
                    phase += occupation
                elif state[(site - 1) % self.length] == 0:
                    self.cosine_powers[state_index, sublattice] += self.max_occupation
            self.prefactors[state_index] *= (-1j) ** phase
        self._hamiltonians: dict[float, object] = {}

    def hamiltonian(self, deformation: float = 0.0):
        key = float(deformation)
        if key not in self._hamiltonians:
            self._hamiltonians[key] = full_hamiltonian(
                self.states,
                self.max_occupation,
                deformation=key,
            )
        return self._hamiltonians[key]

    def state_and_tangents(
        self, theta_even: float, theta_odd: float
    ) -> tuple[np.ndarray, tuple[np.ndarray, np.ndarray]]:
        angles = (theta_even, theta_odd)
        cosines = np.cos(np.asarray(angles) / 2.0)
        sines = np.sin(np.asarray(angles) / 2.0)
        unnormalized = self.prefactors.copy()
        for sublattice in range(2):
            unnormalized *= (
                cosines[sublattice] ** self.cosine_powers[:, sublattice]
                * sines[sublattice] ** self.sine_powers[:, sublattice]
            )
        norm = float(np.linalg.norm(unnormalized))
        if norm < 1e-13:
            raise ValueError("MPS coordinate is singular")
        state = unnormalized / norm
        tangents: list[np.ndarray] = []
        for differentiated in range(2):
            derivative = self.prefactors.copy()
            for sublattice in range(2):
                if sublattice == differentiated:
                    factor = _power_derivative(
                        float(cosines[sublattice]),
                        float(sines[sublattice]),
                        self.cosine_powers[:, sublattice],
                        self.sine_powers[:, sublattice],
                    )
                else:
                    factor = (
                        cosines[sublattice] ** self.cosine_powers[:, sublattice]
                        * sines[sublattice] ** self.sine_powers[:, sublattice]
                    )
                derivative *= factor
            overlap = float(np.real(np.vdot(unnormalized, derivative)))
            tangents.append(derivative / norm - unnormalized * overlap / norm**3)
        return state, (tangents[0], tangents[1])

    def residual(
        self, theta_even: float, theta_odd: float, *, deformation: float = 0.0
    ) -> float:
        state, tangents = self.state_and_tangents(theta_even, theta_odd)
        if deformation:
            velocities = (
                float(deformed_flow(theta_even, theta_odd, deformation)),
                float(deformed_flow(theta_odd, theta_even, deformation)),
            )
        else:
            velocities = (
                float(tdvp_flow(theta_even, theta_odd, self.spin)),
                float(tdvp_flow(theta_odd, theta_even, self.spin)),
            )
        residual = (
            1j * (self.hamiltonian(deformation) @ state)
            + velocities[0] * tangents[0]
            + velocities[1] * tangents[1]
        )
        return float(np.linalg.norm(residual) / sqrt(self.length))

    def projected_velocity(
        self, theta_even: float, theta_odd: float, *, deformation: float = 0.0
    ) -> np.ndarray:
        """Project -iH|psi> onto the two tangents without using printed EOM."""

        state, tangents = self.state_and_tangents(theta_even, theta_odd)
        gram = np.asarray(
            [
                [float(np.real(np.vdot(left, right))) for right in tangents]
                for left in tangents
            ]
        )
        instantaneous = 1j * (self.hamiltonian(deformation) @ state)
        right_hand_side = -np.asarray(
            [float(np.real(np.vdot(tangent, instantaneous))) for tangent in tangents]
        )
        return np.linalg.solve(gram, right_hand_side)

    def heatmap(self, grid: np.ndarray) -> np.ndarray:
        values = np.full((len(grid), len(grid)), np.nan, dtype=float)
        for row, theta_odd in enumerate(grid):
            for column, theta_even in enumerate(grid):
                try:
                    values[row, column] = self.residual(theta_even, theta_odd)
                except (ValueError, FloatingPointError):
                    continue
        return values

    def orbit_integrals(self, deformation: float) -> dict[str, float | np.ndarray]:
        times, coordinates, period = integrate_orbit_segment(
            0.5, deformation=deformation, samples=360
        )
        gamma = np.asarray(
            [
                self.residual(even, odd, deformation=deformation)
                for even, odd in coordinates
            ]
        )
        return {
            "times": times,
            "coordinates": coordinates,
            "period": period,
            "integrated_error": float(2.0 * np.trapezoid(gamma, times)),
            "integrated_fluctuation": float(2.0 * np.trapezoid(gamma**2, times)),
        }
