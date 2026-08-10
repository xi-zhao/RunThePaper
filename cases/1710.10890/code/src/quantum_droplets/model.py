from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from scipy.integrate import solve_bvp
from scipy.optimize import brentq


@dataclass(frozen=True)
class ScatteringModel:
    """Quadratic Lagrange representation of published scattering rows.

    The model is intentionally constructed from explicit table values supplied
    by the run configuration. It does not read the paper, source figures, or an
    author coupled-channel implementation.
    """

    magnetic_fields_gauss: tuple[float, ...]
    a11_bohr: tuple[float, ...]
    a22_bohr: tuple[float, ...]
    a12_bohr: tuple[float, ...]
    center_gauss: float = 56.45

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> "ScatteringModel":
        rows = config["scattering_table"]
        return cls(
            tuple(float(v) for v in rows["magnetic_fields_gauss"]),
            tuple(float(v) for v in rows["a11_bohr"]),
            tuple(float(v) for v in rows["a22_bohr"]),
            tuple(float(v) for v in rows["a12_bohr"]),
            float(rows.get("polynomial_center_gauss", 56.45)),
        )

    def _coefficients(self, values: tuple[float, ...]) -> np.ndarray:
        fields = np.asarray(self.magnetic_fields_gauss) - self.center_gauss
        return np.polyfit(fields, np.asarray(values), deg=2)

    def evaluate(self, magnetic_field_gauss: np.ndarray | float) -> dict[str, np.ndarray]:
        field = np.asarray(magnetic_field_gauss, dtype=float)
        x = field - self.center_gauss
        a11 = np.polyval(self._coefficients(self.a11_bohr), x)
        a22 = np.polyval(self._coefficients(self.a22_bohr), x)
        a12 = np.polyval(self._coefficients(self.a12_bohr), x)
        delta_a = a12 + np.sqrt(a11 * a22)
        ratio = np.sqrt(a22 / a11)
        return {
            "magnetic_field_gauss": field,
            "a11_bohr": a11,
            "a22_bohr": a22,
            "a12_bohr": a12,
            "delta_a_bohr": delta_a,
            "population_ratio": ratio,
        }

    def collapse_field(self, bracket: tuple[float, float]) -> float:
        return float(
            brentq(
                lambda field: float(self.evaluate(field)["delta_a_bohr"]),
                float(bracket[0]),
                float(bracket[1]),
                xtol=1e-12,
            )
        )

    def table_residual(self) -> float:
        values = self.evaluate(np.asarray(self.magnetic_fields_gauss))
        residuals = [
            np.max(np.abs(values["a11_bohr"] - np.asarray(self.a11_bohr))),
            np.max(np.abs(values["a22_bohr"] - np.asarray(self.a22_bohr))),
            np.max(np.abs(values["a12_bohr"] - np.asarray(self.a12_bohr))),
        ]
        return float(max(residuals))


def equilibrium_scales(
    a11_bohr: np.ndarray | float,
    a22_bohr: np.ndarray | float,
    a12_bohr: np.ndarray | float,
) -> dict[str, np.ndarray]:
    """Petrov equilibrium densities and length scale in Bohr units."""

    a11 = np.asarray(a11_bohr, dtype=float)
    a22 = np.asarray(a22_bohr, dtype=float)
    a12 = np.asarray(a12_bohr, dtype=float)
    delta_a = a12 + np.sqrt(a11 * a22)
    common = (
        25.0
        * np.pi
        / 1024.0
        * delta_a**2
        / (a11 * a22 * (np.sqrt(a11) + np.sqrt(a22)) ** 5)
    )
    n1_per_bohr3 = common / np.sqrt(a11)
    n2_per_bohr3 = common / np.sqrt(a22)
    xi_bohr = np.sqrt(
        384.0
        / (25.0 * np.pi**2)
        * a11
        * a22
        * (np.sqrt(a11) + np.sqrt(a22)) ** 6
        / np.abs(delta_a) ** 3
    )
    return {
        "delta_a_bohr": delta_a,
        "n1_per_bohr3": n1_per_bohr3,
        "n2_per_bohr3": n2_per_bohr3,
        "xi_bohr": xi_bohr,
    }


@dataclass(frozen=True)
class RadialProfile:
    chemical_potential: float
    radius: np.ndarray
    field: np.ndarray
    derivative: np.ndarray
    particle_number: float
    energy: float
    axis_rms: float
    central_field: float
    solver_status: int
    solver_message: str


def solve_radial_profile(
    chemical_potential: float,
    *,
    radius_max: float = 20.0,
    initial_nodes: int = 1200,
    tolerance: float = 1e-7,
    max_nodes: int = 30000,
) -> RadialProfile:
    """Solve the spherical dimensionless Petrov stationary equation."""

    mu = float(chemical_potential)
    radius = np.linspace(1e-5, float(radius_max), int(initial_nodes))
    amplitude = 0.65 if mu > -0.09 else 0.85
    guess_field = amplitude * np.exp(-((radius / 2.8) ** 2))
    guess_derivative = np.gradient(guess_field, radius)

    def equation(r: np.ndarray, state: np.ndarray) -> np.ndarray:
        field, derivative = state
        curvature = (
            -2.0 * derivative / r
            - 6.0 * field**3
            + 5.0 * field**4
            - 2.0 * mu * field
        )
        return np.vstack((derivative, curvature))

    def boundary(left: np.ndarray, right: np.ndarray) -> np.ndarray:
        return np.asarray([left[1], right[0]])

    solution = solve_bvp(
        equation,
        boundary,
        radius,
        np.vstack((guess_field, guess_derivative)),
        tol=float(tolerance),
        max_nodes=int(max_nodes),
    )
    if solution.status != 0:
        raise RuntimeError(f"radial BVP failed: {solution.message}")

    field, derivative = solution.sol(radius)
    volume_weight = 4.0 * np.pi * radius**2
    number = float(np.trapezoid(volume_weight * field**2, radius))
    energy = float(
        np.trapezoid(
            volume_weight
            * (0.5 * derivative**2 - 1.5 * field**4 + field**5),
            radius,
        )
    )
    mean_radius_sq = float(
        np.trapezoid(volume_weight * radius**2 * field**2, radius) / number
    )
    return RadialProfile(
        chemical_potential=mu,
        radius=radius,
        field=field,
        derivative=derivative,
        particle_number=number,
        energy=energy,
        axis_rms=float(np.sqrt(mean_radius_sq / 3.0)),
        central_field=float(field[0]),
        solver_status=int(solution.status),
        solver_message=str(solution.message),
    )


def solve_zero_energy_profile(
    bracket: tuple[float, float],
    **solver_options: Any,
) -> RadialProfile:
    cache: dict[float, RadialProfile] = {}

    def profile(mu: float) -> RadialProfile:
        key = round(float(mu), 12)
        if key not in cache:
            cache[key] = solve_radial_profile(float(mu), **solver_options)
        return cache[key]

    root = brentq(
        lambda mu: profile(float(mu)).energy,
        float(bracket[0]),
        float(bracket[1]),
        xtol=2e-9,
    )
    return profile(float(root))
