"""Independent arithmetic audit of the paper's Eq. (15) coefficient."""

from __future__ import annotations

from decimal import Decimal, localcontext

import numpy as np


def lzf_kzm_density_ratio(fidelity: float) -> float:
    """Evaluate the literal Eq. (15) ratio ``nu_LZF / nu_KZM``."""

    f = float(fidelity)
    if not 0.0 < f < 1.0:
        raise ValueError("fidelity must lie strictly inside (0, 1)")
    return float(np.sqrt(2.0 * abs(np.log1p(-f)) / np.pi) / (2.0 * np.pi))


def ratio_from_preceding_equations(
    fidelity: float,
    *,
    coupling_w: float,
    tau_q: float,
    hbar: float,
) -> float:
    """Re-derive the same ratio independently from Eqs. (10) and (14)."""

    if coupling_w <= 0.0 or tau_q <= 0.0 or hbar <= 0.0:
        raise ValueError("coupling_w, tau_q, and hbar must be positive")
    f = float(fidelity)
    if not 0.0 < f < 1.0:
        raise ValueError("fidelity must lie strictly inside (0, 1)")
    n_tilde = 2.0 * np.pi * np.sqrt(
        np.pi * coupling_w * tau_q / (hbar * abs(np.log1p(-f)))
    )
    nu_lzf = 1.0 / n_tilde
    nu_kzm = np.sqrt(hbar / (2.0 * coupling_w * tau_q))
    return float(nu_lzf / nu_kzm)


def decimal_literal_ratio(fidelity: str, *, precision: int = 60) -> Decimal:
    """High-precision implementation independent of the NumPy code path."""

    with localcontext() as context:
        context.prec = precision
        f = Decimal(fidelity)
        if not Decimal(0) < f < Decimal(1):
            raise ValueError("fidelity must lie strictly inside (0, 1)")
        pi = Decimal("3.14159265358979323846264338327950288419716939937510582097494")
        return ((Decimal(2) * (-(Decimal(1) - f).ln()) / pi).sqrt()) / (
            Decimal(2) * pi
        )
