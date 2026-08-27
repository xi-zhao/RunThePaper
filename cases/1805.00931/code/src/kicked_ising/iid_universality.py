"""Distribution-agnostic dual-transfer checks for IID longitudinal fields."""

from __future__ import annotations

import numpy as np

from .model import computational_spins, floquet_matrix, transfer_multiplicities


def centered_characteristic_function(
    differences: np.ndarray,
    *,
    distribution: str,
    standard_deviation: float,
) -> np.ndarray:
    """Evaluate the centered one-site characteristic function.

    All parameterizations use the same standard deviation, so the comparison
    changes the IID distribution rather than its width.  No sampled author
    fields or source curves are inputs.
    """

    q = np.asarray(differences, dtype=float)
    sigma = float(standard_deviation)
    if sigma <= 0.0:
        raise ValueError("standard_deviation must be positive")
    if distribution == "gaussian":
        return np.exp(-0.5 * sigma**2 * q**2)
    if distribution == "uniform":
        half_width = np.sqrt(3.0) * sigma
        return np.sinc(half_width * q / np.pi)
    if distribution == "symmetric_binary":
        return np.cos(sigma * q)
    if distribution == "laplace":
        scale = sigma / np.sqrt(2.0)
        return 1.0 / (1.0 + scale**2 * q**2)
    raise ValueError(f"unsupported IID distribution: {distribution}")


def iid_transfer_spectrum(
    time: int,
    *,
    h_mean: float,
    standard_deviation: float,
    distribution: str,
) -> dict[str, float | int]:
    """Diagonalize the small-time transfer operator for one IID law."""

    magnetization = np.sum(computational_spins(time), axis=1)
    differences = magnetization[:, None] - magnetization[None, :]
    dephasing = centered_characteristic_function(
        differences,
        distribution=distribution,
        standard_deviation=standard_deviation,
    )
    dual = floquet_matrix(time, np.full(time, h_mean, dtype=float))
    transfer = np.kron(dual, dual.conj()) @ np.diag(dephasing.ravel())
    eigenvalues = np.linalg.eigvals(transfer)
    moduli = np.abs(eigenvalues)
    unit_mask = np.abs(moduli - 1.0) <= 1e-8
    expected_plus, expected_minus = transfer_multiplicities(time)
    subunit = moduli[~unit_mask]
    return {
        "time": time,
        "unit_modulus_count": int(np.count_nonzero(unit_mask)),
        "expected_unit_modulus_count": int(expected_plus + expected_minus),
        "maximum_subunit_modulus": float(np.max(subunit)) if subunit.size else 0.0,
        "characteristic_at_zero_error": float(
            abs(
                centered_characteristic_function(
                    np.asarray([0.0]),
                    distribution=distribution,
                    standard_deviation=standard_deviation,
                )[0]
                - 1.0
            )
        ),
    }
