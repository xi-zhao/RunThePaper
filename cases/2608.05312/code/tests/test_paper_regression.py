from __future__ import annotations

import pytest

from cavity_transport.model import ChannelRates, TransportModel
from cavity_transport.simulation import ensemble_final_populations, prepare_ensemble


def _mean_eta(model: TransportModel, rates: ChannelRates, final_time: float) -> float:
    result = ensemble_final_populations(
        prepare_ensemble(model, range(15)), rates, final_time
    )
    return float(result["mean"]["sink"])


def test_figure2_n6_cross_figure_endpoint() -> None:
    model = TransportModel(6)
    rescue = _mean_eta(model, ChannelRates(gamma_rec=1.0), 30.0)
    dephasing = _mean_eta(model, ChannelRates(gamma_deph=1.0), 30.0)
    assert rescue == pytest.approx(0.999, abs=0.01)
    assert dephasing == pytest.approx(0.794, abs=0.03)


@pytest.mark.parametrize(
    ("detuning", "paper_eta"),
    [(0.0, 0.794), (5.0, 0.611), (10.0, 0.395), (20.0, 0.170)],
)
def test_table_s2_dephasing_detuning(detuning: float, paper_eta: float) -> None:
    generated = _mean_eta(
        TransportModel(6, detuning=detuning), ChannelRates(gamma_deph=1.0), 30.0
    )
    assert generated == pytest.approx(paper_eta, abs=0.025)


def test_figure3_size_inversion() -> None:
    eta_n6 = _mean_eta(TransportModel(6), ChannelRates(gamma_deph=0.5), 25.0)
    eta_n64 = _mean_eta(TransportModel(64), ChannelRates(gamma_deph=0.5), 25.0)
    assert eta_n6 == pytest.approx(0.66, abs=0.03)
    assert eta_n64 == pytest.approx(0.09, abs=0.01)
    assert eta_n6 > 5 * eta_n64
