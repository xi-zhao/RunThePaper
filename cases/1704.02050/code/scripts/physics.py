"""Independent held-control model, with angular frequencies only at the PSD interface."""
from functools import lru_cache

import numpy as np
from scipy.special import j0
from scipy.signal import hilbert
from scipy.signal.windows import dpss


@lru_cache(maxsize=32)
def tapers(n, nw, count):
    return dpss(n, nw, count, sym=True, norm=2)


def echo(n, order, padding=0):
    pieces = np.array_split(np.ones(n-2*padding), order+1)
    return np.pad(np.concatenate([(-1)**i*piece for i,piece in enumerate(pieces)]), padding)


def shift(values, step, carrier, modulation):
    oscillator = np.exp(2j*np.pi*carrier*step*np.arange(values.size))
    return (hilbert(values)*oscillator).real if modulation == "SSB" else values*oscillator.real


def areas(values, total=np.pi, signed=False, trapezoid=False):
    """Return the rotation angles per held sample, with explicit normalization."""
    measure = values if signed else np.abs(values)
    norm = np.trapezoid(measure) if trapezoid else np.sum(measure)
    return values * (total/norm)


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
        out[i:i+chunk] = scale*(phase @ areas_per_cell)
    return out


def sid_loss(response, alpha):
    """Exact phase-averaged loss from a uniformly phased coherent tone."""
    return (1-j0(alpha*np.abs(response)))/2


def detuned_probability(angles, f, duration):
    """Exact SU(2) multiplication for each constant detuned segment."""
    detuning = 2*np.pi*np.asarray(f)*duration/len(angles)
    a = np.ones(len(detuning), complex)
    b = np.zeros_like(a)
    for angle in angles:
        radius = np.hypot(angle, detuning)
        cos = np.cos(radius/2)
        sinc = np.sinc(radius/(2*np.pi))/2
        z = cos-1j*detuning*sinc
        x = -1j*angle*sinc
        a,b = z*a+x*b, x*a+z.conj()*b
    return np.abs(b)**2


def three_axis_ensemble(angles, f, duration, alpha, dephase_rms_ratio, noise_hold, runs, seed):
    """Average error-channel projections for Gaussian piecewise-white dephasing."""
    rng = np.random.default_rng(seed)
    n = len(angles)
    dt = duration/n
    phases = rng.uniform(0,2*np.pi,runs)
    increment = 2*np.pi*np.asarray(f)[:,None]*dt
    hold_response = np.sinc(np.asarray(f)[:,None]*dt)
    ideal_a, ideal_b = np.cos(angles.sum()/2), np.sin(angles.sum()/2)
    scale = 2*dephase_rms_ratio*np.max(np.abs(angles))
    a = np.ones((len(f),runs), complex)
    b = np.zeros_like(a)
    for index,theta in enumerate(angles):
        if index % noise_hold == 0:
            z_angle = scale*rng.normal(size=runs)
        x_angle = theta*(1+alpha*np.cos(phases+increment*(index+0.5))*hold_response)
        radius = np.hypot(x_angle,z_angle)
        sinc = np.sinc(radius/(2*np.pi))/2
        z = np.cos(radius/2)-1j*z_angle*sinc
        x = -1j*x_angle*sinc
        a,b = z*a+x*b, x*a+z.conj()*b
    a,b = ideal_a*a+1j*ideal_b*b, 1j*ideal_b*a+ideal_a*b
    squares = np.stack([b.imag**2,b.real**2,a.imag**2])
    survival = 1-squares.sum(axis=0)+squares
    return survival.mean(axis=-1), squares[0].mean(axis=-1), squares[0].std(axis=-1,ddof=1)/np.sqrt(runs)
