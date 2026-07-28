"""Numeric verification of the equation cards for arXiv:2607.02157.

Every EQC*_ check declared in EQUATION_CARDS.json is implemented here; the
script writes outputs/checks/formula_check_details.json and exits non-zero
if any check fails. Run from the workspace folder:

    python scripts/verify_formulas.py
"""
from __future__ import annotations

import json
import sys

import numpy as np

from runtime_layout import CASE_ROOT, SOURCE_DIR

sys.path.insert(0, str(SOURCE_DIR))
from mackey_glass import generate_mg_sequences, sequence_statistics  # noqa: E402
from qrc_engine import (  # noqa: E402
    binned_states,
    build_map_cache,
    cluster_hamiltonian,
    coherence_terms,
    collisional_step,
    eig_map_pieces,
    holevo_capacity,
    relative_entropy,
    shannon_entropy,
    von_neumann_entropy,
)

RESULTS: list[dict] = []


def record(check_id: str, passed: bool, detail: str) -> None:
    RESULTS.append({"id": check_id, "status": "passed" if passed else "failed", "detail": detail})
    print(("PASS " if passed else "FAIL ") + check_id + ": " + detail)


def random_density(rng: np.random.Generator, d: int) -> np.ndarray:
    A = rng.normal(size=(d, d)) + 1j * rng.normal(size=(d, d))
    rho = A @ A.conj().T
    return rho / np.trace(rho).real


def random_hermitian(rng: np.random.Generator, d: int) -> np.ndarray:
    A = rng.normal(size=(d, d)) + 1j * rng.normal(size=(d, d))
    return (A + A.conj().T) / 2.0


def check_map_cptp() -> None:
    rng = np.random.default_rng(11)
    L, beta, gamma0, dt, lam = 3, 1.0, 0.1, 1.0, 0.05
    H0 = random_hermitian(rng, 2**L)
    cache = build_map_cache(H0, lam, dt, beta, n_grid=101)
    P_th = 1.0 - np.exp(-gamma0 * dt)
    rho = np.stack([random_density(rng, 2**L) for _ in range(8)])
    s = rng.uniform(-1, 1, size=8)
    out = collisional_step(rho, s, cache, P_th)
    trace_err = float(np.max(np.abs(np.einsum("nii->n", out) - 1.0)))
    min_eig = float(np.min(np.linalg.eigvalsh(out)))
    record("EQC001_cptp", trace_err < 1e-10 and min_eig > -1e-10,
           f"trace_err={trace_err:.2e}, min_eig={min_eig:.2e}")

    idx = cache.index(np.array([0.3]))[0]
    rho_eq = cache.rho_eq[idx]
    out_eq = collisional_step(rho_eq[None], cache.s_grid[idx][None], cache, P_th)[0]
    gibbs_err = float(np.max(np.abs(out_eq - rho_eq)))
    record("EQC001_gibbs_invariant", gibbs_err < 1e-10, f"|E(rho_eq)-rho_eq|_max={gibbs_err:.2e}")


def check_mg_stats() -> None:
    seqs = generate_mg_sequences(64, 3000, seed=3)
    stats = sequence_statistics(seqs)
    ok = (abs(stats["mean"]) < 0.02
          and abs(stats["variance"] - 0.11) < 0.015
          and 0.25 < stats["omega_peak"] < 0.45
          and float(np.abs(seqs).max()) <= 1.0)
    record("EQC002_stats", ok,
           f"mean={stats['mean']:.3f}, var={stats['variance']:.3f}, omega_peak={stats['omega_peak']:.3f}, "
           f"max|s|={float(np.abs(seqs).max()):.2f} (paper: ~0, ~0.11, ~0.36, within [-1,1])")


def random_ensemble(rng: np.random.Generator, d: int, n: int):
    P = rng.dirichlet(np.ones(n))
    states = np.stack([random_density(rng, d) for _ in range(n)])
    return P, states


