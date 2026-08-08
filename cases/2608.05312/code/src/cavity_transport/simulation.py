"""Prepared-realization simulation service.

The expensive coherent and dissipative pieces are prepared once per disorder
sample.  Rate scans only combine those linear pieces, making the state changes
explicit and ensuring that compared mechanisms share identical disorder.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Iterable

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy.sparse import csc_matrix

from .liouvillian import (
    dissipator_superoperator,
    hamiltonian_superoperator,
    propagate_final,
    propagate_times,
)
from .model import (
    ChannelRates,
    TransportModel,
    build_hamiltonian,
    build_unit_jump_families,
    initial_density,
    sample_standard_disorder,
)
from .observables import ManifoldProjectors, manifold_projectors, population_series, populations


@lru_cache(maxsize=128)
def _shared_dissipators(model: TransportModel) -> dict[str, csc_matrix]:
    """Cache geometry-only dissipators across disorder realizations."""

    unit_families = build_unit_jump_families(model)
    return {
        name: dissipator_superoperator(jumps, model.dimension)
        for name, jumps in unit_families.items()
    }


@dataclass(frozen=True)
class PreparedTransport:
    model: TransportModel
    seed: int
    standard_disorder: NDArray[np.float64]
    hamiltonian: NDArray[np.complex128]
    projectors: ManifoldProjectors
    rho0: NDArray[np.complex128]
    coherent: csc_matrix
    dissipators: dict[str, csc_matrix]

    @classmethod
    def from_seed(cls, model: TransportModel, seed: int) -> "PreparedTransport":
        disorder = sample_standard_disorder(model, seed)
        hamiltonian = build_hamiltonian(model, disorder)
        dissipators = _shared_dissipators(model)
        return cls(
            model=model,
            seed=seed,
            standard_disorder=disorder,
            hamiltonian=hamiltonian,
            projectors=manifold_projectors(hamiltonian),
            rho0=initial_density(model),
            coherent=hamiltonian_superoperator(hamiltonian),
            dissipators=dissipators,
        )

    def generator(self, rates: ChannelRates) -> csc_matrix:
        return csc_matrix(
            self.coherent
            + rates.gamma_rec * self.dissipators["rec"]
            + rates.gamma_abs * self.dissipators["abs"]
            + rates.gamma_deph * self.dissipators["deph"]
            + rates.gamma_lead * self.dissipators["lead"]
        )

    def final_density(self, rates: ChannelRates, final_time: float) -> NDArray[np.complex128]:
        return propagate_final(self.generator(rates), self.rho0, final_time)

    def final_populations(self, rates: ChannelRates, final_time: float) -> dict[str, float]:
        return populations(self.final_density(rates, final_time), self.projectors)

    def population_dynamics(
        self,
        rates: ChannelRates,
        times: ArrayLike,
    ) -> dict[str, NDArray[np.float64]]:
        rhos = propagate_times(self.generator(rates), self.rho0, times)
        return population_series(rhos, self.projectors)


def prepare_ensemble(
    model: TransportModel,
    seeds: Iterable[int],
) -> list[PreparedTransport]:
    return [PreparedTransport.from_seed(model, int(seed)) for seed in seeds]


def ensemble_final_populations(
    ensemble: list[PreparedTransport],
    rates: ChannelRates,
    final_time: float,
) -> dict[str, NDArray[np.float64] | dict[str, float]]:
    if not ensemble:
        raise ValueError("ensemble must not be empty")
    sample_rows = [sample.final_populations(rates, final_time) for sample in ensemble]
    names = sample_rows[0].keys()
    samples = {
        name: np.asarray([row[name] for row in sample_rows], dtype=float) for name in names
    }
    mean = {name: float(np.mean(values)) for name, values in samples.items()}
    sem = {
        name: float(np.std(values, ddof=1) / np.sqrt(len(values)))
        if len(values) > 1
        else 0.0
        for name, values in samples.items()
    }
    return {"samples": samples, "mean": mean, "sem": sem}


def ensemble_population_dynamics(
    ensemble: list[PreparedTransport],
    rates: ChannelRates,
    times: ArrayLike,
) -> dict[str, dict[str, NDArray[np.float64]]]:
    if not ensemble:
        raise ValueError("ensemble must not be empty")
    runs = [sample.population_dynamics(rates, times) for sample in ensemble]
    names = runs[0].keys()
    stacked = {
        name: np.stack([run[name] for run in runs], axis=0) for name in names
    }
    mean = {name: np.mean(values, axis=0) for name, values in stacked.items()}
    sem = {
        name: np.std(values, axis=0, ddof=1) / np.sqrt(values.shape[0])
        if values.shape[0] > 1
        else np.zeros(values.shape[1], dtype=float)
        for name, values in stacked.items()
    }
    return {"samples": stacked, "mean": mean, "sem": sem}
