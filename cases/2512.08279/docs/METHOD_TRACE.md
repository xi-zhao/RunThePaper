# Method Trace

The paper's numerical evidence has two different computational objects:

1. a Monte Carlo estimator for one expectation-value trajectory (Fig. 2);
2. a convex optimization for a worst-case channel error (Fig. 3).

They share the Liouvillian/Choi convention but must not be conflated. The
method cards below keep their inputs, outputs, and verification signals
separate.

## METHOD001 — Independent Liouvillian and Choi construction

- Source:
  - Supplemental Sec. A, `appendix:lindblad_to_choi`;
  - Fig. 3 model definitions and public parameter scripts.
- Role: generate channels and normalized Choi program states without calling
  the authors' MATLAB functions or loading their arrays.
- Inputs:
  - system dimension \(d\);
  - Hermitian Hamiltonian \(H\);
  - jump operators \(L_k\);
  - time values \(t\).
- Outputs:
  - Liouvillian matrix \(\mathbf L\);
  - channel superoperator \(e^{t\mathbf L}\);
  - unnormalized Choi matrix \(J(e^{t\mathcal L})\);
  - normalized program state \(J(e^{t\mathcal L})/d\).
- Algorithm:
  1. build the GKSL matrix from `EQC001`;
  2. exponentiate it with a dense matrix exponential;
  3. reshuffle the four channel indices according to `EQC002`;
  4. symmetrize only floating-point anti-Hermitian residue, while recording its
     norm before doing so;
  5. verify positivity and both trace constraints.
- Parameters: at most \(d=4\) for Fig. 2 and \(d=2\) for Fig. 3; all matrices
  are dense and small.
- Code pointer: `src/programmable_lindbladian.py`.
- Independent checks:
  - identity Choi has trace \(d\) and output partial trace \(I\);
  - the amplitude-damping matrix exponential agrees with its analytic Kraus
    channel;
  - the SWAP-dephasing Liouvillian agrees with the exact factorization;
  - every normalized Choi program is positive and trace one.
- Method gate: `verified`.
- Open questions: the supplemental Liouville formula places the two loss-term
  transposes inconsistently with its own vectorization identity. The
  implementation follows the independently derived identity in
  `DERIVATION_TRACE.md`; the disclosed numerical models use real diagonal
  \(L^\dagger L\), so this source typo does not change either target.

## METHOD002 — Nested quasi-sampling for Fig. 2

- Source:
  - Proposition 3 and Supplemental Eq. `eq:programmable_swap`;
  - main Fig. 2 caption;
  - quasi-sampling discussion in Supplemental Sec. A.
- Role: reproduce the visible red estimates from physically sampled branches,
  not by adding arbitrary noise to the analytic curve.
- Inputs:
  - fixed HPTP SWAP processor from `EQC005`;
  - its independently optimized signed CPTP decomposition;
  - \(\lambda=0.5\);
  - initial state \(|01\rangle\);
  - observable \(|01\rangle\langle01|\);
  - 101 time values in \([0,10]\);
  - 1000 outer samples and 200 inner quasi samples per time;
  - a recorded deterministic pseudorandom seed.
- Outputs:
  - analytic overlap at each time;
  - direct-Liouvillian overlap;
  - quasi-sampled estimate, standard error, and confidence interval;
  - recovered \(p_+,p_-\), overhead \(\kappa\), and solver diagnostics.
- Algorithm:
  1. construct the fixed HPTP processor from matrix units;
  2. solve its small Choi decomposition into \(p_+\mathcal E_+-p_-\mathcal
     E_-\);
  3. sample the outer physical mixture between coherent and dephasing
     branches;
  4. for each coherent event, sample the two physical inner channels with
     probability \(p_\pm/\kappa\);
  5. multiply inner outcomes by \(\kappa s_\pm\);
  6. aggregate means and standard errors without using source curve values.
- Parameters:
  - paper: \(\lambda=0.5,T=10,101\) plotted times, 1000 cycles, 200 inner
    samples;
  - generated control: seed `251208279`, which changes only stochastic
    repeatability, not the physical model.
- Code pointer:
  - `src/programmable_lindbladian.py`;
  - `scripts/run_swap_dephasing.py`.
- Independent checks:
  - HPTP Choi Hermiticity and trace preservation;
  - \(p_+-p_-=1\);
  - recovered optimum \(p_++p_-=2\), as predicted in the supplement but not
    imported from the authors' matrices;
  - exact and direct-Liouvillian curves agree to floating-point tolerance;
  - normalized residuals of the sampled curve are statistically compatible
    with the recorded standard errors.
- Method gate: `verified`.
- Open questions: the source notebook does not set a random seed. The fixed
  seed is explicitly a reproducibility control, not a paper parameter.

## METHOD003 — Hermiticity-preserving diamond-norm SDP for Fig. 3

- Source:
  - main programming-cost definition `eq:primal_program_pga`;
  - Supplemental SDP `eq:sdp_virtual_cost`;
  - public `error_threshold_ad.m` and `error_threshold_ad_phase.m`;
  - Watrous diamond-norm SDPs and QETLAB's disclosed implementation.