def check_holevo_recast() -> None:
    rng = np.random.default_rng(21)
    P, states = random_ensemble(rng, 6, 9)
    rho_bar = np.einsum("b,bij->ij", P, states)
    chi_direct = holevo_capacity(rho_bar, P, states)
    chi_relent = float(np.sum([P[b] * relative_entropy(states[b], rho_bar) for b in range(len(P))]))
    err = abs(chi_direct - chi_relent)
    record("EQC003_recast", err < 1e-9, f"|entropy-form - relative-entropy-form|={err:.2e}")


def check_marginalization() -> None:
    rng = np.random.default_rng(31)
    n = 400
    states = np.stack([random_density(rng, 4) for _ in range(n)])
    s_n = rng.uniform(-1, 1, n)
    s_np1 = rng.uniform(-1, 1, n)
    rho_bar = states.mean(axis=0)
    P_m, rho_m, _ = binned_states(states, s_n, 10)
    P_p, rho_p, _ = binned_states(states, s_np1, 10)
    err_m = float(np.max(np.abs(np.einsum("b,bij->ij", P_m, rho_m) - rho_bar)))
    err_p = float(np.max(np.abs(np.einsum("b,bij->ij", P_p, rho_p) - rho_bar)))
    record("EQC004_marginalization", max(err_m, err_p) < 1e-12,
           f"memory-avg err={err_m:.2e}, predictive-avg err={err_p:.2e}")


def check_qid_definition() -> None:
    """Verify that the QID difference is the conditional-entropy excess.

    The two ensembles have the same unconditional state, so the entropy of
    that shared state cancels between their Holevo quantities.
    """
    rng = np.random.default_rng(36)
    P_m, rho_m, P_p, rho_p = paired_ensembles(rng, 6, 8, 5)
    rho_bar = np.einsum("b,bij->ij", P_m, rho_m)
    qid_from_capacities = (
        holevo_capacity(rho_bar, P_m, rho_m)
        - holevo_capacity(rho_bar, P_p, rho_p)
    )
    qid_from_conditional_entropies = float(
        np.sum(P_p * von_neumann_entropy(rho_p))
        - np.sum(P_m * von_neumann_entropy(rho_m))
    )
    err = abs(qid_from_capacities - qid_from_conditional_entropies)
    record(
        "EQC005_definition",
        err < 1e-9,
        f"|Holevo difference - conditional-entropy difference|={err:.2e}",
    )


def check_coherence_split() -> None:
    rng = np.random.default_rng(41)
    P, states = random_ensemble(rng, 6, 8)
    rho_bar = np.einsum("b,bij->ij", P, states)
    chi = holevo_capacity(rho_bar, P, states)
    I_cl, C_ens, _ = coherence_terms(rho_bar, P, states)
    err = abs(chi - (I_cl + C_ens))
    record("EQC006_split", err < 1e-9 and C_ens > -1e-10 and chi >= I_cl - 1e-10,
           f"|chi-(I+C)|={err:.2e}, C={C_ens:.4f}, chi-I={chi - I_cl:.4f}")


def paired_ensembles(rng: np.random.Generator, d: int, n_m: int, n_p: int):
    """Memory ensemble + predictive ensemble sharing the same average state."""
    P_m, states_m = random_ensemble(rng, d, n_m)
    # joint distribution with marginal P_m over memory index
    Q = rng.dirichlet(np.ones(n_p), size=n_m) * P_m[:, None]
    P_p = Q.sum(axis=0)
    states_p = np.einsum("mp,mij->pij", Q, states_m) / P_p[:, None, None]
    return P_m, states_m, P_p, states_p


