"""Recalculate the QC27 pulse, randomized-benchmarking and readout model."""

import json
from pathlib import Path
import sys

import numpy as np
from scipy.optimize import least_squares

from physical import (CLIFFORDS, conjugate, elementary, error_vectors, exact_noise,
                      group, moment_table, one_gate, product, pulses, rotate, sequences)


def shuffled_variance(samples):
    """Exact expectation over all orderings of the finite set of noise draws."""
    k, n = samples.shape
    centered = samples - samples.mean(axis=0)
    row_mean = centered.mean(axis=1)
    floor = row_mean @ row_mean / (k - 1)
    fluctuation = ((centered - row_mean[:, None])**2).sum() / ((k - 1) * (n - 1))
    return floor + fluctuation * (1 / np.arange(1, n+1) - 1/n)


def model_variance(j, n, c, u):
    """Table I where c and u denote the two variances sigma squared."""
    return (2*j*(2*j-1)*(n+2)/(9*n)*c**2
            + 2*j*(4+2*j+n)/(9*n)*u**2 + (4*j/9)*c*u)


def fit_errors(j, variance):
    n = np.arange(1, len(variance)+1)
    fit = least_squares(
        lambda x: np.log(model_variance(j, n, *np.exp(x))) - np.log(variance),
        np.log([1e-4, 1e-3]), bounds=(np.log([1e-10, 1e-10]), np.log([1., 1.])),
    )
    return np.exp(fit.x).tolist()


def pulse_filter(family, frequency):
    """First-order Fourier integral of the toggling-frame Z operator."""
    signal = np.zeros((len(frequency), 3), dtype=complex)
    elapsed = 0.0
    pre = (1., 0., 0., 0.)
    z = np.array([0., 0., 1.])

    def phasor(w, duration):
        return duration * np.exp(0.5j*w*duration) * np.sinc(w*duration/(2*np.pi))

    for dt, x, y, _ in pulses("x", family):
        rate = np.hypot(x, y)
        base = rotate(conjugate(pre), z)
        transverse = rotate(conjugate(pre), np.array([-y, x, 0.]) / rate)
        plus, minus = phasor(frequency+rate, dt), phasor(frequency-rate, dt)
        local = (plus+minus)[:, None] / 2 * base + (plus-minus)[:, None] / (2j) * transverse
        signal += np.exp(1j*frequency*elapsed)[:, None] * local / 2
        pre = product(elementary(dt, x, y, 0.), pre)
        elapsed += dt
    return np.linalg.norm(signal, axis=1)


