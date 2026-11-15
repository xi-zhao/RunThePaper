"""Propagate the source-defined Walsh iSWAP and its dephasing filter."""

import json
from pathlib import Path

import numpy as np
from scipy.linalg import expm


X = np.array([[0., 1.], [1., 0.]])
IDENTITY = np.eye(2)
COUPLING = np.zeros((4, 4))
COUPLING[1, 2] = COUPLING[2, 1] = .5
DRIVE = np.kron(X, IDENTITY) / 2
NOISE = np.kron(IDENTITY, np.diag([-1., 1.])) / 2


def controls(config, primitive=False):
    if primitive:
        return [(np.pi, COUPLING)]
    scale = config["coupling_peak_rad_per_microsecond"]
    return [(scale * t, a * COUPLING + b * DRIVE)
            for t, a, b in zip(config["duration_microseconds"],
                              config["lambda_relative"], config["omega_relative"])]


def propagate(pieces, offset=0):
    u = np.eye(4, dtype=complex)
    for duration, h in pieces:
        u = expm(-1j * duration * (h + offset * NOISE)) @ u
    return u


def filter_integrals(pieces, frequencies, scale):
    """Frequencies are Hz; internal time is inverse peak angular coupling."""
    omega = 2 * np.pi * np.asarray(frequencies) / scale
    accumulated = np.zeros((len(omega), 4, 4), dtype=complex)
    u = np.eye(4, dtype=complex)
    elapsed = 0.
    for duration, h in pieces:
        values, vectors = np.linalg.eigh(h)
        n = vectors.conj().T @ NOISE @ vectors
        phases = omega[:, None, None] + values[:, None] - values[None, :]
        integrals = duration * np.exp(.5j * phases * duration) * np.sinc(phases * duration / (2 * np.pi))
        local = np.einsum("ia,fab,jb->fij", vectors, integrals * n, vectors.conj())
        rotated = np.einsum("ia,fij,jb->fab", u.conj(), local, u)
        accumulated += rotated * np.exp(1j * omega * elapsed)[:, None, None]
        u = expm(-1j * duration * h) @ u
        elapsed += duration
    return accumulated / scale


def compute(config):
    target = propagate(controls(config, primitive=True))
    freq = np.unique(np.r_[0., np.logspace(1, 7, 601), np.arange(1e3, 1e7+1, 1e3)])
    offsets = np.linspace(-.1, .1, 401)
    small = np.array([.001, .002, .005, .01, .02])
    scale = config["coupling_peak_rad_per_microsecond"] * 1e6
    result = dict(frequencies_hz=freq.tolist(), offsets=offsets.tolist(), small_offsets=small.tolist())
    for name, primitive in (("primitive", True), ("walsh", False)):
        parts = controls(config, primitive)
        u = propagate(parts)
        integrals = filter_integrals(parts, freq, scale)
        power = np.einsum("fij,fij->f", integrals.conj(), integrals).real / 4
        loss = lambda e: float(1 - abs(np.trace(target.conj().T @ propagate(parts, e)) / 4)**2)
        result[name] = dict(duration_microseconds=sum(t for t, _ in parts) / (scale / 1e6),
            nominal_infidelity=loss(0), unitarity_error=float(np.max(abs(u.conj().T @ u - np.eye(4)))),
            filter_power_seconds_squared=power.tolist(),
            static_infidelity=[loss(e) for e in offsets],
            small_offset_infidelity=[loss(e) for e in small],
            dc_noise_cost=float(power[0] * scale**2),
            dc_integral_real=integrals[0].real.tolist(), dc_integral_imag=integrals[0].imag.tolist())
    return result


if __name__ == "__main__":
    result = compute(json.loads(Path("config/walsh-followup.json").read_text()))
    Path("results/walsh-followup.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print({name: {key: result[name][key] for key in
          ("duration_microseconds", "nominal_infidelity", "dc_noise_cost")} for name in ("primitive", "walsh")},
          flush=True)
