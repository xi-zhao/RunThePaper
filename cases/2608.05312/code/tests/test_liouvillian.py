from __future__ import annotations

import numpy as np

from cavity_transport.liouvillian import dense_propagate_final
from cavity_transport.model import ChannelRates, TransportModel
from cavity_transport.simulation import PreparedTransport


def test_sparse_propagation_matches_paper_dense_expm_path() -> None:
    prepared = PreparedTransport.from_seed(TransportModel(3), seed=4)
    rates = ChannelRates(gamma_rec=0.3, gamma_abs=0.07, gamma_deph=0.2)
    sparse = prepared.final_density(rates, 2.5)
    dense = dense_propagate_final(prepared.generator(rates), prepared.rho0, 2.5)
    assert np.max(np.abs(sparse - dense)) < 1e-10


def test_lindblad_evolution_preserves_density_matrix() -> None:
    prepared = PreparedTransport.from_seed(TransportModel(6), seed=3)
    rho = prepared.final_density(
        ChannelRates(gamma_rec=0.5, gamma_abs=0.1, gamma_deph=0.4), 5.0
    )
    assert abs(np.trace(rho) - 1.0) < 1e-10
    assert np.max(np.abs(rho - rho.conj().T)) < 1e-10
    assert np.min(np.linalg.eigvalsh((rho + rho.conj().T) / 2)) > -1e-10
