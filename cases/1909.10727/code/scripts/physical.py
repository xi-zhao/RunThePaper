"""Exact single-qubit propagation of the published Clifford and DCG pulses."""

import math

import numpy as np
from numba import njit


# Time-ordered decomposition from the Ref. 32 convention, also used in QC33.
CLIFFORDS = ("i", "x", "y", "z", "X", "Y", "Z", "a", "b", "c", "zX", "za",
             "Zx", "cx", "ZX", "Za", "Xc", "zb", "Zb", "cY", "zY", "cX", "ZY", "ca")
SPEC = {
    "x": (0, np.pi), "y": (1, np.pi), "z": (2, np.pi),
    "X": (0, np.pi / 2), "Y": (1, np.pi / 2), "Z": (2, np.pi / 2),
    "a": (0, -np.pi / 2), "b": (1, -np.pi / 2), "c": (2, -np.pi / 2),
}
IDENTITY = (1.0, 0.0, 0.0, 0.0)


@njit(inline="always")
def product(l, r):
    a, x, y, z = l
    b, u, v, w = r
    return (a*b - x*u - y*v - z*w,
            a*u + x*b + y*w - z*v,
            a*v + y*b + z*u - x*w,
            a*w + z*b + x*v - y*u)


@njit(inline="always")
def elementary(dt, x, y, z):
    radius = math.sqrt(x*x + y*y + z*z)
    if radius == 0:
        return IDENTITY
    half = dt * radius / 2
    s = math.sin(half) / radius
    return math.cos(half), x*s, y*s, z*s


def pulses(label, family):
    """Rows are duration, x/y Rabi components, and any instantaneous Z angle."""
    if label == "i":
        if family == "primitive":
            return [(np.pi, 0, 0, 0)]
        second = 1 if family.endswith("-2pi") else -1
        return [(np.pi, 1, 0, 0), (np.pi, second, 0, 0)]
    family = family.removesuffix("-2pi")
    axis, angle = SPEC[label]
    if axis == 2:
        return [(0, 0, 0, angle)]
    phase = axis * np.pi / 2 + (np.pi if angle < 0 else 0)
    theta = abs(angle)
    if family == "primitive":
        rotations = [(theta, 1, 0)]
    elif family == "corpse":
        k = np.arcsin(np.sin(theta / 2) / 2)
        rotations = [(2*np.pi + theta/2 - k, 1, 0), (2*np.pi - 2*k, 1, np.pi),
                     (theta/2 - k, 1, 0)]
    elif family == "wamf":
        x0, x3 = theta + 2*np.pi, np.pi * (1.0 if theta == np.pi else 0.64)
        rotations = [((x0+x3)/4, 1, 0), ((x0-x3)/2, (x0-x3)/(x0+x3), 0),
                     ((x0+x3)/4, 1, 0)]
    elif family == "bb1":
        k = np.arccos(-theta / (4*np.pi))
        rotations = [(theta, 1, 0), (np.pi, 1, k), (2*np.pi, 1, 3*k), (np.pi, 1, k)]
    else:
        raise ValueError(family)
    return [(a / amp, amp*np.cos(phase+p), amp*np.sin(phase+p), 0) for a, amp, p in rotations]


def timeline(sequence, family, clock=np.pi/2):
    """Split driven and idle segments at a laboratory-clock noise boundary."""
    time = 0.0
    rows, indices = [], []
    for gate, k in enumerate(sequence):
        for label in CLIFFORDS[k]:
            for dt, x, y, z in pulses(label, family):
                if dt == 0:
                    rows.append((0, 0, 0, z))
                    indices.append((gate, 0))
                    continue
                end = time + dt
                while time < end - 1e-11:
                    tick = math.floor(time / clock + 1e-11)
                    limit = min(end, (tick + 1) * clock)
                    if limit <= time:
                        raise ValueError("clock failed to advance")
                    rows.append((limit - time, x, y, 0))
                    indices.append((gate, tick))
                    time = limit
                time = end
    return np.asarray(rows), np.asarray(indices, dtype=np.int64)


