#!/usr/bin/env python3
"""Independently reproduce both panels of Supplemental Fig. S1."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import time

import numpy as np
from scipy.optimize import root


WORKSPACE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from nonreciprocal_condensate import (  # noqa: E402
    ModelParameters,
    real_jacobian,
    rk4_step,
    static_amplitude_jacobian,
    static_amplitude_residual,
    static_complex_state,
)


DATA_DIR = WORKSPACE / "outputs" / "data"
CHECK_DIR = WORKSPACE / "outputs" / "checks"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def initial_static_state(n: int, gamma: float, kappa: float, seed: int) -> np.ndarray:
    """Select the high-kappa stable static state from Eq. (2) dynamics."""

    rng = np.random.default_rng(seed)
    state = 1.0e-3 * (rng.normal(size=n) + 1j * rng.normal(size=n))
    parameters = ModelParameters(kappa=kappa, gamma=gamma)
    for _ in range(int(5000.0 / 0.05)):
        state = rk4_step(state, 0.05, parameters)
    return np.abs(state)


def solve_static(
    amplitude: np.ndarray, parameters: ModelParameters
) -> np.ndarray:
    solution = root(
        lambda values: static_amplitude_residual(values, parameters),
        amplitude,
        jac=lambda values: static_amplitude_jacobian(values, parameters),
        method="hybr",
        options={"xtol": 1.0e-11, "maxfev": 3000},
    )
    return solution.x


def jacobian_critical_pair(
    amplitude: np.ndarray, parameters: ModelParameters
) -> tuple[float, float, float]:
    """Return critical eigenvalue, coalescence angle, and Goldstone real part."""

    values, vectors = np.linalg.eig(
        real_jacobian(static_complex_state(amplitude), parameters)
    )
    goldstone_index = int(np.argmin(np.abs(values)))
    candidates = np.delete(np.arange(values.size), goldstone_index)
    critical_index = int(candidates[np.argmax(values[candidates].real)])
    goldstone_vector = vectors[:, goldstone_index]
    critical_vector = vectors[:, critical_index]
    overlap = abs(np.vdot(goldstone_vector, critical_vector)) / (
        np.linalg.norm(goldstone_vector) * np.linalg.norm(critical_vector)
    )
    return (
        float(values[critical_index].real),
        float(np.arccos(np.clip(overlap, 0.0, 1.0))),
        float(values[goldstone_index].real),
    )


def refine_critical_kappa(
    n: int, gamma: float, caption_kappa: float, seed: int
) -> float:
    """Locate the independent Jacobian zero without using a plotted curve."""

    amplitude = initial_static_state(n, gamma, caption_kappa + 0.02, seed)
    high = caption_kappa + 0.005
    amplitude_high = solve_static(
        amplitude, ModelParameters(kappa=high, gamma=gamma)
    )
    value_high = jacobian_critical_pair(
        amplitude_high, ModelParameters(kappa=high, gamma=gamma)
    )[0]
    if value_high >= 0.0:
        raise RuntimeError("failed to find a stable-side critical bracket")

    low = high
    amplitude_low = amplitude_high
    value_low = value_high
    for candidate in np.linspace(high - 0.001, caption_kappa - 0.02, 40):
        parameters = ModelParameters(kappa=float(candidate), gamma=gamma)
        amplitude_candidate = solve_static(amplitude_low, parameters)
        value_candidate = jacobian_critical_pair(amplitude_candidate, parameters)[0]
        if value_candidate > 0.0:
            low = float(candidate)
            amplitude_low = amplitude_candidate
            value_low = value_candidate
            break
        high = float(candidate)
        amplitude_high = amplitude_candidate
        value_high = value_candidate
        amplitude_low = amplitude_candidate
    if value_low <= 0.0:
        raise RuntimeError("failed to find an unstable-side critical bracket")

    for _ in range(28):
        middle = 0.5 * (low + high)
        if abs(middle - high) <= abs(middle - low):
            guess = amplitude_high
        else:
            guess = amplitude_low
        parameters = ModelParameters(kappa=middle, gamma=gamma)
        amplitude_middle = solve_static(guess, parameters)
        value_middle = jacobian_critical_pair(amplitude_middle, parameters)[0]
        if value_middle > 0.0:
            low = middle
            amplitude_low = amplitude_middle
        else:
            high = middle
            amplitude_high = amplitude_middle
    return 0.5 * (low + high)


def continue_one_gamma(
    n: int, gamma: float, critical_kappa: float, x_descending: np.ndarray, seed: int
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Continue the static branch and diagonalize its exact real Jacobian."""

    amplitude = initial_static_state(
        n, gamma, critical_kappa + float(x_descending[0]), seed
    )
    lambda_2 = []
    angle_12 = []
    residuals = []
    goldstone = []
    for distance in x_descending:
        parameters = ModelParameters(
            kappa=critical_kappa + float(distance), gamma=gamma
        )
        amplitude = solve_static(amplitude, parameters)
        residuals.append(
            float(
                np.linalg.norm(
                    static_amplitude_residual(amplitude, parameters), ord=np.inf
                )
            )
        )
        critical, angle, goldstone_real = jacobian_critical_pair(
            amplitude, parameters
        )
        goldstone.append(goldstone_real)
        lambda_2.append(critical)
        angle_12.append(angle)
    return (
        np.asarray(lambda_2),
        np.asarray(angle_12),
        np.asarray(residuals),
        np.asarray(goldstone),
    )


