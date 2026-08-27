# Method Trace

## METHOD001 — cumulant fixed points and stability

- Source: main text plus accessible arXiv v1 supplement equations.
- Role: analytic branches, instability threshold, and Bogoliubov spectra.
- Inputs: omega_c, omega_a, kappa1, kappa2, lambda.
- Outputs: fixed-point observables, residuals, Jacobian eigenvalues.
- Algorithm: derive polynomial/root candidates, substitute them into the full
  printed equations, differentiate the same equations, and classify each
  non-neutral eigenvalue.
- Code: `src/dicke.py`; `scripts/run_analytic.py`.
- Checks: threshold identity, fixed-point residual <=6.1e-14, branch endpoint
  identity, physical-real Jacobian spectrum, and cubic zero-mode coefficient.
- Status: verified, with a confirmed paper branch-to-spectrum/Bogoliubov-
  evidence discrepancy documented in `PAPER_DISCREPANCY.md`.
- Open question: whether the authors paired the plotted squeezed-high ordinate
  with another root's spectrum or intended to report nonlinear instability.

## METHOD002 — finite-system open quantum dynamics

- Source: printed Hamiltonian, jumps, and arXiv v1 quantum-trajectory method.
- Role: Fock distributions, photon/spin means, and reduced photon states.
- Inputs: N, photon cutoff M, losses, coupling, final time, trajectory count,
  and deterministic seed range.
- Outputs: generated density matrices and cumulative ensemble summaries.
- Algorithm: construct the symmetric-spin tensor Hilbert space, draw one dense
  Haar initial ket independently for every integer-indexed trajectory, evolve
  the stochastic paths, average projectors online, then trace out the spin
  subsystem. The paper-scale implementation shards those integer indices and
  fails closed on gaps or overlap.
- Code: `src/paper_scale_trajectories.py` and
  `scripts/run_paper_scale_trajectories.py`; the older
  `src/dicke.py::trajectory_density` remains the historical reduced runner.
- Checks: trace, density positivity, photon-cutoff tail, frozen seeds, and
  access-log attestation.
- Status: paper-scale code ready; the corrected path is isolated-smoke
  attested, while the 500/3000-trajectory production campaign remains compute
  deferred. The historical
  `quantum-main-feature-v3` run shared one random initial ket across every
  trajectory in a job, contrary to the printed per-trajectory randomization
  rule. That reproduction defect is recorded in `REPRODUCTION_DEFECTS.json`,
  and the historical arrays are not promoted as convergence evidence. The
  corrected execution proof is
  `outputs/runs/2412.14271-quantum-main-paper-scale-smoke-v4-20260825/run_attestation.json`.
- Open question: the published integration time and seed policy are not stated.

## METHOD003 — Wigner transform

- Source: standard Wigner transform applied to the generated reduced photon state.
- Role: Fig. 4 phase-space panels.
- Inputs: frozen reduced photon density matrices and a declared x/p grid.
- Outputs: six Wigner fields.
- Algorithm: evaluate the transform without consulting source pixels; source
  images are opened only in the later RenderContract lane.
- Code: `src/dicke.py::photon_wigner`; `scripts/render_figures.py`.
- Checks: integral error <=7.1e-4 and Z4 rotational residual by job.
- Status: feature-level; low trajectory counts leave residual 0.13-0.62.

## METHOD004 — Liouvillian kernel and parity sectors

- Source: printed pair-loss model and parity argument in the accessible supplement.
- Role: parity-protected steady-state degeneracy.
- Inputs: N=4, M=50, kappa2=0.05, lambda=0.85, kappa1=0.
- Outputs: near-zero Liouvillian eigenvalues and even/odd photon distributions.
- Algorithm: sparse shift-invert near zero plus independent trajectories from
  initial Fock states 15 and 10.
- Code: `src/dicke.py::liouvillian_near_zero_eigenvalues` and parity helpers.
- Checks: kernel rank=2, eigenvalue residual near zero, parity leakage=0.
- Status: paper-exact parameters and invariants verified; fresh review pending.
