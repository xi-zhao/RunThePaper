"""Domain model for the compressed-spectrum convex relaxation.

The paper proves that the constrained probability optimum is controlled by a
single strictly concave dual function.  This module keeps that business rule in
one place: callers provide a spectrum problem and receive a fully checked
solution, without knowing how the scalar root is bracketed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import mpmath as mp


@dataclass(frozen=True)
class SpectrumProblem:
    """Finite spectrum and stable-Schmidt-rank relaxation parameters."""

    energies: tuple[mp.mpf, ...]
    stable_schmidt_lower_bounds: tuple[mp.mpf, ...]
    compression_bound: mp.mpf

    @classmethod
    def from_sequences(
        cls,
        energies: Sequence[int | float | str],
        lower_bounds: Sequence[int | float | str],
        compression_bound: int | float | str,
    ) -> "SpectrumProblem":
        return cls(
            tuple(mp.mpf(value) for value in energies),
            tuple(mp.mpf(value) for value in lower_bounds),
            mp.mpf(compression_bound),
        )

    def __post_init__(self) -> None:
        if not self.energies or len(self.energies) != len(self.stable_schmidt_lower_bounds):
            raise ValueError("energies and lower bounds must have the same nonzero length")
        if any(right < left for left, right in zip(self.energies, self.energies[1:])):
            raise ValueError("energies must be ordered")
        if any(value <= 0 for value in self.stable_schmidt_lower_bounds):
            raise ValueError("stable-Schmidt-rank lower bounds must be positive")
        if self.compression_bound <= 0:
            raise ValueError("compression bound must be positive")


@dataclass(frozen=True)
class FeasibilityStatus:
    feasible: bool
    strictly_above_ground: bool
    inverse_bound_sum: mp.mpf
    required_inverse_compression: mp.mpf
    ground_only_compression_value: mp.mpf


@dataclass(frozen=True)
class DualRoot:
    nu: mp.mpf
    stationarity_residual: mp.mpf
    iterations: int
    bracket_width: mp.mpf


@dataclass(frozen=True)
class SpectrumSolution:
    root: DualRoot
    probabilities: tuple[mp.mpf, ...]
    energy: mp.mpf
    dual_energy: mp.mpf
    normalization_residual: mp.mpf
    compression_residual: mp.mpf
    primal_dual_gap: mp.mpf


@dataclass(frozen=True)
class SupportMetrics:
    support_size: int
    harmonic_mean: mp.mpf
    harmonic_mean_over_compression: mp.mpf
    integer_lower_bound: int
    max_support_minus_one_inverse_sum: mp.mpf
    support_minus_one_feasible: bool


@dataclass(frozen=True)
class CoarseGrainedSolution:
    a1: mp.mpf
    a2: mp.mpf
    mu: mp.mpf
    ground_probability: mp.mpf


def inverse_bound_sum(problem: SpectrumProblem) -> mp.mpf:
    return mp.fsum(1 / value for value in problem.stable_schmidt_lower_bounds)


def compression_value(problem: SpectrumProblem, probabilities: Sequence[mp.mpf]) -> mp.mpf:
    if len(probabilities) != len(problem.energies):
        raise ValueError("probability vector length does not match the problem")
    return mp.fsum(
        mp.sqrt(probability / lower_bound)
        for probability, lower_bound in zip(probabilities, problem.stable_schmidt_lower_bounds)
    )


def feasibility_status(problem: SpectrumProblem) -> FeasibilityStatus:
    inverse_sum = inverse_bound_sum(problem)
    required = 1 / problem.compression_bound
    ground_value = 1 / mp.sqrt(problem.stable_schmidt_lower_bounds[0])
    return FeasibilityStatus(
        feasible=inverse_sum >= required,
        strictly_above_ground=ground_value < 1 / mp.sqrt(problem.compression_bound),
        inverse_bound_sum=inverse_sum,
        required_inverse_compression=required,
        ground_only_compression_value=ground_value,
    )


def dual_sum(problem: SpectrumProblem, nu: mp.mpf, power: int) -> mp.mpf:
    if power < 1:
        raise ValueError("dual sum power must be positive")
    if nu >= problem.energies[0]:
        raise ValueError("dual variable must satisfy nu < E1")
    return mp.fsum(
        1 / (lower_bound * (energy - nu) ** power)
        for energy, lower_bound in zip(problem.energies, problem.stable_schmidt_lower_bounds)
    )


def dual_derivative(problem: SpectrumProblem, nu: mp.mpf) -> mp.mpf:
    s1 = dual_sum(problem, nu, 1)
    s2 = dual_sum(problem, nu, 2)
    return 1 - s2 / (problem.compression_bound * s1**2)


def stationarity_residual(problem: SpectrumProblem, nu: mp.mpf) -> mp.mpf:
    s1 = dual_sum(problem, nu, 1)
    s2 = dual_sum(problem, nu, 2)
    return abs(s2 / problem.compression_bound - s1**2)


def solve_dual_root(
    problem: SpectrumProblem,
    *,
    decimal_digits: int = 100,
    interval_tolerance: str = "1e-70",
) -> DualRoot:
    """Solve the unique dual stationarity root with a proof-backed bracket."""

    if not feasibility_status(problem).feasible:
        raise ValueError("the compressed-spectrum problem is infeasible")

    with mp.workdps(decimal_digits):
        e1 = problem.energies[0]
        span = max(mp.mpf(1), problem.energies[-1] - e1)
        upper = e1 - mp.power(10, -min(30, decimal_digits // 3))
        lower = e1 - span

        # Proposition 2 proves h' is strictly decreasing.  Expand only the
        # negative endpoint until the unique root is bracketed.
        for _ in range(256):
            if dual_derivative(problem, lower) > 0:
                break
            span *= 2
            lower = e1 - span
        else:
            raise RuntimeError("failed to find the positive-derivative dual endpoint")

        if dual_derivative(problem, upper) >= 0:
            raise RuntimeError("nontriviality gate failed near the ground energy")

        tolerance = mp.mpf(interval_tolerance)
        iterations = 0
        while upper - lower > tolerance:
            middle = (lower + upper) / 2
            if dual_derivative(problem, middle) > 0:
                lower = middle
            else:
                upper = middle
            iterations += 1
            if iterations > 4096:
                raise RuntimeError("dual bisection exceeded its iteration limit")

        nu = (lower + upper) / 2
        return DualRoot(
            nu=+nu,
            stationarity_residual=+stationarity_residual(problem, nu),
            iterations=iterations,
            bracket_width=+(upper - lower),
        )


def solve_spectrum(
    problem: SpectrumProblem,
    *,
    decimal_digits: int = 100,
    interval_tolerance: str = "1e-70",
) -> SpectrumSolution:
    with mp.workdps(decimal_digits):
        root = solve_dual_root(
            problem,
            decimal_digits=decimal_digits,
            interval_tolerance=interval_tolerance,
        )
        weights = tuple(
            1 / (lower_bound * (energy - root.nu) ** 2)
            for energy, lower_bound in zip(problem.energies, problem.stable_schmidt_lower_bounds)
        )
        normalizer = mp.fsum(weights)
        probabilities = tuple(weight / normalizer for weight in weights)
        energy = mp.fsum(
            probability * level for probability, level in zip(probabilities, problem.energies)
        )
        dual_energy = root.nu + 1 / (
            problem.compression_bound * dual_sum(problem, root.nu, 1)
        )
        normalization_residual = abs(mp.fsum(probabilities) - 1)
        compression_residual = abs(
            compression_value(problem, probabilities) - 1 / mp.sqrt(problem.compression_bound)
        )
        return SpectrumSolution(
            root=root,
            probabilities=tuple(+value for value in probabilities),
            energy=+energy,
            dual_energy=+dual_energy,
            normalization_residual=+normalization_residual,
            compression_residual=+compression_residual,
            primal_dual_gap=+abs(energy - dual_energy),
        )


def support_metrics(problem: SpectrumProblem, probabilities: Sequence[mp.mpf]) -> SupportMetrics:
    if len(probabilities) != len(problem.energies):
        raise ValueError("probability vector length does not match the problem")
    support_size = sum(value > 0 for value in probabilities)
    harmonic_mean = len(problem.energies) / inverse_bound_sum(problem)
    scaled = harmonic_mean / problem.compression_bound
    inverse_weights = sorted(
        (1 / value for value in problem.stable_schmidt_lower_bounds),
        reverse=True,
    )
    max_support_minus_one_inverse_sum = mp.fsum(inverse_weights[:-1])
    return SupportMetrics(
        support_size=support_size,
        harmonic_mean=harmonic_mean,
        harmonic_mean_over_compression=scaled,
        integer_lower_bound=int(mp.ceil(scaled)),
        max_support_minus_one_inverse_sum=max_support_minus_one_inverse_sum,
        support_minus_one_feasible=(
            max_support_minus_one_inverse_sum >= 1 / problem.compression_bound
        ),
    )


def effective_log_slopes(
    energies: Sequence[mp.mpf],
    probabilities: Sequence[mp.mpf],
    *,
    first_index: int = 1,
) -> tuple[mp.mpf, ...]:
    """Return adjacent positive b values required by p=A*exp(-bE)."""

    if len(energies) != len(probabilities):
        raise ValueError("energies and probabilities must have the same length")
    if first_index < 0 or first_index >= len(energies) - 1:
        raise ValueError("first_index must leave at least two levels")
    return tuple(
        (mp.log(probabilities[index]) - mp.log(probabilities[index + 1]))
        / (energies[index + 1] - energies[index])
        for index in range(first_index, len(energies) - 1)
    )


def coarse_grained_solution(
    problem: SpectrumProblem,
    *,
    ground_levels: int,
) -> CoarseGrainedSolution:
    if ground_levels <= 0 or ground_levels >= len(problem.energies):
        raise ValueError("coarse graining requires two nonempty level groups")
    a1 = mp.fsum(1 / value for value in problem.stable_schmidt_lower_bounds[:ground_levels])
    a2 = mp.fsum(1 / value for value in problem.stable_schmidt_lower_bounds[ground_levels:])
    mu = (
        problem.compression_bound * a1 * (a1 + a2) - a1
    ) / a2
    if not 0 < mu < 1:
        raise ValueError("two-level parametrization requires 0 < mu < 1")
    probability = (a1 + mp.sqrt(mu) * a2) ** 2 / (
        (a1 + a2) * (a1 + mu * a2)
    )
    return CoarseGrainedSolution(a1=a1, a2=a2, mu=mu, ground_probability=probability)
