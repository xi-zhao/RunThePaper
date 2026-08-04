"""Four-dimensional :math:`Z_N` lattice-gauge Monte Carlo primitives.

The implementation follows the paper's single-link Metropolis kernel, but
groups non-interacting links into exact colour classes.  Links in one colour
never share a plaquette; when the monopole term is active they also never share
a 3-cell.  Every proposal therefore has the same local Metropolis acceptance
ratio as a sequential update, while NumPy can evaluate a colour in parallel.

This module keeps the scientific objects explicit:

* integer link fields ``s[mu, x0, x1, x2, x3]`` in ``Z_N``;
* oriented principal plaquette fluxes ``f``;
* integer monopole charges ``dm`` on 3-cells;
* Wilson, extended-Z4, and monopole-suppressed actions.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations, product

import numpy as np


DIM = 4
PLAQUETTES = tuple(combinations(range(DIM), 2))
CUBES = tuple(combinations(range(DIM), 3))


@dataclass(frozen=True)
class Model:
    n: int
    beta: float
    beta_tilde: float = 0.0
    monopole_mu: float = 0.0

    def __post_init__(self) -> None:
        if self.n < 2:
            raise ValueError("n must be at least 2")


def _forward(array: np.ndarray, axis: int) -> np.ndarray:
    """Return ``array[x + e_axis]`` with periodic boundaries."""

    return np.roll(array, -1, axis=axis)


def _backward(array: np.ndarray, axis: int) -> np.ndarray:
    """Return ``array[x - e_axis]`` with periodic boundaries."""

    return np.roll(array, 1, axis=axis)


def principal_flux(raw_flux: np.ndarray, n: int) -> np.ndarray:
    """Map integer flux to the paper's unique interval ``-N/2 < f <= N/2``."""

    residue = np.mod(raw_flux, n)
    return np.where(residue > n / 2, residue - n, residue).astype(np.int16)


def plaquette_flux(links: np.ndarray, n: int, mu: int, nu: int) -> np.ndarray:
    """Oriented principal flux on the ``(mu, nu)`` plaquette, ``mu < nu``."""

    if not 0 <= mu < nu < DIM:
        raise ValueError("plaquette axes must satisfy 0 <= mu < nu < 4")
    raw = (
        links[mu]
        + _forward(links[nu], mu)
        - _forward(links[mu], nu)
        - links[nu]
    )
    return principal_flux(raw, n)


def all_plaquette_fluxes(links: np.ndarray, n: int) -> dict[tuple[int, int], np.ndarray]:
    return {axes: plaquette_flux(links, n, *axes) for axes in PLAQUETTES}