def check_qid_split() -> None:
    rng = np.random.default_rng(51)
    P_m, rho_m, P_p, rho_p = paired_ensembles(rng, 6, 7, 5)
    rho_bar = np.einsum("b,bij->ij", P_m, rho_m)
    chi_m = holevo_capacity(rho_bar, P_m, rho_m)
    chi_p = holevo_capacity(rho_bar, P_p, rho_p)
    I_m, _, Cc_m = coherence_terms(rho_bar, P_m, rho_m)
    I_p, _, Cc_p = coherence_terms(rho_bar, P_p, rho_p)
    D_c = I_m - I_p
    D_q = Cc_m - Cc_p
    err = abs((chi_m - chi_p) - (D_c + D_q))
    record("EQC007_split", err < 1e-9, f"|chi_d-(D_c+D_q)|={err:.2e}")


def check_injection_work_conditioning() -> None:
    """Check that conditional-state work equals a direct trajectory average."""
    rng = np.random.default_rng(56)
    n, d, lam = 600, 6, 0.05
    states = np.stack([random_density(rng, d) for _ in range(n)])
    current_labels = rng.integers(0, 7, size=n)
    next_labels = rng.integers(0, 5, size=n)
    current_values = np.linspace(-0.9, 0.9, 7)
    next_values = np.linspace(-0.8, 0.8, 5)
    H0 = random_hermitian(rng, d)
    drive = np.diag(rng.normal(size=d))

    def hamiltonian(signal: float) -> np.ndarray:
        return H0 + lam * signal * drive

    direct = 0.0
    for index, rho in enumerate(states):
        H_before = hamiltonian(float(current_values[current_labels[index]]))
        H_after = hamiltonian(float(next_values[next_labels[index]]))
        direct += float(np.trace(rho @ (H_after - H_before)).real) / n

    def conditional_energy(labels: np.ndarray, values: np.ndarray) -> float:
        total = 0.0
        for label, signal in enumerate(values):
            selected = states[labels == label]
            if len(selected) == 0:
                continue
            probability = len(selected) / n
            conditional_state = selected.mean(axis=0)
            total += probability * float(
                np.trace(conditional_state @ hamiltonian(float(signal))).real
            )
        return total

    conditional = (
        conditional_energy(next_labels, next_values)
        - conditional_energy(current_labels, current_values)
    )
    err = abs(direct - conditional)
    record(
        "EQC008_conditioning",
        err < 1e-12,
        f"|trajectory-average work - conditional-state work|={err:.2e}",
    )


def check_work_identity() -> None:
    rng = np.random.default_rng(61)
    beta, lam = 1.0, 0.05
    d = 8
    P_m, rho_m, P_p, rho_p = paired_ensembles(rng, d, 8, 6)
    rho_bar = np.einsum("b,bij->ij", P_m, rho_m)
    H0 = random_hermitian(rng, d)
    z = rng.normal(size=d)
    s_m = rng.uniform(-1, 1, len(P_m))
    s_p = rng.uniform(-1, 1, len(P_p))

    def energy(P, rho, s):
        e0 = np.real(np.einsum("bij,ji->b", rho, H0))
        ez = np.real(np.einsum("bii,i->b", rho, z))
        return float(np.sum(P * (e0 + lam * s * ez)))

    E_p, E_m = energy(P_p, rho_p, s_p), energy(P_m, rho_m, s_m)
    S_p = float(np.sum(P_p * von_neumann_entropy(rho_p)))
    S_m = float(np.sum(P_m * von_neumann_entropy(rho_m)))
    W = E_p - E_m
    delta_F = (E_p - S_p / beta) - (E_m - S_m / beta)
    beta_W_irr = beta * (W - delta_F)
    chi_d = holevo_capacity(rho_bar, P_m, rho_m) - holevo_capacity(rho_bar, P_p, rho_p)
    err = abs(beta_W_irr - chi_d)
    record("EQC009_identity", err < 1e-9, f"|beta*W_irr - chi_d|={err:.2e}")


