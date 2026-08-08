"""Independent reproduction of arXiv:2608.05312.

The public API intentionally mirrors the physical model: a transport geometry,
channel rates, a prepared disorder realization, and observable projectors.
"""

from .model import ChannelRates, TransportModel, absorption_rate
from .simulation import PreparedTransport, prepare_ensemble

__all__ = [
    "ChannelRates",
    "PreparedTransport",
    "TransportModel",
    "absorption_rate",
    "prepare_ensemble",
]