def cube_charge(
    fluxes: dict[tuple[int, int], np.ndarray], n: int, a: int, b: int, c: int
) -> np.ndarray:
    """Integer monopole charge ``dm`` on an oriented ``(a,b,c)`` 3-cell."""

    if not 0 <= a < b < c < DIM:
        raise ValueError("cube axes must satisfy 0 <= a < b < c < 4")
    df = (
        _forward(fluxes[(b, c)], a)
        - fluxes[(b, c)]
        - _forward(fluxes[(a, c)], b)
        + fluxes[(a, c)]
        + _forward(fluxes[(a, b)], c)
        - fluxes[(a, b)]
    )
    if np.any(np.mod(df, n) != 0):
        raise AssertionError("discrete Bianchi identity violated: df is not divisible by N")
    return (df // n).astype(np.int16)


def all_cube_charges(
    fluxes: dict[tuple[int, int], np.ndarray], n: int
) -> dict[tuple[int, int, int], np.ndarray]:
    return {axes: cube_charge(fluxes, n, *axes) for axes in CUBES}


def action_densities(
    links: np.ndarray, model: Model
) -> tuple[dict[tuple[int, int], np.ndarray], dict[tuple[int, int, int], np.ndarray]]:
    """Return per-plaquette and per-cube action terms."""

    fluxes = all_plaquette_fluxes(links, model.n)
    angle = 2.0 * np.pi / model.n
    plaquette_terms = {
        axes: -model.beta * np.cos(angle * flux)
        - model.beta_tilde * np.cos(2.0 * angle * flux)
        for axes, flux in fluxes.items()
    }
    cube_terms: dict[tuple[int, int, int], np.ndarray] = {}
    if model.monopole_mu != 0.0:
        cube_terms = {
            axes: model.monopole_mu * charge.astype(np.float64) ** 2
            for axes, charge in all_cube_charges(fluxes, model.n).items()
        }
    return plaquette_terms, cube_terms


def total_action(links: np.ndarray, model: Model) -> float:
    plaquette_terms, cube_terms = action_densities(links, model)
    return float(sum(np.sum(value) for value in (*plaquette_terms.values(), *cube_terms.values())))


def _colour_masks(length: int, direction: int, monopole_term: bool) -> list[np.ndarray]:
    coordinates = np.indices((length,) * DIM, sparse=False)
    if not monopole_term:
        return [np.mod(np.sum(coordinates, axis=0), 2) == parity for parity in (0, 1)]

    transverse = [axis for axis in range(DIM) if axis != direction]
    return [
        np.logical_and.reduce([coordinates[axis] % 2 == bit for axis, bit in zip(transverse, bits)])
        for bits in product((0, 1), repeat=DIM - 1)
    ]


def local_action_delta(
    old_plaquettes: dict[tuple[int, int], np.ndarray],
    new_plaquettes: dict[tuple[int, int], np.ndarray],
    old_cubes: dict[tuple[int, int, int], np.ndarray],
    new_cubes: dict[tuple[int, int, int], np.ndarray],
    direction: int,
) -> np.ndarray:
    """Sum action changes of every term incident on each link in ``direction``."""

    shape = next(iter(old_plaquettes.values())).shape
    delta = np.zeros(shape, dtype=np.float64)
    for transverse in range(DIM):
        if transverse == direction:
            continue
        axes = tuple(sorted((direction, transverse)))
        term_delta = new_plaquettes[axes] - old_plaquettes[axes]
        delta += term_delta + _backward(term_delta, transverse)

    for other_axes in combinations([axis for axis in range(DIM) if axis != direction], 2):
        cube_axes = tuple(sorted((direction, *other_axes)))
        if cube_axes not in old_cubes:
            continue
        term_delta = new_cubes[cube_axes] - old_cubes[cube_axes]
        a, b = other_axes
        delta += term_delta
        delta += _backward(term_delta, a)
        delta += _backward(term_delta, b)
        delta += _backward(_backward(term_delta, a), b)
    return delta


class MetropolisSampler:
    """Exact coloured single-link Metropolis sampler on a periodic 4-torus."""

    def __init__(
        self,
        length: int,
        model: Model,
        seed: int,
        start: str = "hot",
    ) -> None:
        if length < 2:
            raise ValueError("length must be at least 2")
        if length % 2:
            raise ValueError("coloured periodic updates require an even lattice length")
        self.length = int(length)
        self.model = model
        self.rng = np.random.default_rng(seed)
        shape = (DIM,) + (self.length,) * DIM
        if start == "hot":
            self.links = self.rng.integers(0, model.n, size=shape, dtype=np.int16)
        elif start == "cold":
            self.links = np.zeros(shape, dtype=np.int16)
        else:
            raise ValueError("start must be 'hot' or 'cold'")
        self.proposed = 0
        self.accepted = 0

    @property
    def acceptance_rate(self) -> float:
        return self.accepted / self.proposed if self.proposed else 0.0

    def _update_colour(self, direction: int, mask: np.ndarray) -> None:
        old_p, old_c = action_densities(self.links, self.model)
        trial_values = self.rng.integers(0, self.model.n, size=mask.shape, dtype=np.int16)
        proposal = self.links.copy()
        proposal[direction][mask] = trial_values[mask]
        new_p, new_c = action_densities(proposal, self.model)
        delta = local_action_delta(old_p, new_p, old_c, new_c, direction)
        accept = mask & (self.rng.random(mask.shape) < np.exp(-np.maximum(delta, 0.0)))
        self.links[direction][accept] = trial_values[accept]
        self.proposed += int(np.count_nonzero(mask))
        self.accepted += int(np.count_nonzero(accept))

    def sweep(self, count: int = 1) -> None:
        for _ in range(count):
            for direction in range(DIM):
                masks = _colour_masks(
                    self.length,
                    direction,
                    monopole_term=self.model.monopole_mu != 0.0,
                )
                for mask in masks:
                    self._update_colour(direction, mask)

    def polyakov_loop(self, time_direction: int = 0) -> complex:
        winding = np.sum(self.links[time_direction], axis=time_direction)
        phases = np.exp(2j * np.pi * winding / self.model.n)
        return complex(np.mean(phases))

    def vortex_density(self) -> float:
        fluxes = all_plaquette_fluxes(self.links, self.model.n)
        nonzero = sum(np.count_nonzero(flux) for flux in fluxes.values())
        total = sum(flux.size for flux in fluxes.values())
        return nonzero / total

    def monopole_density(self) -> float:
        fluxes = all_plaquette_fluxes(self.links, self.model.n)
        charges = all_cube_charges(fluxes, self.model.n)
        nonzero = sum(np.count_nonzero(charge) for charge in charges.values())
        total = sum(charge.size for charge in charges.values())
        return nonzero / total

    def action(self) -> float:
        return total_action(self.links, self.model)


def symmetry_augment_polyakov(polyakov: np.ndarray, n: int) -> np.ndarray:
    """Apply the supplement's complete :math:`Z_N` orbit augmentation.

    The paper augments every measured smeared Polyakov loop by all global
    ``Z_N`` rotations before plotting a phase histogram. This makes the sample
    mean exactly zero, up to round-off, without changing any radius. Keeping
    the operation explicit separates the plotting convention from raw-chain
    sector tunnelling.
    """

    values = np.asarray(polyakov, dtype=np.complex128)
    roots = np.exp(2j * np.pi * np.arange(n) / n)
    return (values[:, None] * roots[None, :]).reshape(-1)


def coulomb_correlator_ratio(n: int, length: int) -> float:
    """Paper Eq. (8) finite-torus prediction ``C(n)/C(n+1)``.

    The unknown normalization cancels.  ``n+1`` must remain strictly inside
    the periodic interval so both image terms are finite.
    """

    if not 1 <= n < length - 1:
        raise ValueError("require 1 <= n < length - 1")

    def shape(distance: int) -> float:
        return distance**-4 + (length - distance) ** -4

    return shape(n) / shape(n + 1)
