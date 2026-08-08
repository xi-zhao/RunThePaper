"""Domain model for cavity-coupled single-excitation transport."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
from numpy.typing import NDArray
from scipy.sparse import csc_matrix


DrainKind = Literal["cavity", "site_n"]


@dataclass(frozen=True)
class TransportModel:
    """Coherent geometry and immutable preparation rules for one experiment.

    Energies and rates are expressed in meV, while time is in hbar/meV.  The
    common energy origin is set by ``cavity_energy=0``.
    """

    n_sites: int
    g: float = 1.5
    t_mean: float = 1.0
    delta_t: float = 0.5
    detuning: float = 0.0
    drain: DrainKind = "cavity"
    source_site: int = 1

    def __post_init__(self) -> None:
        if self.n_sites < 1:
            raise ValueError("n_sites must be positive")
        if self.g < 0 or self.delta_t < 0:
            raise ValueError("g and delta_t must be non-negative")
        if self.drain not in ("cavity", "site_n"):
            raise ValueError("drain must be 'cavity' or 'site_n'")
        if not 1 <= self.source_site <= self.n_sites:
            raise ValueError("source_site must index an emitter from 1 to N")

    @property
    def dimension(self) -> int:
        """Extended Hilbert-space dimension: cavity + sites + sink."""

        return self.n_sites + 2

    @property
    def sink_index(self) -> int:
        return self.n_sites + 1

    @property
    def drain_source_index(self) -> int:
        return 0 if self.drain == "cavity" else self.n_sites


@dataclass(frozen=True)
class ChannelRates:
    """Rates that change the state of a fixed transport geometry."""

    gamma_rec: float = 0.0
    gamma_abs: float = 0.0
    gamma_deph: float = 0.0
    gamma_lead: float = 0.5

    def __post_init__(self) -> None:
        if min(self.gamma_rec, self.gamma_abs, self.gamma_deph, self.gamma_lead) < 0:
            raise ValueError("all Lindblad rates must be non-negative")


def absorption_rate(gamma_rec: float, thermal_ratio: float) -> float:
    """Return gamma_abs for ``thermal_ratio = k_B T / Delta``.

    This is Eq. (S17), parameterized as in Figures 3 and S4.  Treat zero as the
    analytic T -> 0 limit instead of evaluating ``exp(-inf)``.
    """

    if gamma_rec < 0:
        raise ValueError("gamma_rec must be non-negative")
    if thermal_ratio < 0:
        raise ValueError("thermal_ratio must be non-negative")
    if thermal_ratio == 0 or gamma_rec == 0:
        return 0.0
    return float(gamma_rec * np.exp(-1.0 / thermal_ratio))


def sample_standard_disorder(model: TransportModel, seed: int) -> NDArray[np.float64]:
    """Draw the standard-normal variables X_i for one paired realization."""

    return np.random.default_rng(seed).normal(size=model.n_sites - 1)


def build_hamiltonian(
    model: TransportModel,
    standard_disorder: NDArray[np.float64],
) -> NDArray[np.complex128]:
    """Construct Eq. (1) in ``[cavity, sites, sink]`` order."""

    expected = (model.n_sites - 1,)
    if np.shape(standard_disorder) != expected:
        raise ValueError(f"standard_disorder must have shape {expected}")

    h = np.zeros((model.dimension, model.dimension), dtype=np.complex128)
    h[0, 0] = 0.0
    for site in range(1, model.n_sites + 1):
        h[site, site] = model.detuning
        h[0, site] = model.g
        h[site, 0] = model.g

    hoppings = model.t_mean + model.delta_t * np.asarray(standard_disorder)
    for site, hopping in enumerate(hoppings, start=1):
        h[site, site + 1] = hopping
        h[site + 1, site] = hopping

    return h


def rank_one_operator(
    dimension: int,
    destination: int,
    source: int,
) -> csc_matrix:
    """Return the unit-amplitude operator ``|destination><source|``."""

    return csc_matrix(
        ([1.0 + 0.0j], ([destination], [source])),
        shape=(dimension, dimension),
        dtype=np.complex128,
    )


def build_unit_jump_families(model: TransportModel) -> dict[str, list[csc_matrix]]:
    """Build unit-rate jump families; physical rates multiply dissipators."""

    d = model.dimension
    sites = range(1, model.n_sites + 1)
    return {
        "rec": [rank_one_operator(d, 0, site) for site in sites],
        "abs": [rank_one_operator(d, site, 0) for site in sites],
        "deph": [rank_one_operator(d, site, site) for site in sites],
        "lead": [rank_one_operator(d, model.sink_index, model.drain_source_index)],
    }


def initial_density(model: TransportModel) -> NDArray[np.complex128]:
    """Prepare the reconstructed source state ``|source><source|``."""

    rho = np.zeros((model.dimension, model.dimension), dtype=np.complex128)
    rho[model.source_site, model.source_site] = 1.0
    return rho
