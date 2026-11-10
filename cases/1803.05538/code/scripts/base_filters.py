"""Numerical kernels reused from the QC34 held-control model.

Source SHA-256: 68243272872fdb57ac3190717b9477ccdcfa54a3a629035b4ab5fb61c303aee6.
"""
from functools import lru_cache

import numpy as np
from scipy.signal import hilbert
from scipy.signal.windows import dpss

@lru_cache(maxsize=32)
def tapers(n, nw, count):
    return dpss(n, nw, count, sym=True, norm=2)


def shift(values, step, carrier, modulation):
    oscillator = np.exp(2j*np.pi*carrier*step*np.arange(values.size))
    return (hilbert(values)*oscillator).real if modulation == "SSB" else values*oscillator.real


def transfer(areas_per_cell, frequency_hz, duration):
    """Integral of the drive against exp(+i 2 pi f t) for piecewise constants."""
    f = np.atleast_1d(frequency_hz)
    dt = duration / areas_per_cell.shape[0]
    samples = np.arange(areas_per_cell.shape[0]) + 0.5
    out = np.empty((len(f),)+areas_per_cell.shape[1:],complex)
    chunk = max(1, 1_000_000//len(samples))
    for i in range(0,len(f),chunk):
        frequency = f[i:i+chunk]
        phase = np.exp(2j*np.pi*dt*frequency[:,None]*samples)
        scale = np.sinc(dt*frequency).reshape((len(frequency),)+(1,)*(out.ndim-1))
        with np.errstate(divide="ignore", invalid="ignore", over="ignore"):
            block = scale*(phase @ areas_per_cell)
        if not np.all(np.isfinite(block)):
            raise FloatingPointError("Nonfinite held-control transform")
        out[i:i+chunk] = block
    return out
