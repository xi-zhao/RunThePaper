"""Batched Torch backend for the verified four-dimensional Z_N kernel.

The implementation intentionally mirrors ``zn_lgt.py``.  A batch dimension
holds independent Markov chains so a GPU advances many lattices at once.  This
changes neither a chain's proposal distribution nor its Metropolis ratio, but
the final provenance must state that the paper's total sample count was split
over multiple independently thermalized chains.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations, product
import math

import torch


DIM = 4
PLAQUETTES = tuple(combinations(range(DIM), 2))
CUBES = tuple(combinations(range(DIM), 3))


@dataclass(frozen=True)
class TorchModel:
    n: int
    beta: float
    beta_tilde: float = 0.0
    monopole_mu: float = 0.0


def _forward(array: torch.Tensor, axis: int) -> torch.Tensor:
    return torch.roll(array, -1, dims=axis + 1)


def _backward(array: torch.Tensor, axis: int) -> torch.Tensor:
    return torch.roll(array, 1, dims=axis + 1)


def principal_flux(raw_flux: torch.Tensor, n: int) -> torch.Tensor:
    residue = torch.remainder(raw_flux, n)
    return torch.where(residue > n / 2, residue - n, residue).to(torch.int16)


def plaquette_flux(
    links: torch.Tensor, n: int, mu: int, nu: int
) -> torch.Tensor:
    if not 0 <= mu < nu < DIM:
        raise ValueError("plaquette axes must satisfy 0 <= mu < nu < 4")
    raw = (
        links[:, mu]
        + _forward(links[:, nu], mu)
        - _forward(links[:, mu], nu)
        - links[:, nu]
    )
    return principal_flux(raw, n)


def all_plaquette_fluxes(
    links: torch.Tensor, n: int
) -> dict[tuple[int, int], torch.Tensor]:
    return {axes: plaquette_flux(links, n, *axes) for axes in PLAQUETTES}


def cube_charge(
    fluxes: dict[tuple[int, int], torch.Tensor], n: int, a: int, b: int, c: int
) -> torch.Tensor:
    df = (
        _forward(fluxes[(b, c)], a)
        - fluxes[(b, c)]
        - _forward(fluxes[(a, c)], b)
        + fluxes[(a, c)]
        + _forward(fluxes[(a, b)], c)
        - fluxes[(a, b)]
    )
    # Divisibility is guaranteed by the discrete Bianchi identity and covered
    # by CPU cross-checks. A device-to-host assertion here would synchronize the
    # GPU several times per colour update and destroy throughput.
    return (df // n).to(torch.int16)


def all_cube_charges(
    fluxes: dict[tuple[int, int], torch.Tensor], n: int
) -> dict[tuple[int, int, int], torch.Tensor]:
    return {axes: cube_charge(fluxes, n, *axes) for axes in CUBES}


def action_densities(
    links: torch.Tensor, model: TorchModel
) -> tuple[
    dict[tuple[int, int], torch.Tensor],
    dict[tuple[int, int, int], torch.Tensor],
]:
    fluxes = all_plaquette_fluxes(links, model.n)
    angle = 2.0 * math.pi / model.n
    plaquette_terms = {
        axes: -model.beta * torch.cos(angle * flux.to(torch.float32))
        - model.beta_tilde * torch.cos(2.0 * angle * flux.to(torch.float32))
        for axes, flux in fluxes.items()
    }
    cube_terms: dict[tuple[int, int, int], torch.Tensor] = {}
    if model.monopole_mu != 0.0:
        cube_terms = {
            axes: model.monopole_mu * charge.to(torch.float32) ** 2
            for axes, charge in all_cube_charges(fluxes, model.n).items()
        }
    return plaquette_terms, cube_terms


def total_action(links: torch.Tensor, model: TorchModel) -> torch.Tensor:
    plaquette_terms, cube_terms = action_densities(links, model)
    terms = [*plaquette_terms.values(), *cube_terms.values()]
    return sum(term.flatten(1).sum(1) for term in terms)


def colour_masks(
    length: int, direction: int, monopole_term: bool, device: torch.device
) -> list[torch.Tensor]:
    coordinates = torch.meshgrid(
        *(torch.arange(length, device=device) for _ in range(DIM)), indexing="ij"
    )
    if not monopole_term:
        parity_sum = sum(coordinates)
        return [parity_sum % 2 == parity for parity in (0, 1)]
    transverse = [axis for axis in range(DIM) if axis != direction]
    return [
        torch.stack(
            [coordinates[axis] % 2 == bit for axis, bit in zip(transverse, bits)]
        ).all(0)
        for bits in product((0, 1), repeat=DIM - 1)
    ]


def local_action_delta(
    old_plaquettes: dict[tuple[int, int], torch.Tensor],
    new_plaquettes: dict[tuple[int, int], torch.Tensor],
    old_cubes: dict[tuple[int, int, int], torch.Tensor],
    new_cubes: dict[tuple[int, int, int], torch.Tensor],
    direction: int,
) -> torch.Tensor:
    delta = torch.zeros_like(next(iter(old_plaquettes.values())))
    for transverse in range(DIM):
        if transverse == direction:
            continue
        axes = tuple(sorted((direction, transverse)))
        term_delta = new_plaquettes[axes] - old_plaquettes[axes]
        delta = delta + term_delta + _backward(term_delta, transverse)
    for other_axes in combinations(
        [axis for axis in range(DIM) if axis != direction], 2
    ):
        cube_axes = tuple(sorted((direction, *other_axes)))
        if cube_axes not in old_cubes:
            continue
        term_delta = new_cubes[cube_axes] - old_cubes[cube_axes]
        a, b = other_axes
        delta = (
            delta
            + term_delta
            + _backward(term_delta, a)
            + _backward(term_delta, b)
            + _backward(_backward(term_delta, a), b)
        )
    return delta


class BatchedMetropolisSampler:
    def __init__(
        self,
        *,
        batch_size: int,
        length: int,
        model: TorchModel,
        seed: int,
        device: str,
        start: str = "hot",
    ) -> None:
        if length < 2 or length % 2:
            raise ValueError("length must be even and at least 2")
        if batch_size < 1:
            raise ValueError("batch_size must be positive")
        self.batch_size = batch_size
        self.length = length
        self.model = model
        self.device = torch.device(device)
        self.generator = torch.Generator(device=self.device).manual_seed(seed)
        shape = (batch_size, DIM) + (length,) * DIM
        if start == "hot":
            self.links = torch.randint(
                model.n,
                shape,
                dtype=torch.int16,
                device=self.device,
                generator=self.generator,
            )
        elif start == "cold":
            self.links = torch.zeros(shape, dtype=torch.int16, device=self.device)
        else:
            raise ValueError("start must be 'hot' or 'cold'")
        self.proposed = 0
        self._accepted_device = torch.zeros((), dtype=torch.int64, device=self.device)
        self._masks = {
            direction: colour_masks(
                length,
                direction,
                model.monopole_mu != 0.0,
                self.device,
            )
            for direction in range(DIM)
        }

    @property
    def acceptance_rate(self) -> float:
        return self.accepted / self.proposed if self.proposed else 0.0

    @property
    def accepted(self) -> int:
        return int(self._accepted_device.item())

    @accepted.setter
    def accepted(self, value: int) -> None:
        self._accepted_device.fill_(int(value))

    @torch.no_grad()
    def _update_colour(self, direction: int, mask: torch.Tensor) -> None:
        old_p, old_c = action_densities(self.links, self.model)
        trial = torch.randint(
            self.model.n,
            (self.batch_size,) + mask.shape,
            dtype=torch.int16,
            device=self.device,
            generator=self.generator,
        )
        proposal = self.links.clone()
        batch_mask = mask.unsqueeze(0).expand(self.batch_size, *mask.shape)
        proposal[:, direction] = torch.where(
            batch_mask, trial, proposal[:, direction]
        )
        new_p, new_c = action_densities(proposal, self.model)
        delta = local_action_delta(old_p, new_p, old_c, new_c, direction)
        random = torch.rand(
            delta.shape, device=self.device, generator=self.generator
        )
        accept = batch_mask & (random < torch.exp(-torch.clamp_min(delta, 0.0)))
        self.links[:, direction] = torch.where(
            accept, trial, self.links[:, direction]
        )
        self.proposed += self.batch_size * int(mask.numel())
        self._accepted_device += accept.sum()

    @torch.no_grad()
    def sweep(self, count: int = 1) -> None:
        for _ in range(count):
            for direction in range(DIM):
                for mask in self._masks[direction]:
                    self._update_colour(direction, mask)

    @torch.no_grad()
    def polyakov_loop(self, time_direction: int = 0) -> torch.Tensor:
        winding = self.links[:, time_direction].sum(dim=time_direction + 1)
        phase = torch.polar(
            torch.ones_like(winding, dtype=torch.float32),
            2.0 * torch.pi * winding.to(torch.float32) / self.model.n,
        )
        return phase.flatten(1).mean(1)

    @torch.no_grad()
    def action(self) -> torch.Tensor:
        return total_action(self.links, self.model)

    @torch.no_grad()
    def defect_densities(self) -> tuple[torch.Tensor, torch.Tensor]:
        fluxes = all_plaquette_fluxes(self.links, self.model.n)
        vortices = torch.stack(
            [(flux != 0).flatten(1).to(torch.float32).mean(1) for flux in fluxes.values()]
        ).mean(0)
        charges = all_cube_charges(fluxes, self.model.n)
        monopoles = torch.stack(
            [(charge != 0).flatten(1).to(torch.float32).mean(1) for charge in charges.values()]
        ).mean(0)
        return vortices, monopoles
