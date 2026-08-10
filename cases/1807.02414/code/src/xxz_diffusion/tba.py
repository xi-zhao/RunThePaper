"""Root-of-unity XXZ thermodynamic Bethe ansatz.

Only formulas from the paper and its cited primary theory are implemented.  No
source figure, author array, or author implementation is read by this module.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.linalg import solve


@dataclass(frozen=True)
class StationaryState:
    """Numerical stationary state and its independently dressed observables."""

    ell: int
    rapidity: np.ndarray
    quadrature_weight: float
    string_lengths: np.ndarray
    parities: np.ndarray
    signs: np.ndarray
    fillings: np.ndarray
    particle_density: np.ndarray
    total_density: np.ndarray
    velocity: np.ndarray
    dressed_spin: np.ndarray
    susceptibility: float
    susceptibility_weights: np.ndarray
    dressed_scattering: np.ndarray
    spin_onsager: float


def infinite_temperature_fillings(ell: int) -> np.ndarray:
    """Return the exact half-filled, infinite-temperature Y-system fillings."""

    if ell < 3:
        raise ValueError("ell must be at least 3")
    bulk = [1.0 / float(j + 1) ** 2 for j in range(1, ell - 1)]
    return np.asarray([*bulk, 1.0 / ell, (ell - 1.0) / ell], dtype=float)


class RootOfUnityXXZ:
    """Midpoint-Nyström solver for Delta=cos(pi/ell)."""

    def __init__(self, ell: int, rapidity_cutoff: float, rapidity_points: int) -> None:
        if ell < 3:
            raise ValueError("ell must be at least 3")
        if rapidity_cutoff <= 0:
            raise ValueError("rapidity_cutoff must be positive")
        if rapidity_points < 32 or rapidity_points % 2:
            raise ValueError("rapidity_points must be an even integer >= 32")

        self.ell = int(ell)
        self.gamma = np.pi / self.ell
        self.rapidity_cutoff = float(rapidity_cutoff)
        self.rapidity_points = int(rapidity_points)
        self.dlambda = 2.0 * self.rapidity_cutoff / self.rapidity_points
        self.rapidity = np.linspace(
            -self.rapidity_cutoff + self.dlambda / 2.0,
            self.rapidity_cutoff - self.dlambda / 2.0,
            self.rapidity_points,
        )
        self.string_lengths = np.asarray([*range(1, self.ell), 1], dtype=int)
        self.parities = np.asarray([*[1.0] * (self.ell - 1), -1.0])
        self.signs = self.parities.copy()
        self.fillings = infinite_temperature_fillings(self.ell)

    def _a_kernel(self, length: int, parity: float, rapidity: np.ndarray) -> np.ndarray:
        sine = float(np.sin(length * self.gamma))
        # Under the finite root-of-unity string prescription, regular zero
        # kernels are identically zero.  Testing sine first also avoids 0/0 at
        # lambda=0 for the formal endpoint kernel.
        if abs(sine) < 1.0e-13:
            return np.zeros_like(rapidity, dtype=float)
        denominator = np.cosh(2.0 * rapidity) - parity * np.cos(length * self.gamma)
        return parity * sine / (np.pi * denominator)

    def _a_kernel_energy_derivative(
        self, length: int, parity: float, rapidity: np.ndarray
    ) -> np.ndarray:
        """Derivative of e=-pi sin(gamma) a with respect to rapidity."""

        sine = float(np.sin(length * self.gamma))
        if abs(sine) < 1.0e-13:
            return np.zeros_like(rapidity, dtype=float)
        denominator = np.cosh(2.0 * rapidity) - parity * np.cos(length * self.gamma)
        return (
            2.0
            * parity
            * np.sin(self.gamma)
            * sine
            * np.sinh(2.0 * rapidity)
            / denominator**2
        )

    def _scattering_block(self, first: int, second: int, difference: np.ndarray) -> np.ndarray:
        n_first = int(self.string_lengths[first])
        n_second = int(self.string_lengths[second])
        parity = float(self.parities[first] * self.parities[second])
        lower = abs(n_first - n_second)
        result = np.zeros_like(difference, dtype=float)
        if n_first != n_second:
            result += self._a_kernel(lower, parity, difference)
        for length in range(lower + 2, n_first + n_second, 2):
            result += 2.0 * self._a_kernel(length, parity, difference)
        result += self._a_kernel(n_first + n_second, parity, difference)
        return result

    def bare_scattering_kernel(self) -> np.ndarray:
        """Return T_ab(lambda_i-lambda_j), without quadrature weights."""

        points = self.rapidity_points
        difference = self.rapidity[:, None] - self.rapidity[None, :]
        matrix = np.empty((self.ell * points, self.ell * points), dtype=float)
        for first in range(self.ell):
            row = slice(first * points, (first + 1) * points)
            for second in range(self.ell):
                column = slice(second * points, (second + 1) * points)
                matrix[row, column] = self._scattering_block(first, second, difference)
        return matrix

    def solve_stationary_state(self) -> StationaryState:
        """Solve densities, velocities, scattering dressing, and spin diffusion."""

        points = self.rapidity_points
        modes = self.ell * points
        repeated_fillings = np.repeat(self.fillings, points)
        repeated_signs = np.repeat(self.signs, points)

        bare_scattering = self.bare_scattering_kernel()
        convolution = bare_scattering * self.dlambda
        dressing_operator = np.diag(repeated_signs / repeated_fillings) + convolution

        bare_density = np.concatenate(
            [
                self._a_kernel(int(length), float(parity), self.rapidity)
                for length, parity in zip(self.string_lengths, self.parities, strict=True)
            ]
        )
        particle_density = solve(dressing_operator, bare_density, assume_a="gen")
        total_density = particle_density / repeated_fillings

        bare_energy_derivative = np.concatenate(
            [
                self._a_kernel_energy_derivative(
                    int(length), float(parity), self.rapidity
                )
                for length, parity in zip(self.string_lengths, self.parities, strict=True)
            ]
        )
        velocity_density = solve(
            dressing_operator,
            bare_energy_derivative / (2.0 * np.pi),
            assume_a="gen",
        )
        velocity = np.divide(
            velocity_density,
            particle_density,
            out=np.zeros_like(velocity_density),
            where=particle_density > 1.0e-300,
        )

        dressed_spin = np.zeros(modes, dtype=float)
        dressed_spin[-2 * points :] = self.ell / 2.0
        thermal_factor = 1.0 - repeated_fillings
        susceptibility_density = (
            particle_density * thermal_factor * dressed_spin**2
        )
        susceptibility = float(np.sum(susceptibility_density) * self.dlambda)
        susceptibility_weights = (
            susceptibility_density * self.dlambda / susceptibility
        )

        resolvent = np.eye(modes) + convolution * (
            repeated_fillings * repeated_signs
        )[None, :]
        dressed_scattering = solve(
            resolvent, bare_scattering, assume_a="gen", overwrite_a=True
        )

        spin_onsager = self._spin_onsager(
            particle_density=particle_density,
            total_density=total_density,
            velocity=velocity,
            dressed_spin=dressed_spin,
            dressed_scattering=dressed_scattering,
        )
        return StationaryState(
            ell=self.ell,
            rapidity=self.rapidity.copy(),
            quadrature_weight=self.dlambda,
            string_lengths=self.string_lengths.copy(),
            parities=self.parities.copy(),
            signs=self.signs.copy(),
            fillings=self.fillings.copy(),
            particle_density=particle_density,
            total_density=total_density,
            velocity=velocity,
            dressed_spin=dressed_spin,
            susceptibility=susceptibility,
            susceptibility_weights=susceptibility_weights,
            dressed_scattering=dressed_scattering,
            spin_onsager=spin_onsager,
        )

    def _spin_onsager(
        self,
        *,
        particle_density: np.ndarray,
        total_density: np.ndarray,
        velocity: np.ndarray,
        dressed_spin: np.ndarray,
        dressed_scattering: np.ndarray,
    ) -> float:
        points = self.rapidity_points
        repeated_fillings = np.repeat(self.fillings, points)
        repeated_signs = np.repeat(self.signs, points)
        measure = (
            particle_density * (1.0 - repeated_fillings) * self.dlambda
        )
        dressed_charge_density = dressed_spin / (repeated_signs * total_density)

        pair_integrand = np.abs(velocity[:, None] - velocity[None, :])
        pair_integrand *= dressed_scattering**2
        pair_integrand *= (
            dressed_charge_density[None, :] - dressed_charge_density[:, None]
        ) ** 2
        pair_integrand *= measure[:, None]
        pair_integrand *= measure[None, :]
        return float(0.5 * np.sum(pair_integrand))