- Role: independently reproduce the two 41-point sampling-overhead curves
  without MATLAB, CVX, QETLAB, or author result arrays.
- Inputs:
  - Choi programs from `METHOD001`;
  - one fixed retrieval Choi variable \(J^\mathcal P\);
  - error threshold \(\epsilon\);
  - sampled time grid;
  - model branch \(H=0\) or \(H=Z\).
- Outputs:
  - optimum \(\kappa_\epsilon=p_++p_-\);
  - \(\gamma_\epsilon=\log_2\kappa_\epsilon\);
  - primal status, residuals, iteration count, and wall time;
  - endpoint-inclusion and time-grid convergence checks.
- Algorithm:
  1. generate all \(J(e^{t_k\mathcal L})\) and
     \(\pi_k=J(e^{t_k\mathcal L})/2\);
  2. create \(16\times16\) Hermitian \(J_+,J_-\) and scalars \(p_+,p_-\);
  3. constrain both CP maps to be proportional to trace-preserving maps;
  4. contract the program state with \(J_+-J_-\);
  5. impose the Hermiticity-preserving diamond-norm LMI from `EQC010` on a
     deterministic active subset of the disclosed source grid;
  6. minimize \(p_++p_-\);
  7. certify every omitted source-grid time using the explicit feasible
     Watrous primal point \(Z=|J(\Delta_t)|\);
  8. if any omitted point is not certified, add it to the active set and
     resolve;
  9. warm-start successive \(\epsilon\) values without changing the physical
     model.
- Parameters:
  - \(d=2,\Gamma=0.1,H=0\) or \(Z\), \(n=1,T=10\);
  - 1000 source-script times \(0,0.01,\ldots,9.99\);
  - 41 errors \(0,0.005,\ldots,0.2\);
  - final solver tolerances are recorded in the run artifact rather than
    treated as physical parameters.
- Code pointer:
  - `src/programmable_lindbladian.py`;
  - `scripts/run_programming_cost.py`.
- Independent checks:
  - diamond norm of identity equals one;
  - diamond norm of the difference between identity and a Pauli-\(X\) channel
    equals two;
  - each recovered \(J_\pm\) is positive within solver tolerance;
  - \(p_+-p_-=1\);
  - every sampled half-diamond error is below \(\epsilon\) within the reported
    solver residual;
  - all 1000 disclosed source-grid times are either active constraints or
    carry the rigorous upper bound
    \(\tfrac12\|\operatorname{tr}_{S'}|J(\Delta_t)|\|_\infty
    \le\epsilon\);
  - coarse, medium, and author-exact time grids preserve the curve topology;
  - adding \(t=10\) is reported separately.
- Method gate: `verified`.
- Open questions: the paper does not report its CVX/QETLAB solver or
  tolerances. The reproduction must disclose its own solver uncertainty and
  cannot interpret sub-tolerance source differences as physics.

Why the active-set result is still the full-grid optimum: constraining a
subset gives a lower bound on the 1000-point problem. If the resulting
retrieval map is then independently certified feasible at every omitted
point, the same objective is also an upper bound for the full problem. The
bounds coincide (within solver tolerance), so no paper constraint has been
discarded.

## METHOD004 — Structured evidence and source-separated rendering

- Source:
  - main Fig. 2 and Fig. 3 captions;
  - source assets `non_unitary_evolution.pdf` and
    `damping_with_Z_rotation_41points.pdf`.
- Role: preserve numerical provenance while creating paper-faithful figures
  and comparisons.
- Inputs:
  - generated CSV/JSON data from `METHOD002` and `METHOD003`;
  - separately rendered source panels used only as references.
- Outputs:
  - independent scientific figures;
  - source-versus-generated comparisons;
  - numerical feature metrics;
  - pixel-layout evidence with axis and visible-series contracts.
- Algorithm:
  1. write data before drawing;
  2. render every physical branch from the generated dataset;
  3. preserve source axis ranges, ticks, colors, line/marker meanings, and
     aspect ratios;
  4. keep source pixels in the reference lane and generated pixels in the
     evidence lane;
  5. compare curve features numerically before any pixel score;
  6. record pixel residuals as presentation fidelity, never as proof of the
     equations.
- Parameters: figure size, DPI, fonts, and marker size are rendering
  parameters and are recorded separately from physical parameters.
- Code pointer:
  - `scripts/render_reproduction.py`;
  - `scripts/compare_reproduction.py`.
- Independent checks:
  - every rendered figure references an independent generated dataset;
  - no source raster or author data array enters the numerical code path;
  - line branches and marker-only sampled data remain visibly distinct;
  - source and generated panels have registered axis boxes before pixel
    metrics are interpreted.
- Method gate: `verified`.
- Open questions: exact source font metadata is not required for the
  scientific verdict; any remaining typography mismatch will be reported as a
  pixel-lane limitation.
