"""Fig. S1 data: accumulation factor G(omega), MG spectrum, and energy spectra.

a) G(omega) via the binning estimator (SI Eq. S43-S44, normalized by sigma_s^2
   as in Eq. S49) plus the ensemble-averaged Fourier power spectrum of the drive;
b) disorder-averaged normalized energy spectrum of the L=6 fully connected TFIM
   vs J (paper: 10000 realizations; reduced locally);
c) energy spectrum of the L=6 augmented cluster model vs alpha (deterministic).

Usage: python scripts/run_figS1.py --n-seq 500 --tfim-realizations 500
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mackey_glass import generate_mg_sequences  # noqa: E402
from qrc_engine import bin_indices, cluster_hamiltonian, tfim_hamiltonian  # noqa: E402

P_TH = 1.0 - np.exp(-0.1)  # gamma0 = 0.1, dt = 1
WORKSPACE = Path(__file__).resolve().parents[1]
DATA_DIR = WORKSPACE / "outputs" / "data"
CHECK_DIR = WORKSPACE / "outputs" / "checks"


def g_factor_binned(sequences: np.ndarray, omegas: np.ndarray, n_wash: int = 500, n_bins: int = 50) -> np.ndarray:
    """Empirical G(omega) = E_{s_n}[ |E[Y(n) | s_n]|^2 ] (SI Eqs. S43-S44) with the
    filtered history Y(n) = sum_m s_m g^{n-m}, g = (1-P_th) e^{-i omega dt}.
    Via the linear estimator (S45-S47) this equals |E[Y s]|^2 / sigma_s^2, whose
    resonance value is the S52 closed form (~2.3 at omega_s)."""
    n_seq, n_total = sequences.shape
    G = np.empty(len(omegas))
    for w_idx, omega in enumerate(omegas):
        g = (1.0 - P_TH) * np.exp(-1j * omega)
        Y = np.zeros(n_seq, dtype=np.complex128)
        num = np.zeros(n_bins, dtype=np.complex128)
        cnt = np.zeros(n_bins)
        acc = 0.0
        n_acc = 0
        for n in range(n_total):
            Y = g * Y + sequences[:, n]
            if n < n_wash:
                continue
            idx = bin_indices(sequences[:, n], n_bins)
            num.fill(0), cnt.fill(0)
            np.add.at(num, idx, Y)
            np.add.at(cnt, idx, 1.0)
            occ = cnt > 0
            means = num[occ] / cnt[occ]
            P_b = cnt[occ] / n_seq
            acc += float(np.sum(P_b * np.abs(means) ** 2))
            n_acc += 1
        G[w_idx] = acc / n_acc
    return G


def mg_power_spectrum(sequences: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Ensemble-averaged Fourier power spectrum F(omega).

    The paper does not publish its normalization; F = |FFT|^2 * 2pi / N^2 puts
    50*F on the same O(1) scale as G(omega) in Fig. S1a (only the shape and the
    peak location carry the panel's message)."""
    N = sequences.shape[1]
    centered = sequences - sequences.mean(axis=1, keepdims=True)
    power = (np.abs(np.fft.rfft(centered, axis=1)) ** 2 * 2.0 * np.pi / N**2).mean(axis=0)
    omega = 2.0 * np.pi * np.fft.rfftfreq(N, d=1.0)
    return omega, power


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-seq", type=int, default=500)
    parser.add_argument("--n-samples", type=int, default=2500)
    parser.add_argument("--tfim-realizations", type=int, default=500)
    parser.add_argument("--n-j", type=int, default=40)
    parser.add_argument("--n-alpha", type=int, default=101)
    parser.add_argument("--omega-points", type=int, default=90)
    parser.add_argument("--output-dir", type=Path, default=DATA_DIR)
    parser.add_argument(
        "--check-path", type=Path, default=CHECK_DIR / "figS1_features.json"
    )
    args = parser.parse_args()
    data_dir = (
        args.output_dir
        if args.output_dir.is_absolute()
        else WORKSPACE / args.output_dir
    )
    check_path = (
        args.check_path
        if args.check_path.is_absolute()
        else WORKSPACE / args.check_path
    )
    data_dir.mkdir(parents=True, exist_ok=True)
    check_path.parent.mkdir(parents=True, exist_ok=True)

    # --- panel a ---------------------------------------------------------
    seqs = generate_mg_sequences(args.n_seq, args.n_samples, seed=42)
    omegas = np.linspace(0.02, 3.0, args.omega_points)
    G = g_factor_binned(seqs, omegas)
    om_f, F = mg_power_spectrum(seqs)
    with (data_dir / "figS1a_g_factor.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["omega", "G"])
        w.writerows(zip(omegas, G))
    with (data_dir / "figS1a_mg_spectrum.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["omega", "power"])
        w.writerows(zip(om_f, F))
    mean_per_step = seqs.mean(axis=0)
    var_per_step = seqs.var(axis=0)
    with (data_dir / "figS1a_insets.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["n", "signal_example", "mean", "variance"])
        for n in range(args.n_samples):
            w.writerow([n, seqs[0, n], mean_per_step[n], var_per_step[n]])

    # --- panel b ---------------------------------------------------------
    Js = np.logspace(-1, 2, args.n_j)
    spec_b = np.empty((args.n_j, 64))
    for j_idx, J in enumerate(Js):
        acc = np.zeros(64)
        for r in range(args.tfim_realizations):
            rng = np.random.default_rng(50_000 + 977 * j_idx + r)
            w = np.linalg.eigvalsh(tfim_hamiltonian(6, float(J), rng))
            center = 0.5 * (w[-1] + w[0])
            width = w[-1] - w[0]
            acc += (w - center) / width
        spec_b[j_idx] = acc / args.tfim_realizations
    with (data_dir / "figS1b_tfim_spectrum.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["J"] + [f"level_{k}" for k in range(64)])
        for j_idx, J in enumerate(Js):
            w.writerow([J] + list(spec_b[j_idx]))

    # --- panel c ---------------------------------------------------------
    alphas = np.linspace(0.0, 1.0, args.n_alpha)
    spec_c = np.array([np.linalg.eigvalsh(cluster_hamiltonian(6, float(a))) for a in alphas])
    with (data_dir / "figS1c_cluster_spectrum.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["alpha"] + [f"level_{k}" for k in range(64)])
        for a_idx, a in enumerate(alphas):
            w.writerow([a] + list(spec_c[a_idx]))

    # --- feature checks --------------------------------------------------
    # The rendered S1c panel is OBC (paper convention). The bulk transition
    # criterion uses the PBC gap; the OBC fingerprints are the asymmetric
    # spectral widths and the alpha=1 edge zero modes (Fig. S1c).
    peak_idx = int(np.argmax(G))
    gaps_pbc = np.array([
        np.diff(np.linalg.eigvalsh(cluster_hamiltonian(6, float(a), pbc=True))[:2])[0]
        for a in alphas
    ])
    width_0 = float(spec_c[0, -1] - spec_c[0, 0])
    width_1 = float(spec_c[-1, -1] - spec_c[-1, 0])
    edge_gap_1 = float(spec_c[-1, 1] - spec_c[-1, 0])
    checks = {
        "schema_version": 1,
        "paper_id": "2607.02157",
        "check": "figS1_features",
        "status": "pending",
        "features": {
            "g_peak_omega": float(omegas[peak_idx]),
            "g_peak_value": float(G[peak_idx]),
            "g_peak_omega_expected": 0.36,
            "g_peak_value_expected": 2.3,
            "mg_spectrum_peak_omega": float(om_f[1 + int(np.argmax(F[1:]))]),
            "cluster_pbc_bulk_min_gap_alpha": float(alphas[int(np.argmin(gaps_pbc))]),
            "cluster_pbc_bulk_min_gap_alpha_expected": 0.5,
            "cluster_obc_width_alpha0": width_0,
            "cluster_obc_width_alpha1": width_1,
            "cluster_obc_edge_gap_alpha1": edge_gap_1,
            "tfim_realizations": args.tfim_realizations,
            "n_seq": args.n_seq,
        },
    }
    ok = (abs(checks["features"]["g_peak_omega"] - 0.36) < 0.1
          and 1.5 < checks["features"]["g_peak_value"] < 3.5
          and abs(checks["features"]["cluster_pbc_bulk_min_gap_alpha"] - 0.5) < 0.1
          and width_0 > width_1 + 2.0
          and edge_gap_1 < 1e-8)
    checks["status"] = "passed" if ok else "failed"
    check_path.write_text(json.dumps(checks, indent=2) + "\n")
    print(json.dumps(checks["features"], indent=2))
    print("status:", checks["status"])
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
