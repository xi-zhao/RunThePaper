# Numerical Methods

## NUM001 — analytic/cumulant branches

- Targets: T001, T002, T004, T005
- Equations: DPT003-DPT006
- Method: closed-form one-photon branches; continuation of cumulant fixed
  points; Jacobian eigenvalues at every branch point.
- Checks: threshold identity, conjugation constraints, spin-length residual,
  ODE residual, and sign of largest real stability eigenvalue.

## NUM002 — finite-size Lindblad exact diagonalization

- Targets: T001, T002, T003, T008
- Equations: DPT001-DPT002, DPT009
- Basis: photon Fock basis times the permutation-symmetric spin `j=N/2`
  representation, consistent with `[Jx,Jy]=2iJz`.
- Solver: QuTiP 5 sparse Liouvillian/steady-state tools; QuTiP is the same
  independent library named in the paper, not author code.
- Checks: trace one, Hermiticity, positivity tolerance, residual
  `||L rho||`, cutoff-edge occupation, and photon parity.

## NUM003 — quantum trajectories and Wigner transform

- Targets: T002, T003, T007
- Initial state: one independently and reproducibly seeded random normalized
  vector for every trajectory, matching the finite-temperature sampling rule
  printed in the supplement. Initial-state and jump-process seeds are disjoint.
- Solver: Monte-Carlo trajectories with stable integer indices, 60-way
  job-local sharding, atomic checkpoints, and exact-once merge validation.
- Wigner: computed only from the generated reduced photon density matrix.
- Checks: complete/nonoverlapping trajectory indices, trace/positivity,
  500-to-3000 sample-count convergence, cutoff tail, Wigner normalization, and
  `Z4` rotation residual.

## Isolation and efficiency

The runner receives only `src/`, `scripts/`, and JSON configuration in an
isolated directory. `raw/` and original figures are inaccessible. Exact
finite-size cost scales with the squared Hilbert dimension in Liouville space;
large-N panels therefore begin with a measured trajectory pilot before any
paper-scale request.