def check_relax_nonneg() -> None:
    rng = np.random.default_rng(71)
    d = 8
    H = random_hermitian(rng, d)
    U, rho_eq, _, _ = eig_map_pieces(H, 1.0, 1.0)
    P_th = 1.0 - np.exp(-0.1)
    worst = np.inf
    for _ in range(20):
        rho = random_density(rng, d)
        rho2 = (1 - P_th) * (U @ rho @ U.conj().T) + P_th * rho_eq
        worst = min(worst, relative_entropy(rho, rho_eq) - relative_entropy(rho2, rho_eq))
    record("EQC010_monotonicity", worst > -1e-9,
           f"min decrease of S(rho||rho_eq) over 20 random states = {worst:.3e} (must be >= 0)")


def check_bkm_integral() -> None:
    rng = np.random.default_rng(81)
    worst = 0.0
    for _ in range(10):
        p, q = rng.uniform(0.01, 1.0, 2)
        if abs(p - q) < 1e-3:
            q = p + 0.1
        x = np.linspace(0, 4000, 4_000_001)
        integrand = 1.0 / ((p + x) * (q + x))
        numeric = float(np.trapezoid(integrand, x))
        closed = float(np.log(p / q) / (p - q))
        worst = max(worst, abs(numeric - closed) / abs(closed))
    record("EQC011_partial_fraction", worst < 1e-3, f"max rel err over 10 draws = {worst:.2e}")


def bkm_metric(rho_bar: np.ndarray, drho: np.ndarray) -> float:
    w, V = np.linalg.eigh(rho_bar)
    w = np.clip(np.real(w), 1e-14, None)
    d_eig = V.conj().T @ drho @ V
    num = np.log(w[:, None]) - np.log(w[None, :])
    den = w[:, None] - w[None, :]
    kernel = np.where(np.abs(den) > 1e-12, num / np.where(np.abs(den) > 1e-12, den, 1.0), 1.0 / w[:, None])
    return float(np.real(np.sum(np.abs(d_eig) ** 2 * kernel)))


def check_bkm_quadratic() -> None:
    rng = np.random.default_rng(91)
    d = 6
    rho_bar = 0.7 * random_density(rng, d) + 0.3 * np.eye(d) / d  # keep spectrum away from 0
    A = random_hermitian(rng, d)
    drho = A - np.trace(A).real * rho_bar  # traceless perturbation
    drho = (drho + drho.conj().T) / 2

    def rel_err(lam: float) -> float:
        S_rel = relative_entropy(rho_bar + lam * drho, rho_bar)
        quad = 0.5 * lam**2 * bkm_metric(rho_bar, drho)
        return abs(S_rel - quad) / quad

    e3, e4 = rel_err(1e-3), rel_err(1e-4)
    # third-order remainder => relative error shrinks linearly in lambda
    record("EQC011_quadratic", e4 < 1e-2 and e4 < 0.3 * e3,
           f"rel_err(1e-3)={e3:.2e}, rel_err(1e-4)={e4:.2e} (linear shrink confirms O(lambda^3) remainder)")


def check_g_peak() -> None:
    sigma_s2, P_th, gamma_s_dt, omega_s, dt = 0.11, 0.095, 0.015, 0.36, 1.0
    closed = sigma_s2 / (4.0 * (P_th + gamma_s_dt) ** 2)
    taus = np.arange(0, 4000)
    C_a = sigma_s2 * np.cos(omega_s * taus * dt) * np.exp(-gamma_s_dt * taus)
    g = (1 - P_th) * np.exp(-1j * omega_s * dt)
    numeric = float(np.abs(np.sum(C_a * g**taus)) ** 2 / sigma_s2)
    rel = abs(numeric - closed) / closed
    ok = rel < 0.35 and 1.8 < closed < 2.8
    record("EQC012_peak_value", ok,
           f"closed-form G(omega_s)={closed:.2f} (paper ~2.3), full sum={numeric:.2f}, rel gap={rel:.2f} "
           "(closed form keeps only the co-rotating term)")


