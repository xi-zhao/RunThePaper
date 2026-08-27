"""Parameter scan driver for Fig. 2 / Fig. S2 observables.

Runs the collisional-map simulation over the model's tuning parameter and
writes one CSV row per (parameter, realization) with all accumulated totals.

Usage (from the workspace folder):
    python scripts/run_scan.py --model cluster --n-seq 500 --n-points 17
    python scripts/run_scan.py --model tfim --n-seq 300 --n-points 13 --realizations 8

Physics constants are fixed to the paper values inside qrc_engine.
"""
from __future__ import annotations

import argparse
import csv
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mackey_glass import generate_mg_sequences  # noqa: E402
from qrc_engine import cluster_hamiltonian, simulate_ensemble, tfim_hamiltonian  # noqa: E402

N_WASH = 500
N_EVAL = 2000
TAUS = (1, 2)      # chi_m(tau=0) is chi_m itself
HS = (2, 3)        # chi_p(h=1) is chi_p itself
MAX_H = 3


def run_one(job: tuple) -> dict:
    model, param, realization, n_seq, seq_seed = job
    t0 = time.time()
    sequences = generate_mg_sequences(n_seq, N_WASH + N_EVAL + MAX_H + 1, seed=seq_seed)
    if model == "cluster":
        H0 = cluster_hamiltonian(6, float(param))
    else:
        rng = np.random.default_rng(10_000 + realization)
        H0 = tfim_hamiltonian(6, float(param), rng)
    totals = simulate_ensemble(H0, sequences, n_wash=N_WASH, n_eval=N_EVAL, taus=TAUS, hs=HS)
    row = {"model": model, "param": float(param), "realization": realization,
           "runtime_s": round(time.time() - t0, 1)}
    row.update({k: v for k, v in totals.items()})
    return row


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", choices=["cluster", "tfim"], required=True)
    parser.add_argument("--n-seq", type=int, default=500)
    parser.add_argument("--n-points", type=int, default=17)
    parser.add_argument("--realizations", type=int, default=1)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    if args.model == "cluster":
        params = np.linspace(0.0, 1.0, args.n_points)
    else:
        params = np.logspace(-1, 2, args.n_points)

    jobs = []
    for i, p in enumerate(params):
        for r in range(args.realizations):
            # independent MG ensembles per job so realizations are uncorrelated
            jobs.append((args.model, p, r, args.n_seq, 1000 * i + r + 1))

    out_path = Path(args.out) if args.out else (
        Path(__file__).resolve().parents[1] / "outputs" / "data" / f"fig2_{args.model}_scan.csv"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)

    t0 = time.time()
    rows = []
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        for k, row in enumerate(pool.map(run_one, jobs)):
            rows.append(row)
            print(f"[{k + 1}/{len(jobs)}] {row['model']} param={row['param']:.4g} "
                  f"real={row['realization']} chi_m={row['chi_m_tot']:.3f} "
                  f"chi_p={row['chi_p_tot']:.3f} bWirr={row['beta_W_irr_tot']:.3f} "
                  f"({row['runtime_s']}s)", flush=True)

    fields = list(rows[0].keys())
    with out_path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {out_path} ({len(rows)} rows) in {time.time() - t0:.0f}s total")

    worst = max(r["identity_residual_max"] for r in rows)
    print(f"max |beta*W_irr_inj - chi_d| over all runs: {worst:.2e}")
    return 0


if __name__ == "__main__":
    main()