@njit
def propagate(rows, indices, slow, fast, block, quadrature):
    out = np.empty((len(slow), 4))
    for i in range(len(slow)):
        q = IDENTITY
        for j in range(len(rows)):
            dt, x, y, z = rows[j]
            if dt == 0:
                p = elementary(z, 0.0, 0.0, 1.0)
            else:
                gate, tick = indices[j]
                delta = slow[i, gate//block] + fast[i, tick]
                if quadrature == 0:
                    p = elementary(dt, x, y, delta)
                else:
                    p = elementary(dt, (1+delta)*x, (1+delta)*y, 0.0)
            q = product(p, q)
        out[i] = q
    return out


def one_gate(k, family, noise=0, quadrature=0):
    rows, ix = timeline([k], family)
    return propagate(rows, ix, np.full((1, 1), float(noise)), np.zeros((1, ix[:, 1].max()+1)), 1, quadrature)[0]


def group():
    gates = np.array([one_gate(k, "primitive") for k in range(24)])
    m = np.empty((24, 24), dtype=np.int64)
    for j, left in enumerate(gates):
        for k, right in enumerate(gates):
            scores = np.abs(gates @ product(tuple(left), tuple(right)))
            assert np.max(scores) > 1-1e-12
            m[j, k] = scores.argmax()
    assert all(len(set(row)) == 24 for row in m)
    return gates, m, np.argmax(m == 0, axis=0)


def sequences(rng, count, length, multiplication, inverse):
    gates = rng.integers(0, 24, size=(count, length))
    state = np.zeros(count, dtype=np.int64)
    for j in range(length-1):
        state = multiplication[gates[:, j], state]
    gates[:, -1] = inverse[state]
    assert np.all(multiplication[gates[:, -1], state] == 0)
    return gates


def exact_noise(seqs, family, quadrature, reps, slow_variance, fast_variance, block, seed):
    rng = np.random.default_rng(seed)
    count, length = seqs.shape
    shared = rng.normal(0, np.sqrt(slow_variance), (reps, (length+block-1)//block))
    results = np.empty((count, reps))
    for k, seq in enumerate(seqs):
        rows, ix = timeline(seq, family)
        fast = rng.normal(0, np.sqrt(fast_variance), (reps, ix[:, 1].max()+1))
        u = propagate(rows, ix, shared, fast, block, quadrature)
        results[k] = u[:, 1]**2 + u[:, 2]**2
    return results


def conjugate(q):
    w, x, y, z = q
    return w, -x, -y, -z


def error_vectors(k, family, quadrature, h=1e-5):
    """Central differences for quasistatic and piecewise independent perturbations."""
    rows, ix = timeline([k], family)
    width = ix[:, 1].max()+1
    n = width + 1
    plus, minus = np.zeros((n, 1)), np.zeros((n, 1))
    plus[0, 0], minus[0, 0] = h, -h
    fast = np.r_[np.zeros((1, width)), h*np.eye(width)]
    ideal = conjugate(one_gate(k, family))
    p = propagate(rows, ix, plus, fast, 1, quadrature)
    m = propagate(rows, ix, minus, -fast, 1, quadrature)
    return np.asarray([product(ideal, tuple(v))[1:] for v in (p-m)/(2*h)])


def rotate(q, v):
    return np.asarray(product(product(tuple(q), (0.0, *v)), conjugate(q))[1:])


def moment_table(gates, family, quadrature, h=1e-5):
    energies = []
    for k in range(24):
        vectors = error_vectors(k, family, quadrature, h)
        for prior in gates:
            proj = np.array([rotate(prior, v)[:2] for v in vectors])
            static = np.sum(proj[0]**2)
            white = np.sum(proj[1:]**2)
            energies.append((static, white))
    energies = np.asarray(energies)
    return dict(second=energies.mean(axis=0).tolist(), fourth=(energies**2).mean(axis=0).tolist(),
                mixed=float(np.mean(np.prod(energies,axis=1))-np.prod(energies.mean(axis=0))))
