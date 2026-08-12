# Method Trace

## NUM001 — Gaussian QSD trajectories

- Source: Main Eqs. (1)-(2), statement that the evolution is number-conserving
  and Gaussian.
- Input: `(L,p,gamma,dt,t_burn,t_sample,seed)` and the half-filled Neel state.
- Output: trajectory-local projectors and nonlinear entropy/correlation samples.
- Algorithm: exact circulant unitary half-step, derived diagonal stochastic
  measurement update, QR, second unitary half-step.
- Checks: projector idempotency, Hermiticity, fixed trace, gamma-zero unitary
  limit, zero-hopping pointer-state limit, step-halving comparison.
- Status: specified; implementation follows in `src/dark_state_fermions`.

## NUM002 — Finite-size scaling analysis

- Source: Supplement Eqs. (7)-(9).
- Input: ensemble means and standard errors for all configured sizes.
- Output: central charge, `a`, `b`, fit residuals, and local-slope diagnostics.
- Algorithm: bounded nonlinear least squares plus independent log-log slopes.
- Checks: synthetic curves with known parameters; fit-window sensitivity.
- Status: specified.

## NUM003 — Dark-state kernel quadrature

- Source: Supplement Eqs. (10)-(19).
- Input: `(p,q)` grids independent of trajectory data.
- Output: infrared kernel slopes and analytic `a,b` theory lines.
- Algorithm: adaptive quadrature with a split oscillatory tail and log-log fits.
- Checks: two q ranges, direct exponent identity, threshold bracketing.
- Status: specified.

## NUM004 — Sharded paper-scale campaign

- Source: all numerical captions and the same equations as NUM001-NUM003.
- Input: immutable job table spanning all paper sizes/parameters and convergence
  variants.
- Output: atomic per-trajectory checkpoints, streaming sufficient statistics,
  aggregate datasets, hashes, and target acceptance.
- Algorithm: nonoverlapping deterministic seeds; shard-local execution and
  fail-closed aggregation.
- Checks: resume without recomputation, no seed overlap, config/source hashes,
  time-step and size convergence.
- Status: required even if the production campaign is not run.
