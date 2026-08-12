# Numerical methods

## NUM001 -- analytic free decay

- Target: T001.
- Grid: 0--60 s with 5 ms spacing.
- Solver: stable closed Eq. (4), not a curve fit.
- Checks: zero initial response, late decay, analytic envelope.

## NUM002 -- driven resonator

- Targets: T002--T003.
- Grid: the same declared uniform time grid.
- Solvers: exact exponential step with linear input and independent RK4.
- Tolerance: relative RMS disagreement below 0.02.
- Risk: Gaussian/chirp shapes are explicit reconstruction choices because the
  paper does not print their complete parameters.

## NUM003 -- matched filter

- Targets: T004--T005.
- Input: deterministic seeded synthetic noise and a formula-generated template.
- Solvers: FFT correlation and direct least squares.
- Checks: arrival error at most 0.1 s, amplitude error below 5%, FFT/direct
  difference below `1e-10`, Monte Carlo/analytic sigma difference below 15%.
- Risk: this validates the method, not the unpublished experimental trace.

## NUM004 -- statistics and axion kernel

- Targets: T006--T007.
- Solvers: analytic Gaussian/quadrature propagation; direct point-source kernel.
- Checks: exact printed uncertainty aggregate, exact printed constraint anchor,
  and massless-kernel limit.
- Risk: finite-volume geometry is blocked by inaccessible supplemental inputs.

## Paper-scale execution

The paper-scale path validates hash-bound inputs, checkpoints per dataset,
supports resume, and shards the finite-volume mass scan. It fails closed when
the Supplemental Material, calibration arrays, segment bundles, or cell
geometry are missing. It never accepts source pixels as a scientific input.
