# Numerical Methods

## `T001` — SWAP-dephasing quasi-sampling

- Equations: `EQC001`, `EQC003`–`EQC006`.
- Methods: `METHOD001`, `METHOD002`.
- Physical parameters:
  - \(\lambda=0.5\);
  - initial state \(|01\rangle\);
  - observable \(|01\rangle\langle01|\);
  - \(t=0,0.1,\ldots,10\).
- Sampling parameters:
  - 1000 outer cycles;
  - 200 inner HPTP samples;
  - generated repeatability seed `251208279`.
- Convex subproblem: decompose one fixed \(8\to4\) HPTP processor into two
  CPTP channels by two \(32\times32\) Choi variables.
- Solver policy: use CVXPY with an installed open-source conic solver; record
  solver name, version, tolerances, residuals, iterations, and wall time.
- Output schema:
  - CSV columns for time, analytic overlap, direct-Liouvillian overlap,
    sampled overlap, standard error, and confidence bounds;
  - JSON for \(p_\pm\), \(\kappa\), Choi residuals, random seed, and timing.
- Validation:
  - analytic/direct maximum error \(\le10^{-11}\);
  - Hermiticity and trace residuals \(\le10^{-8}\), unless the measured solver
    tolerance is larger and explicitly reported;
  - \(p_+-p_-=1\) within solver tolerance;
  - sampled residual root-mean-square no larger than three aggregate standard
    errors and no unexplained systematic bias.
- Numerical risks:
  - a signed estimator can leave the physical interval on individual shots;
    only its expectation is a physical observable;
  - using equal branch probabilities for subnormalized maps inflates variance;
    branch probabilities must be \(p_\pm/\kappa\);
  - stochastic agreement cannot substitute for the exact Liouvillian check.

## `T002` — programming-overhead SDP

- Equations: `EQC001`, `EQC002`, `EQC007`–`EQC011`.
- Methods: `METHOD001`, `METHOD003`.
- Physical parameters:
  - \(d=2\);
  - \(L_0=\sqrt{0.1}|0\rangle\langle1|\);
  - \(H=0\) and \(H=Z\);
  - one normalized Choi-state program copy;
  - \(T=10\);
  - \(\epsilon=0,0.005,\ldots,0.2\).
- Source-exact finite grid: 1000 times
  \(0,0.01,\ldots,9.99\).
- Sensitivity grids:
  - coarse measured run before scaling;
  - endpoint-augmented grid that includes \(t=10\);
  - optional intermediate grid for convergence.
- Variables per optimization:
  - two \(16\times16\) complex Hermitian matrices \(J_\pm\);
  - two real weights \(p_\pm\);
  - one \(4\times4\) complex Hermitian diamond-norm certificate per time.
- Solver policy:
  - first run one branch, one \(\epsilon\), and a small time grid;
  - profile canonicalization, solve time, peak memory, and residuals;
  - estimate the full 82-solve budget;
  - only then authorize the author-exact final run;
  - use a deterministic source-grid active set and warm-start neighboring
    \(\epsilon\) values;
  - certify every omitted one of the 1000 source times with the feasible
    diamond-SDP certificate \(Z=|J(\Delta_t)|\);
  - add and resolve any point whose certified upper bound exceeds the allowed
    error.
- Output schema:
  - CSV columns for branch, \(\epsilon\), \(\kappa_\epsilon\),
    \(\gamma_\epsilon\), \(p_\pm\), solver status, residuals, iterations, and
    time-grid metadata;
  - JSON summary for grid convergence, endpoint sensitivity, and total
    runtime.
- Validation:
  - analytic amplitude-damping and damping-plus-\(Z\) Choi checks;
  - diamond norm of identity \(=1\);
  - diamond distance between identity and Pauli \(X\) channels \(=2\);
  - \(p_+-p_-=1\);
  - every reconstructed half-diamond error no larger than
    \(\epsilon+\) disclosed feasibility tolerance;
  - \(\kappa_\epsilon\ge1\) and nonincreasing with \(\epsilon\), up to solver
    tolerance;
  - source-curve landmark and shape comparison after generation.
- Numerical risks:
  - 1000 small semidefinite constraints can make canonicalization, not matrix
    algebra, the bottleneck;
  - \(\epsilon=0\) can be numerically ill-conditioned;
  - source solver and tolerances are not disclosed;
  - the released script omits the nominal endpoint;
  - SCS returns approximate certificates, so residuals must accompany values.

## Efficiency and reuse plan

- Baseline: explicit CVXPY formulation closest to the paper equations.
- Main bottleneck: repeated construction/canonicalization of 1000
  diamond-norm LMIs over 41 error values and two model branches.
- First optimization: parameterize \(\epsilon\) in one compiled problem per
  branch and warm-start the same variables.
- Second optimization: constraint generation. A subset optimum is a lower
  bound; if its retrieval map is certified feasible at all 1000 disclosed
  times, it is also a matching upper bound and therefore the full-grid
  optimum within solver tolerance.
- Complexity guard: the full computation is not started until the measured
  small run yields a credible time and memory estimate.
- Reuse candidate: Choi reshuffling, partial traces, program contraction, and
  the HP diamond-norm LMI are general quantum-channel utilities. They can be
  proposed for the harness only after this case and a second independent case
  validate the conventions.
- Case-specific code that must remain local: SWAP projectors, Bell dephasing,
  the particular observable, the Fig. 3 Hamiltonians, source grids, and plot
  styling.
- Performance evidence: recorded in
  `outputs/checks/performance_profile.json` after the measured exploratory run.
