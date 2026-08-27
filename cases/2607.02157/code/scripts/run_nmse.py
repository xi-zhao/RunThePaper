"""NMSE scan (Fig. 2a green curves, Fig. S2c) via the ridge readout.

Reduced-scale deviations from the paper protocol (recorded in TARGET_LEDGER):
- readout basis: all 1- and 2-body Pauli strings (153 features + bias) instead
  of the full 4^6 - 1 Pauli basis;
- fewer averaged sequences than the paper's 500.

Usage: python scripts/run_nmse.py --model cluster --n-seq 32 --n-points 17
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
from qrc_engine import (  # noqa: E402
    build_map_cache,
    cluster_hamiltonian,
    collisional_step,
    eig_map_pieces,
    local_pauli_observables,
    tfim_hamiltonian,
)

N_WASH, N_TRAIN, N_TEST, ETA = 500, 2000, 2000, 1e-5
HORIZONS = (1, 2, 3)


def run_one(job: tuple) -> dict:
    model, param, realization, n_seq, seq_seed = job
    t0 = time.time()
    if model == "cluster":
        H0 = cluster_hamiltonian(6, float(param))
    else:
        rng = np.random.default_rng(10_000 + realization)
        H0 = tfim_hamiltonian(6, float(param), rng)

    sequences = generate_mg_sequences(n_seq, N_WASH + N_TRAIN + N_TEST + max(HORIZONS), seed=seq_seed)
    observables = local_pauli_observables(6)
    cache = build_map_cache(H0, 0.05, 1.0, 1.0, 401)
    P_th = 1.0 - np.exp(-0.1)
    _, rho0, _, _ = eig_map_pieces(H0, 1.0, 1.0)
    D = H0.shape[0]
    rho = np.broadcast_to(rho0, (n_seq, D, D)).copy()

    n_obs = observables.shape[0]
    feats = np.empty((n_seq, N_TRAIN + N_TEST, n_obs))
    for n in range(N_WASH + N_TRAIN + N_TEST):
        rho = collisional_step(rho, sequences[:, n], cache, P_th)
        if n >= N_WASH:
            feats[:, n - N_WASH] = np.real(np.einsum("kab,nba->nk", observables, rho))

    row = {"model": model, "param": float(param), "realization": realization}
    for h in HORIZONS:
        vals = []
        for q in range(n_seq):
            X = np.concatenate([feats[q], np.ones((N_TRAIN + N_TEST, 1))], axis=1)
            targets = sequences[q, N_WASH + h: N_WASH + N_TRAIN + N_TEST + h]
            gram = X[:N_TRAIN].T @ X[:N_TRAIN] + ETA * np.eye(X.shape[1])
            w = np.linalg.solve(gram, X[:N_TRAIN].T @ targets[:N_TRAIN])
            pred = X[N_TRAIN:] @ w
            vals.append(float(np.sum((pred - targets[N_TRAIN:]) ** 2) / np.sum(targets[N_TRAIN:] ** 2)))
        row[f"nmse_h{h}"] = float(np.mean(vals))
    row["runtime_s"] = round(time.time() - t0, 1)
    return row


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", choices=["cluster", "tfim"], required=True)
    parser.add_argument("--n-seq", type=int, default=32)
    parser.add_argument("--n-points", type=int, default=17)
    parser.add_argument("--realizations", type=int, default=1)
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()

    params = np.linspace(0.0, 1.0, args.n_points) if args.model == "cluster" else np.logspace(-1, 2, args.n_points)
    jobs = [(args.model, p, r, args.n_seq, 7000 + 100 * i + r)
            for i, p in enumerate(params) for r in range(args.realizations)]

    out_path = Path(__file__).resolve().parents[1] / "outputs" / "data" / f"nmse_{args.model}_scan.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        for k, row in enumerate(pool.map(run_one, jobs)):
            rows.append(row)
            print(f"[{k + 1}/{len(jobs)}] param={row['param']:.4g} real={row['realization']} "
                  f"nmse_h1={row['nmse_h1']:.4g} ({row['runtime_s']}s)", flush=True)
    with out_path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {out_path} ({len(rows)} rows)")
    return 0


if __name__ == "__main__":
    main()
