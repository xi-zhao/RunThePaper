"""Independent maximum-entropy continuation with an explicit alpha scan."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class MaxEntResult:
    omega: np.ndarray
    spectrum: np.ndarray
    selected_alpha: float
    chi_squared: float
    normalization: float
    candidates: tuple[dict[str, float], ...]


def _trapezoid_weights(grid: np.ndarray) -> np.ndarray:
    weights = np.empty_like(grid)
    weights[1:-1] = 0.5 * (grid[2:] - grid[:-2])
    weights[0] = 0.5 * (grid[1] - grid[0])
    weights[-1] = 0.5 * (grid[-1] - grid[-2])
    return weights


def maximum_entropy_continue(
    z_input: np.ndarray,
    green_input: np.ndarray,
    omega: np.ndarray,
    *,
    error: np.ndarray | float,
    alpha_grid: np.ndarray,
    default_model: np.ndarray | None = None,
    max_iterations: int = 1000,
) -> MaxEntResult:
    """Solve G(iw)=integral A(w)/(iw-w) dw with A>=0.

    The selected alpha is the discrepancy-principle candidate whose chi-square
    is closest to the number of real data components. This is deliberately
    explicit so a future paper-scale run can replace the assumed errors with
    measured CT-HYB covariance without changing the observable.
    """

    try:
        from scipy.optimize import minimize
    except ImportError as exc:  # pragma: no cover - required on production host
        raise RuntimeError("SciPy is required for independent MaxEnt") from exc

    z = np.asarray(z_input, dtype=np.complex128)
    green = np.asarray(green_input, dtype=np.complex128)
    energies = np.asarray(omega, dtype=float)
    alphas = np.asarray(alpha_grid, dtype=float)
    if z.ndim != 1 or green.shape != z.shape or energies.ndim != 1:
        raise ValueError("continuation inputs must be aligned vectors")
    if energies.size < 3 or np.any(np.diff(energies) <= 0.0):
        raise ValueError("omega must be a strictly increasing grid")
    if alphas.ndim != 1 or alphas.size < 2 or np.any(alphas <= 0.0):
        raise ValueError("alpha_grid must contain positive candidates")
    sigma = np.broadcast_to(np.asarray(error, dtype=float), green.shape)
    if np.any(sigma <= 0.0):
        raise ValueError("continuation errors must be positive")
    weights = _trapezoid_weights(energies)
    model = (
        np.full(energies.size, 1.0 / np.sum(weights))
        if default_model is None
        else np.asarray(default_model, dtype=float)
    )
    if model.shape != energies.shape or np.any(model <= 0.0):
        raise ValueError("default model must be positive and aligned")
    model = model / np.sum(weights * model)
    kernel = weights[None, :] / (z[:, None] - energies[None, :])
    design = np.vstack([kernel.real / sigma[:, None], kernel.imag / sigma[:, None]])
    observed = np.concatenate([green.real / sigma, green.imag / sigma])
    target_chi_squared = float(observed.size)
    candidates: list[dict[str, float]] = []
    solutions: list[np.ndarray] = []
    initial = np.zeros(energies.size, dtype=float)

    for alpha in alphas:

        def objective(log_ratio: np.ndarray) -> tuple[float, np.ndarray]:
            spectrum = model * np.exp(np.clip(log_ratio, -40.0, 40.0))
            residual = design @ spectrum - observed
            entropy = np.sum(weights * (spectrum - model - spectrum * log_ratio))
            normalization_error = np.sum(weights * spectrum) - 1.0
            value = (
                0.5 * float(residual @ residual)
                - float(alpha) * entropy
                + 1e4 * normalization_error**2
            )
            gradient_spectrum = (
                design.T @ residual
                + float(alpha) * weights * log_ratio
                + 2e4 * normalization_error * weights
            )
            return value, gradient_spectrum * spectrum

        optimized = minimize(
            objective,
            initial,
            jac=True,
            method="L-BFGS-B",
            bounds=[(-40.0, 40.0)] * energies.size,
            options={"maxiter": max_iterations, "ftol": 1e-12},
        )
        spectrum = model * np.exp(np.clip(optimized.x, -40.0, 40.0))
        spectrum /= np.sum(weights * spectrum)
        residual = design @ spectrum - observed
        chi_squared = float(residual @ residual)
        candidates.append(
            {
                "alpha": float(alpha),
                "chi_squared": chi_squared,
                "objective": float(optimized.fun),
                "converged": float(bool(optimized.success)),
            }
        )
        solutions.append(spectrum)
        initial = optimized.x
    selected = int(
        np.argmin([abs(row["chi_squared"] - target_chi_squared) for row in candidates])
    )
    spectrum = solutions[selected]
    return MaxEntResult(
        omega=energies,
        spectrum=spectrum,
        selected_alpha=candidates[selected]["alpha"],
        chi_squared=candidates[selected]["chi_squared"],
        normalization=float(np.sum(weights * spectrum)),
        candidates=tuple(candidates),
    )
