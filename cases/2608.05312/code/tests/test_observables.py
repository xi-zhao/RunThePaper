from __future__ import annotations

import numpy as np

from cavity_transport.model import ChannelRates, TransportModel
from cavity_transport.observables import dephasing_rate_matrix, rescue_rate_matrix
from cavity_transport.simulation import PreparedTransport


def test_dark_to_bright_sum_rule_is_size_independent() -> None:
    gamma = 0.73
    for n_sites in (3, 4, 8, 16, 32):
        prepared = PreparedTransport.from_seed(
            TransportModel(n_sites, t_mean=0.0, delta_t=0.0), seed=0
        )
        p = prepared.projectors
        rates = rescue_rate_matrix(p.cavity_weights, gamma)
        dark = p.dark_indices
        bright = p.bright_indices
        assert np.max(np.abs(rates[np.ix_(bright, dark)].sum(axis=0) - gamma)) < 1e-12
        assert np.max(np.abs(rates[dark, :])) < 1e-12


def test_dephasing_rate_matrix_is_bidirectional() -> None:
    prepared = PreparedTransport.from_seed(TransportModel(9), seed=1)
    rates = dephasing_rate_matrix(prepared.projectors.eigenvectors, gamma_deph=0.4)
    assert np.max(np.abs(rates - rates.T)) < 1e-12


def test_clean_dark_population_is_single_exponential() -> None:
    prepared = PreparedTransport.from_seed(
        TransportModel(6, t_mean=0.0, delta_t=0.0), seed=0
    )
    times = np.linspace(0.0, 6.0, 61)
    dynamics = prepared.population_dynamics(ChannelRates(gamma_rec=1.0), times)
    normalized = dynamics["dark"] / dynamics["dark"][0]
    assert np.max(np.abs(normalized - np.exp(-times))) < 1e-10
    assert np.max(np.abs(dynamics["bright"] + dynamics["dark"] + dynamics["sink"] - 1)) < 1e-10
