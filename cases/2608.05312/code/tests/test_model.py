from __future__ import annotations

import numpy as np
import pytest

from cavity_transport.model import (
    ChannelRates,
    TransportModel,
    absorption_rate,
    build_hamiltonian,
    build_unit_jump_families,
)


def test_hamiltonian_matches_basis_and_is_hermitian() -> None:
    model = TransportModel(3, g=1.5, t_mean=1.0, delta_t=0.5, detuning=2.0)
    h = build_hamiltonian(model, np.asarray([0.0, 2.0]))
    assert h.shape == (5, 5)
    assert np.allclose(h, h.conj().T)
    assert np.allclose(h[0, 1:4], 1.5)
    assert h[1, 2] == pytest.approx(1.0)
    assert h[2, 3] == pytest.approx(2.0)
    assert np.allclose(h[-1, :], 0.0)
    assert np.allclose(np.diag(h)[1:4], 2.0)


def test_jump_directions_are_unambiguous() -> None:
    model = TransportModel(4, drain="cavity")
    jumps = build_unit_jump_families(model)
    assert jumps["rec"][2][0, 3] == 1
    assert jumps["rec"][2][3, 0] == 0
    assert jumps["abs"][2][3, 0] == 1
    assert jumps["lead"][0][model.sink_index, 0] == 1

    site_drain = build_unit_jump_families(TransportModel(4, drain="site_n"))
    assert site_drain["lead"][0][5, 4] == 1


def test_detailed_balance_and_validation() -> None:
    assert absorption_rate(0.8, 0.0) == 0.0
    assert absorption_rate(0.8, 1.0) / 0.8 == pytest.approx(np.exp(-1.0))
    with pytest.raises(ValueError):
        absorption_rate(1.0, -0.1)
    with pytest.raises(ValueError):
        ChannelRates(gamma_rec=-1.0)
    with pytest.raises(ValueError):
        TransportModel(0)
