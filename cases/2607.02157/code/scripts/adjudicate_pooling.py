"""Adjudicate the TFIM disorder-ensemble aggregation convention.

Runs R disorder realizations at one J and computes the memory-side
quantities (chi_m, I_m, C_m) under both readings of the paper's protocol:

- per_real: entropies per realization, then averaged (our campaign convention);
- pooled:  all R*S trajectories form one mixed ensemble; rho_bar and the
           measurement bins aggregate across realizations before any entropy.

If the pooled numbers land on the paper's axis-calibrated Fig. 2 readings
(chi_m ~1.9-2.0, C_m ~0.72-0.75 at the peak), the paper used the pooled
convention and the campaign row difference is a convention, not an error.

Usage: python adjudicate_pooling.py [--J 2.371] [--reals 20] [--n-seq 500]
"""
from __future__ import annotations

import argparse
import json
import sys

import numpy as np
import torch

from runtime_layout import SOURCE_DIR

sys.path.insert(0, str(SOURCE_DIR))
import qrc_gpu
from qrc_gpu import (
    MAX_H, N_BINS, N_EVAL, N_WASH, build_cache, device_auto,
    entropy, generate_mg_sequences, shannon, tfim_hamiltonian,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--J", type=float, default=2.3714)
    parser.add_argument("--reals", type=int, default=20)
    parser.add_argument("--n-seq", type=int, default=500)
    parser.add_argument("--cupy-eig", action="store_true")
    args = parser.parse_args()
    if args.cupy_eig:
        import cupy
        qrc_gpu._cupy = cupy
        qrc_gpu.CUPY_EIG = True
    torch.set_grad_enabled(False)

    device = device_auto()
    R, S = args.reals, args.n_seq
    lam, beta, gamma0, dt, G = 0.05, 1.0, 0.1, 1.0, 401
    P_th = 1.0 - np.exp(-gamma0 * dt)

    H0_list = [tfim_hamiltonian(6, args.J, np.random.default_rng(10_000 + r)) for r in range(R)]
    seq_list = [generate_mg_sequences(S, N_WASH + N_EVAL + MAX_H + 1, seed=1000 * 11 + r + 1)
                for r in range(R)]

    caches = [build_cache(H, lam, dt, beta, G, device) for H in H0_list]
    D = caches[0]["H0"].shape[-1]
    U_flat = torch.stack([c["U"] for c in caches]).reshape(-1, D, D)
    EQ_flat = torch.stack([c["rho_eq"] for c in caches]).reshape_as(U_flat)
    seqs = torch.as_tensor(np.stack(seq_list), dtype=torch.float64, device=device)
    r_idx = torch.arange(R, device=device).repeat_interleave(S)
    rho = torch.stack([c["rho0"] for c in caches]).repeat_interleave(S, dim=0).clone()
    ones = torch.ones(R * S, dtype=torch.float64, device=device)
    NBP = R * N_BINS

    acc = {f"{k}_{mode}": torch.zeros((), dtype=torch.float64, device=device)
           for k in ("chi_m", "I_m", "C_m") for mode in ("per_real", "pooled")}

    def grid_index(s_flat):
        return torch.clamp(torch.round((s_flat + 1.0) * (G - 1) / 2.0).long(), 0, G - 1)

    def bins_of(s_flat):
        return torch.clamp(((s_flat + 1.0) * 0.5 * N_BINS).long(), 0, N_BINS - 1)

    for n in range(N_WASH + N_EVAL):
        s_flat = seqs[:, :, n].reshape(-1)
        flat_idx = r_idx * G + grid_index(s_flat)
        U = U_flat[flat_idx]
        rho = (1.0 - P_th) * (U @ rho @ U.conj().transpose(-2, -1)) + P_th * EQ_flat[flat_idx]
        if n < N_WASH:
            continue

        b = bins_of(s_flat)

        # --- per-realization convention (campaign) --------------------
        gidx = r_idx * N_BINS + b
        counts = torch.zeros(NBP, dtype=torch.float64, device=device)
        counts.index_add_(0, gidx, ones)
        sums = torch.zeros(NBP, D * D, dtype=rho.dtype, device=device)
        sums.index_add_(0, gidx, rho.reshape(R * S, -1))
        P_b = counts / S
        rho_b = (sums / torch.clamp(counts, min=1.0).to(rho.dtype)[:, None]).reshape(NBP, D, D)
        S_b = entropy(rho_b)
        H_b = shannon(torch.diagonal(rho_b, dim1=-2, dim2=-1).real)

        rho_bar = torch.zeros(R, D * D, dtype=rho.dtype, device=device)
        rho_bar.index_add_(0, r_idx, rho.reshape(R * S, -1))
        rho_bar = (rho_bar / S).reshape(R, D, D)
        S_bar = entropy(rho_bar)
        H_bar = shannon(torch.diagonal(rho_bar, dim1=-2, dim2=-1).real)

        chi_r = S_bar - (P_b * S_b).reshape(R, N_BINS).sum(dim=1)
        I_r = H_bar - (P_b * H_b).reshape(R, N_BINS).sum(dim=1)
        C_r = (P_b * (H_b - S_b)).reshape(R, N_BINS).sum(dim=1) - (H_bar - S_bar)
        acc["chi_m_per_real"] += chi_r.mean()
        acc["I_m_per_real"] += I_r.mean()
        acc["C_m_per_real"] += C_r.mean()

        # --- pooled convention (candidate paper reading) --------------
        counts_p = torch.zeros(N_BINS, dtype=torch.float64, device=device)
        counts_p.index_add_(0, b, ones)
        sums_p = torch.zeros(N_BINS, D * D, dtype=rho.dtype, device=device)
        sums_p.index_add_(0, b, rho.reshape(R * S, -1))
        P_bp = counts_p / (R * S)
        rho_bp = (sums_p / torch.clamp(counts_p, min=1.0).to(rho.dtype)[:, None]).reshape(N_BINS, D, D)
        S_bp = entropy(rho_bp)
        H_bp = shannon(torch.diagonal(rho_bp, dim1=-2, dim2=-1).real)

        rho_bar_p = rho.reshape(R * S, D * D).mean(dim=0).reshape(1, D, D)
        S_bar_p = entropy(rho_bar_p)[0]
        H_bar_p = shannon(torch.diagonal(rho_bar_p, dim1=-2, dim2=-1).real)[0]

        acc["chi_m_pooled"] += S_bar_p - (P_bp * S_bp).sum()
        acc["I_m_pooled"] += H_bar_p - (P_bp * H_bp).sum()
        acc["C_m_pooled"] += (P_bp * (H_bp - S_bp)).sum() - (H_bar_p - S_bar_p)

    out = {k: float(v) for k, v in acc.items()}
    out.update({"J": args.J, "reals": R, "n_seq": S,
                "paper_reading": {"chi_m": "1.9-2.0", "C_m": "0.72-0.75"}})
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