def random_walks(gates, mult, inv):
    rng = np.random.default_rng(10727)
    vectors = np.array([error_vectors(k, "primitive", 0)[0] for k in range(24)])
    seq = sequences(rng, 8, 100, mult, inv)
    steps = np.empty((*seq.shape, 3))
    for i, row in enumerate(seq):
        state = 0
        for j, k in enumerate(row):
            steps[i, j] = rotate(conjugate(gates[state]), vectors[k])
            state = mult[k, state]
    white = rng.normal(0, 1, (8, 1000, 100))
    dc = rng.normal(0, 1, (8, 1000, 1))
    mag = np.linalg.norm(vectors[rng.integers(24, size=1000)], axis=-1)
    autocorr = {}
    for block in (1, 3, 10, 20, 100):
        noise = rng.normal(0, 1, (400, (1000+block-1)//block))
        x = np.repeat(abs(noise), block, axis=1)[:, :1000]*mag
        autocorr[str(block)] = [float(np.mean(x[:, :1000-d]*x[:, d:])) for d in range(101)]
    return dict(white_ends=np.einsum("krj,kjc->krc", white, steps),
                dc_ends=dc*steps.sum(axis=1)[:, None, :],
                white_path=np.cumsum(white[0, 0, :, None]*steps[0], axis=0),
                dc_path=np.cumsum(dc[0, 0, 0]*steps[0], axis=0)), autocorr


def main():
    gates, mul, inv = group()
    families = ("primitive", "corpse", "wamf", "bb1", "corpse-2pi", "wamf-2pi")
    unitary = {f: float(max(1-abs(gates[k] @ one_gate(k, f)) for k in range(24))) for f in families}
    moments = {f"{f}-{q}": moment_table(gates, f, q) for f in families for q in (0, 1)}
    idle = {f: float(np.linalg.norm(error_vectors(0, f, 0)[0])) for f in ("corpse", "corpse-2pi")}
    freq = np.geomspace(1e-4, 20, 240)
    filters = {f: pulse_filter(f, freq).tolist() for f in ("primitive", "corpse", "wamf")}
    arrays, autocorrelation = random_walks(gates, mul, inv)
    rng = np.random.default_rng(190910727)
    seq = sequences(rng, 50, 100, mul, inv)
    arrays["sequence"] = seq
    stats = {}
    cases = [
        ("dc", "primitive", 0, 2e-3, 0, 100),
        ("white", "primitive", 0, 0, 2e-3, 100),
        ("primitive-z", "primitive", 0, 2e-3, 5e-4, 100),
        ("corpse-z", "corpse", 0, 2e-3, 5e-4, 100),
        ("wamf-z", "wamf", 0, 2e-3, 5e-4, 100),
        ("corpse-2pi-z", "corpse-2pi", 0, 2e-3, 5e-4, 100),
        ("wamf-2pi-z", "wamf-2pi", 0, 2e-3, 5e-4, 100),
        ("primitive-a", "primitive", 1, 9e-4, 2e-4, 100),
        ("bb1-a", "bb1", 1, 9e-4, 2e-4, 100),
    ]
    for name, family, quad, c, u, block in cases:
        p = exact_noise(seq, family, quad, 200, c, u, block, 93590)
        counts = rng.binomial(220, p)
        v = shuffled_variance(counts/220)
        arrays[name], arrays[name+"-counts"] = p, counts
        stats[name] = dict(mean=float(p.mean()), variance=v.tolist(),
                           exact_probability_variance=shuffled_variance(p).tolist(),
                           first_last=float(v[0]/v[-1]), fitted_error_variances=fit_errors(100, v))
    for f in ("primitive", "corpse", "corpse-2pi"):
        for b in (1, 2, 10, 25, 100):
            name = f"{f}-block-{b}"
            p = exact_noise(seq[:20], f, 0, 200, 2e-3, 5e-4, b, 98591)
            counts = rng.binomial(220, p)
            arrays[name], arrays[name+"-counts"] = p, counts
            v = shuffled_variance(counts/220)
            stats[name] = dict(mean=float(p.mean()), variance=v.tolist(), first_last=float(v[0]/v[-1]))
    n = np.arange(1, 201)
    qpn = (arrays["corpse-z"] * (1-arrays["corpse-z"])).mean()/(220*n)
    five = {}
    for f, c, u in [
        ("primitive", np.array([1.2,1.5,1.9,2.4,2.7])*1e-4, np.array([7.5,8.1,8.5,8.6,8.7])*1e-4),
        ("bb1", np.array([2.3,2.5,1.1,2.2,2.3])*1e-5, np.array([6.5,6.5,6.3,6.6,6.5])*1e-4),
    ]:
        five[f] = model_variance(500, np.arange(1, 501)[:, None], c, u).tolist()
    np.savez_compressed("results/trials.npz", **arrays)
    out = dict(frequency=freq.tolist(), filter=filters, unitary_overlap_error=unitary, idle_first_order=idle,
               step_moments=moments, autocorrelation=autocorrelation, statistics=stats,
               five_ion_caption_model=five, qpn=dict(worst=0.25/220, finite_n=qpn.tolist()))
    Path("results/model.json").write_text(json.dumps(out, indent=2, allow_nan=False)+"\n")
    print("completed", len(stats), "noise/gate cases and", len(CLIFFORDS), "Cliffords")


if __name__ == "__main__":
    main()
