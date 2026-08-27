# Numerical Methods

## Method Cards

### NUM001 — Collisional-map ensemble simulation (T001/T003)

- Target: Fig. 2 (a1-c2), Fig. S2 (a1-c2)
- Equations/method cards: EQC001-EQC010, EQC013 (EQUATION_CARDS.json)
- Parameters: L=6, beta=1, gamma0=0.1, dt=1, lambda=0.05, B=50 bins,
  N_wash=500, N_eval=2000; MG drive (0.2, 0.1, 18), sampled every 3,
  centered with sigma_s^2=0.11 (EQC002 assumption).
- Grid or benchmark: cluster alpha in linspace(0,1,17); TFIM J in
  logspace(-1,2,13) with reduced disorder realizations (reduced-scale pass).
- Boundary conditions: cluster chain periodic (EQC013 open question); TFIM
  fully connected (no boundary).
- Solver: exact dense linear algebra on 64x64 matrices; per-step propagator
  and Gibbs state looked up from a 401-point s-grid cache built by
  eigendecomposition (see PERFORMANCE_PROFILE.md for validation).
- Tolerance: eigenvalue truncation 1e-12 in all entropies (paper protocol);
  cache-vs-exact state deviation 1.3e-5 after 200 steps (checked).
- Random seed: MG seeds 1000*i+r+1 per (parameter i, realization r); TFIM
  disorder seeds 10000+r (run_scan.py); deterministic reruns.
- Output schema: one CSV row per (param, realization) with accumulated totals
  chi_m_tot, chi_p_tot, chi_d_tot, I_m/p_tot, C_m/p_tot, beta_W_irr_tot,
  beta_W_relax_tot, chi_m_tau{1,2}_tot, chi_p_h{2,3}_tot,
  identity_residual_max (outputs/data/fig2_*_scan.csv).
- Validation checks: per-step identity beta*W_irr_inj == chi_d (machine
  precision, asserted over every run); chi >= I hierarchy; Landauer
  beta*W_irr_tot >= chi_d_tot; ensemble marginalization (memory and predictive
  bins average to the same state).
- Numerical risks: finite-ensemble bias of the binned Holevo estimator
  (fewer samples per bin than the paper's ~100); drive-normalization
  convention (EQC002); reduced disorder averaging for the TFIM row.

### NUM002 — Ridge readout / NMSE (T001 green curves, T003 panel c)

- Target: Fig. 2a NMSE curves, Fig. S2c
- Equations/method cards: EQC014
- Parameters: N_wash=500, N_train=2000, N_test=2000, eta=1e-5, horizons 1-3.
- Deviation: readout basis reduced to all 1- and 2-body Pauli strings
  (153 features + bias) instead of the full 4^6-1 Pauli basis; fewer
  sequences than the paper's 500. Recorded in TARGET_LEDGER.md.
- Solver: normal-equation ridge regression per sequence, averaged NMSE.
- Numerical risks: reduced feature basis raises the absolute NMSE floor;
  only the *shape* (minimum inside the critical region) is compared.

### NUM003 — Spectral analytics (T002)

- Target: Fig. S1 (a, b, c)
- Equations/method cards: EQC002, EQC012, EQC013
- Parameters: G(omega) on 90 points in [0.02, 3]; filtered history with
  g = (1-P_th)e^{-i omega dt}; binned conditional means (B=50). TFIM spectra:
  40 log-spaced J, reduced realizations, levels normalized by spectral width
  and averaged sorted; cluster spectrum on 101 alpha points (deterministic).
- Validation checks: G peak location ~0.36 and value vs the S52 closed form
  (~2.3); MG spectral peak location; cluster gap minimum at alpha=0.5
  (outputs/checks/figS1_features.json).
- Numerical risks: F(omega) plot normalization is an assumed convention
  (paper does not publish it); averaged sorted levels are a proxy for the
  paper's unspecified spectral-average procedure in S1b.

## Efficiency And Reuse Plan

- Baseline implementation: exact per-step eigendecomposition of H(s_n) for
  every sequence and step (correct but ~4x slower).
- Main bottleneck: 2^L eigendecompositions per sequence-step and per-bin
  entropy eigenvalue problems.
- Efficient implementation choice: 401-point s-grid propagator/Gibbs cache
  (drive enters only through s*lambda*diag(z)); single entropy pass per
  binning; Gibbs relative entropies computed analytically from energies
  (no extra diagonalization).
- Complexity or scaling: evolution O(n_seq * D^2) matmuls per step; metrics
  O(B * D^3) per binning per step, independent of n_seq.
- Performance bottleneck removed: redundant eigendecompositions (cache) and
  duplicated bin-entropy passes.
- Optional harness promotion candidate: none yet — the batched collisional-map
  pattern is paper-specific until a second collision-model case appears.
- Case-specific parts that should not enter the harness: Hamiltonians, drive
  statistics, binning estimator conventions.
- Performance evidence: smoke unit (L=6, 100 seqs, 600 steps): 52 s exact ->
  21 s optimized with identical outputs to print precision; cache-vs-exact
  state deviation 1.3e-5 after 200 steps.