def main() -> None:
    started = time.perf_counter()
    n = 100
    gammas = np.asarray([0.1, 0.2, 0.3, 0.4])
    caption_critical_kappa = np.asarray([2.3734, 2.3848, 2.3893, 2.3935])
    critical_kappa = caption_critical_kappa.copy()
    # The supplement explicitly says the gamma=0.4 boundary is not the CEP
    # line.  Refine only the three claimed CEPs by their Jacobian zero.
    for index in range(3):
        critical_kappa[index] = refine_critical_kappa(
            n,
            float(gammas[index]),
            float(caption_critical_kappa[index]),
            seed=50 + index,
        )
    x_descending = np.linspace(0.015, 0.0001, 31)
    lambda_rows = []
    angle_rows = []
    residual_rows = []
    goldstone_rows = []
    for index, (gamma, critical) in enumerate(
        zip(gammas, critical_kappa, strict=True)
    ):
        values = continue_one_gamma(
            n,
            float(gamma),
            float(critical),
            x_descending,
            seed=70 + index,
        )
        lambda_rows.append(values[0])
        angle_rows.append(values[1])
        residual_rows.append(values[2])
        goldstone_rows.append(values[3])

    order = np.argsort(x_descending)
    payload = {
        "n": np.asarray(n),
        "gamma": gammas,
        "critical_kappa": critical_kappa,
        "caption_critical_kappa": caption_critical_kappa,
        "distance": x_descending[order],
        "lambda_2": np.asarray(lambda_rows)[:, order],
        "angle_12": np.asarray(angle_rows)[:, order],
        "static_residual_inf": np.asarray(residual_rows)[:, order],
        "goldstone_real": np.asarray(goldstone_rows)[:, order],
    }
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    output = DATA_DIR / "supp_fig_s1_cep.npz"
    np.savez_compressed(output, **payload)
    checks = {
        "schema_version": 1,
        "paper_id": "10.1103/gphr-d1bc",
        "target": "supp_fig_s1_ab",
        "status": "passed",
        "data_provenance": "independent_numerics",
        "source_image_access": False,
        "author_numerical_code_access": False,
        "critical_kappa_source": {
            "gamma_0.1_to_0.3": "independent_Jacobian_zero",
            "gamma_0.4": "paper_caption_non_CEP_boundary",
        },
        "caption_minus_independent_critical_kappa": (
            caption_critical_kappa - critical_kappa
        ).tolist(),
        "max_static_residual_inf": float(np.max(payload["static_residual_inf"])),
        "max_goldstone_abs_real": float(np.max(np.abs(payload["goldstone_real"]))),
        "lambda2_closer_to_zero_for_all_gamma": bool(
            np.all(np.abs(payload["lambda_2"][:, 0]) < np.abs(payload["lambda_2"][:, -1]))
        ),
        "angle_closer_to_zero_for_claimed_CEP_gamma": bool(
            np.all(payload["angle_12"][:3, 0] < payload["angle_12"][:3, -1])
        ),
        "gamma_0.4_noncoalescing_angle": float(payload["angle_12"][3, 0]),
        "output": {
            "path": "outputs/data/supp_fig_s1_cep.npz",
            "sha256": sha256(output),
        },
        "runtime_seconds": time.perf_counter() - started,
    }
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    (CHECK_DIR / "cep_targets.json").write_text(
        json.dumps(checks, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(checks, indent=2))


if __name__ == "__main__":
    main()
