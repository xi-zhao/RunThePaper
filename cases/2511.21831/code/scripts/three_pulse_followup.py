"""Repair the two-motif synthesis using an exchange of the two smaller axes."""

import json
from pathlib import Path

import numpy as np

from generate import I, X, Y, XX, cartan, pair_parts, rot


HALF_PI = np.pi / 2


def interval(pulses, target):
    a, b, c = pulses
    x, y, z = target
    exchange = y > a
    if exchange:
        lower = x + z - a
        upper = min(b + c - y, y - b + c, a + x - z, HALF_PI)
    else:
        lower = max(x + y - a, a - x + y, b - c + z)
        upper = min(b + c - z, a + x - y, HALF_PI)
    return float(lower), float(upper), bool(exchange)


def matrix(pulses, target):
    a, b, c = pulses
    c1, y, z = target
    reflected = c1 > HALF_PI
    x = np.pi - c1 if reflected else c1
    lo, hi, exchange = interval(pulses, (x, y, z))
    assert lo <= hi + 1e-13
    delta = (lo + hi) / 2
    v, w = (z, y) if exchange else (y, z)
    front, _, tail = pair_parts(a, delta, x, v)
    first, second, _ = pair_parts(b, c, max(delta, w), min(delta, w))
    mapping = np.kron(rot(X, HALF_PI), rot(X, HALF_PI))
    if exchange:
        # Rz(pi/2) on both sites exchanges XX and YY before mapping YY to ZZ.
        local = np.diag([np.exp(-.25j*np.pi), np.exp(.25j*np.pi)])
        mapping = mapping @ np.kron(local, local)
    u = front @ mapping @ first @ second @ mapping.conj().T @ tail
    if exchange:
        flip = np.kron(rot(X, HALF_PI), rot(X, HALF_PI))
        u = flip @ u @ flip.conj().T
    if reflected:
        # Obtain C(x,y,-z) by conjugating the second motif and outer axes
        # through a global complex conjugation and even local sign changes.
        both_signs = np.kron(rot(np.array([[1.,0.],[0.,-1.]]), np.pi), I)
        signed = both_signs @ u.conj() @ both_signs.conj().T
        y_flip = np.kron(-1j*Y, I)
        u = (-1j*XX) @ y_flip @ signed @ y_flip.conj().T
    direct = cartan(*target)
    discrepancy = float(np.max(abs(u - direct)))
    assert discrepancy < 3e-8, (pulses, target, discrepancy)
    parts = (front, first, second)
    return dict(pulses=list(map(float,pulses)), target=list(map(float,target)),
        delta=delta, interval=[lo,hi], exchange=exchange, reflected=bool(reflected),
        unitary=[u.real.tolist(),u.imag.tolist()],
        entangling_parts=[[v.real.tolist(),v.imag.tolist()] for v in parts],
        direct_matrix_error=discrepancy)


def main():
    cfg = json.loads(Path("config/three-pulse-followup.json").read_text())
    rng = np.random.default_rng(cfg["seed"])
    n = cfg["interval_probes"]
    pulses = np.sort(rng.uniform(0, HALF_PI, (n,3)), axis=1)[:,::-1]
    targets = np.sort(rng.uniform(0, HALF_PI, (n,3)), axis=1)[:,::-1]
    a,b,c = pulses.T
    x,y,z = targets.T
    admissible = (x+y+z <= a+b+c) & (-x+y+z <= -a+b+c) & (z <= c)
    branch = y > a
    widths = [interval(p,t) for p,t in zip(pulses[admissible],targets[admissible],strict=True)]
    assert all(lo <= hi + 1e-13 for lo,hi,_ in widths)
    records = []
    for mask in (~branch,branch):
        indexes = np.flatnonzero(admissible & mask)[:cfg["matrices_per_branch"]]
        for i in indexes:
            p,t = pulses[i],targets[i]
            records.append(matrix(p,t))
            records.append(matrix(p,[np.pi-t[0],t[1],t[2]]))
    witnesses = {k:matrix(**cfg[k]) for k in ("fixed_order_witness","reflected_witness")}
    out = dict(interval_probes=n,accepted=int(admissible.sum()),exchanged=int(np.sum(admissible&branch)),
               minimum_interval_width=min(hi-lo for lo,hi,_ in widths), matrices=records,witnesses=witnesses)
    Path("results/three-pulse-followup.json").write_text(json.dumps(out,allow_nan=False,separators=(",",":"))+"\n")
    print(out["accepted"],out["exchanged"],max(r["direct_matrix_error"] for r in records),flush=True)


if __name__ == "__main__":
    main()
