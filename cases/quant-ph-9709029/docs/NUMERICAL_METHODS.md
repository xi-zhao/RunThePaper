# Numerical Methods

The implementation uses dense linear algebra on matrices no larger than 4x4. The concurrence spectrum comes from singular values of the proof's complex-symmetric `tau` matrix, avoiding unstable nested square roots at exact rank deficiency. The Takagi factorization is solved as a real-symmetric augmented eigenproblem for the anti-linear equation `A conj(u)=s u`; this remains unitary in exactly degenerate subspaces and uses an SVD null basis only for exact zero modes. Real two-state rotations solve the positive branch; a deterministic four-vector polygon closes the zero branch, with its collinear boundary handled analytically instead of evaluating ill-conditioned inverse cosines. Forward and inverse HJW maps verify every ensemble. No author implementation or numerical data are used.

## Method Cards

### NUM001 — spectral identities

- Target: T001–T003
- Equations: EQ002–EQ004
- Solver: Hermitian eigendecomposition and complex-symmetric singular values
- Validation: magic-basis action, pure entropy identity, rho-tilde spectrum, Bell/product/Werner endpoints, local-unitary invariance

### NUM002 — constructive convex roof

- Target: T004–T006
- Equations: EQ001, EQ005, EQ006
- Solver: Takagi factorization, real pair rotations, deterministic phase polygon, HJW forward/inverse maps
- Validation: tilde orthogonality, density reconstruction, equal preconcurrence, optimal average concurrence and entropy, zero-branch phase closure, the named `(0.55, 0.25, 0.10, 0.10)` Bell-diagonal counterexample, and all 455 denominator-12 Bell-simplex states
- Numerical risks: degenerate Takagi subspaces, exact zero modes, and collinear separability boundaries; all have explicit regression tests

### NUM003 — independent falsification families

- Benchmark: random Wishart states of ranks 1–4, arbitrary HJW isometries, Werner states, and independently generated product mixtures
- Random seed: 9709029
- Outputs: `random_mixed_states.csv`, `optimal_decompositions.csv`, `bell_diagonal_adversarial.csv`, `ill_conditioned_physical_states.csv`, and `werner_family.csv`

### NUM004 — whole-paper operational and historical checks

- Targets: T007–T010
- Exact calculation: binomial Schmidt-type probabilities and log-dimensions via `gammaln`/`logsumexp`
- Finite-dimensional check: Caratheodory bound `d^2=16` for two qubits
- Historical-scope checks: dedicated rank-one/rank-two formula campaign and per-component optimal-entanglement spread
- Outputs: `pure_state_protocol_rates.csv` and `historical_claim_checks.csv`
- Boundary: private/unpublished proofs are not reconstructed from missing source material; only their locally executable consequences are tested

The Takagi implementation uses a complex SVD followed by symmetric-unitary
phase refinement inside degenerate singular subspaces. A 15,000-state physical
conditioning campaign covers near-rank-3, near-full-rank, and explicit
near-rank-deficient separable product mixtures; every density matrix is frozen
with a SHA-256 fingerprint.

## Efficiency And Reuse Plan

- Baseline implementation: direct fixed-size formulas
- Main bottleneck: none; the scientific problem is 4x4
- Efficient implementation: follow the constructive proof instead of generically optimizing over ensembles
- Complexity: constant-size linear algebra; campaign cost is linear in sample count
- Case-specific parts that should not enter the Harness: Wootters spin flip and phase construction
- Performance evidence: `outputs/checks/run_summary.json` and the isolated-run attestation
