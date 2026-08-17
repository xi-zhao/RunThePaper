"""The two- and three-level models printed in the Letter."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class QuantumJumpModel:
    hamiltonian: np.ndarray
    jumps: tuple[np.ndarray, ...]
    counted_jump: int = 0


def two_level_model(omega: float = 1.0, kappa: float | None = None) -> QuantumJumpModel:
    if omega <= 0:
        raise ValueError("omega must be positive")
    if kappa is None:
        kappa = 4.0 * omega
    if kappa <= 0:
        raise ValueError("kappa must be positive")
    lowering = np.array([[0.0, 1.0], [0.0, 0.0]], dtype=np.complex128)
    hamiltonian = omega * (lowering + lowering.conj().T)
    jump = np.sqrt(kappa) * lowering
    return QuantumJumpModel(hamiltonian=hamiltonian, jumps=(jump,))


def two_level_exact(
    s: np.ndarray | float, omega: float = 1.0
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Eq. (5), activity and Mandel parameter at kappa=4 Omega."""

    s_values = np.asarray(s, dtype=np.float64)
    exponential = np.exp(-s_values / 3.0)
    theta = -2.0 * omega * (1.0 - exponential)
    activity = (2.0 * omega / 3.0) * exponential
    mandel = np.full_like(s_values, -2.0 / 3.0)
    return theta, activity, mandel


def three_level_model(
    omega_1: float = 1.0,
    omega_2: float = 0.1,
    kappa_1: float | None = None,
) -> QuantumJumpModel:
    if omega_1 <= 0 or omega_2 <= 0:
        raise ValueError("Rabi frequencies must be positive")
    if kappa_1 is None:
        kappa_1 = 4.0 * omega_1
    if kappa_1 <= 0:
        raise ValueError("kappa_1 must be positive")
    a1 = np.zeros((3, 3), dtype=np.complex128)
    a2 = np.zeros((3, 3), dtype=np.complex128)
    a1[0, 1] = 1.0
    a2[0, 2] = 1.0
    hamiltonian = omega_1 * (a1 + a1.conj().T) + omega_2 * (a2 + a2.conj().T)
    jump = np.sqrt(kappa_1) * a1
    return QuantumJumpModel(hamiltonian=hamiltonian, jumps=(jump,))