def check_cluster_gap() -> None:
    # Bulk criterion (PBC): gap minimum at the alpha = 0.5 transition.
    alphas = np.linspace(0.05, 0.95, 19)
    gaps_pbc = []
    for a in alphas:
        w = np.linalg.eigvalsh(cluster_hamiltonian(6, float(a), pbc=True))
        gaps_pbc.append(w[1] - w[0])
    a_min = float(alphas[int(np.argmin(gaps_pbc))])

    # Boundary-condition fingerprint (OBC, the paper's convention): asymmetric
    # spectral widths matching Fig. S1c and SPT edge zero modes at alpha = 1.
    w0 = np.linalg.eigvalsh(cluster_hamiltonian(6, 0.0))
    w1 = np.linalg.eigvalsh(cluster_hamiltonian(6, 1.0))
    width0, width1 = float(w0[-1] - w0[0]), float(w1[-1] - w1[0])
    edge_gap = float(w1[1] - w1[0])

    ok = abs(a_min - 0.5) <= 0.15 and width0 > width1 + 2.0 and edge_gap < 1e-8
    record("EQC013_gap_closing", ok,
           f"PBC bulk-gap minimum at alpha={a_min:.2f} (expect 0.5); OBC widths "
           f"{width0:.2f} (alpha=0) vs {width1:.2f} (alpha=1) match Fig. S1c asymmetry; "
           f"OBC alpha=1 edge-mode gap={edge_gap:.1e}")


def check_ridge_normal_equations() -> None:
    """Independently verify the ridge closed form and NMSE definition."""
    rng = np.random.default_rng(96)
    n_samples, n_features, eta = 80, 12, 1e-5
    X = rng.normal(size=(n_samples, n_features))
    target = rng.normal(size=n_samples)
    gram = X.T @ X + eta * np.eye(n_features)
    weights = np.linalg.solve(gram, X.T @ target)
    gradient = X.T @ (X @ weights - target) + eta * weights
    gradient_norm = float(np.linalg.norm(gradient))

    def objective(candidate: np.ndarray) -> float:
        residual = X @ candidate - target
        return float(residual @ residual + eta * (candidate @ candidate))

    perturbations = rng.normal(scale=1e-3, size=(20, n_features))
    objective_gap = min(
        objective(weights + perturbation) - objective(weights)
        for perturbation in perturbations
    )
    prediction = X @ weights
    nmse = float(np.sum((prediction - target) ** 2) / np.sum(target**2))
    ok = gradient_norm < 1e-9 and objective_gap > -1e-10 and nmse >= 0.0
    record(
        "EQC014_ridge_solution",
        ok,
        f"normal-equation residual={gradient_norm:.2e}, "
        f"min perturbed objective gap={objective_gap:.2e}, NMSE={nmse:.3f}",
    )


def check_coherence_convexity() -> None:
    rng = np.random.default_rng(101)
    worst = np.inf
    for _ in range(20):
        P, states = random_ensemble(rng, 6, 5)
        mix = np.einsum("b,bij->ij", P, states)
        def C(r):
            return float(shannon_entropy(np.real(np.diag(r))) - von_neumann_entropy(r[None])[0])
        worst = min(worst, float(np.sum([P[b] * C(states[b]) for b in range(len(P))])) - C(mix))
    record("EQC015_convexity", worst > -1e-9,
           f"min of sum P C(rho) - C(mixture) over 20 draws = {worst:.3e} (must be >= 0)")


def main() -> int:
    check_map_cptp()
    check_mg_stats()
    check_holevo_recast()
    check_marginalization()
    check_qid_definition()
    check_coherence_split()
    check_qid_split()
    check_injection_work_conditioning()
    check_work_identity()
    check_relax_nonneg()
    check_bkm_integral()
    check_bkm_quadratic()
    check_g_peak()
    check_cluster_gap()
    check_ridge_normal_equations()
    check_coherence_convexity()

    failed = [r for r in RESULTS if r["status"] != "passed"]
    payload = {
        "schema_version": 1,
        "paper_id": "2607.02157",
        "check": "formula_check_details",
        "status": "passed" if not failed else "failed",
        "results": RESULTS,
    }
    out = CASE_ROOT / "outputs" / "checks" / "formula_check_details.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} checks passed -> {out}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
