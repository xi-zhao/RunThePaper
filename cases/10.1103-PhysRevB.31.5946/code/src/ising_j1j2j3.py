"""Exact identities and update primitives for the square-lattice J1-J2-J3 Ising model."""

from __future__ import annotations

from collections.abc import Mapping

import numpy as np


PHASES = ("c2x2", "saf2x1", "four_by_four", "four_by_two")


def ground_state_energies(r: float | np.ndarray, r_prime: float | np.ndarray) -> Mapping[str, np.ndarray]:
    """Return Eqs. (2a)-(2d) in units of |J_NN| per spin."""

    r_array = np.asarray(r, dtype=float)
    rp_array = np.asarray(r_prime, dtype=float)
    return {
        "c2x2": -2.0 + 2.0 * r_array + 2.0 * rp_array,
        "saf2x1": -2.0 * r_array + 2.0 * rp_array,
        "four_by_four": np.broadcast_to(-2.0 * rp_array, np.broadcast_shapes(r_array.shape, rp_array.shape)),
        "four_by_two": np.broadcast_to(-np.ones_like(r_array + rp_array), np.broadcast_shapes(r_array.shape, rp_array.shape)),
    }


def ground_state_labels(r: np.ndarray, r_prime: np.ndarray) -> np.ndarray:
    energies = ground_state_energies(r, r_prime)
    return np.argmin(np.stack([energies[phase] for phase in PHASES], axis=0), axis=0)


def ordered_pattern(name: str, size: int) -> np.ndarray:
    """Construct one periodic representative of each state in source Fig. 1."""

    if size <= 0 or size % 4:
        raise ValueError("size must be a positive multiple of four")
    x, y = np.indices((size, size))
    if name == "c2x2":
        exponent = x + y
    elif name == "saf2x1":
        exponent = x
    elif name == "four_by_four":
        exponent = x // 2 + y // 2
    elif name == "four_by_two":
        exponent = x // 2 + y
    else:
        raise ValueError(f"unknown ordered pattern: {name}")
    return np.where(exponent % 2, -1, 1).astype(np.int8)


def neighbor_field(spins: np.ndarray, *, r: float, r_prime: float) -> np.ndarray:
    """Interaction-weighted sum over four NN, four NNN, and four 3NN sites."""

    spins = np.asarray(spins)
    if spins.ndim != 2 or spins.shape[0] != spins.shape[1]:
        raise ValueError("spins must be a square two-dimensional array")
    nn = sum(np.roll(spins, shift, axis=axis) for axis in (0, 1) for shift in (-1, 1))
    nnn = sum(np.roll(np.roll(spins, dx, axis=0), dy, axis=1) for dx in (-1, 1) for dy in (-1, 1))
    third = sum(np.roll(spins, shift, axis=axis) for axis in (0, 1) for shift in (-2, 2))
    return nn + r * nnn + r_prime * third


def energy_per_spin(spins: np.ndarray, *, r: float, r_prime: float) -> float:
    """Hamiltonian per spin, with every undirected bond counted once."""

    spins = np.asarray(spins)
    nn_positive = np.roll(spins, -1, axis=0) + np.roll(spins, -1, axis=1)
    nnn_positive = np.roll(np.roll(spins, -1, axis=0), -1, axis=1) + np.roll(
        np.roll(spins, -1, axis=0), 1, axis=1
    )
    third_positive = np.roll(spins, -2, axis=0) + np.roll(spins, -2, axis=1)
    return float(np.mean(spins * (nn_positive + r * nnn_positive + r_prime * third_positive)))


def flip_delta_energy(spins: np.ndarray, x: int, y: int, *, r: float, r_prime: float) -> float:
    field = neighbor_field(spins, r=r, r_prime=r_prime)
    return float(-2.0 * spins[x, y] * field[x, y])


def sixteen_color(x: int, y: int) -> int:
    """Color supporting interaction-independent GPU sub-sweeps."""

    return 4 * (x % 4) + (y % 4)


def interaction_displacements() -> tuple[tuple[int, int], ...]:
    return (
        (1, 0), (-1, 0), (0, 1), (0, -1),
        (1, 1), (1, -1), (-1, 1), (-1, -1),
        (2, 0), (-2, 0), (0, 2), (0, -2),
    )


def hyperscaling_nu(alpha_over_nu: float, dimension: float = 2.0) -> float:
    """Solve d*nu=2-alpha with alpha=(alpha/nu)*nu."""

    denominator = dimension + alpha_over_nu
    if denominator <= 0.0:
        raise ValueError("dimension + alpha_over_nu must be positive")
    return 2.0 / denominator
