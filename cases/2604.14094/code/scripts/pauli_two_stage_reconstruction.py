"""Reconstruct all weights after independently pruning elementary local operators."""
import json
from pathlib import Path
import numpy as np
from generate import oscillator, pauli_local
from pauli_thresholds import group


def calculate(k, local_cutoff, final_cutoff):
    d = 2**k
    with np.errstate(divide="ignore", over="ignore", invalid="ignore"):
        x2, x4 = oscillator(d, "projected_position")
    assert np.isfinite(x2).all() and np.isfinite(x4).all()
    second = pauli_local(x2, local_cutoff)
    fourth = pauli_local(x4, local_cutoff)
    number = pauli_local(np.diag(np.arange(d)+.5), local_cutoff)
    single = {key: number.get(key, 0) + fourth.get(key, 0)/64
              + second.get(key, 0)*second[(0, 0)]/16
              for key in second.keys() | fourth.keys() | number.keys()}
    s, g = group(single, k), group(second, k)
    counts = [1]
    for w in range(1, 2*k+1):
        count = int(np.count_nonzero(s[w] > final_cutoff)) if w <= k else 0
        for a in range(max(1, w-k), min(k, w-1)+1):
            count += int(sum(np.count_nonzero(c*g[w-a]/32 > final_cutoff) for c in g[a]))
        counts.append(3*count)
    return dict(k=k, counts=counts, retained_x2=len(second), retained_x4=len(fourth), retained_number=len(number))


def main():
    cfg = json.loads(Path("config/two-stage-protocol.json").read_text())
    rows = [calculate(k, cfg["local_absolute_cutoff"], cfg["assembled_absolute_cutoff"]) for k in range(2, 11)]
    Path("results/two-stage-reconstruction.json").write_text(json.dumps(dict(protocol=cfg, rows=rows), indent=2)+"\n")
    print("reconstructed", len(rows), "cutoffs", sum(len(r["counts"]) for r in rows), "counts", flush=True)


if __name__ == "__main__":
    main()
