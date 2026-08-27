# Numerical Methods

## NUM001 — One-photon sector

- Targets: T001-T002
- Equations: EQC001-EQC006
- Parameters: Q1-Q11; first ten Table S1 bonds; launches Q6, Q1, Q11.
- Grid: 0-250 ns at 0.5 ns.
- Boundary conditions: finite open chain.
- Solver: dense Hermitian eigendecomposition and eigenphase propagation.
- Output: site density, one-site entropy, connected z correlation,
  concurrence, rms displacement.
- Validation: norm and density sum at 1e-10; exact initial state; observable
  bounds; Eq. S29 spectral velocity within 0.00223% of 153.99 sites/us.

## NUM002 — Two-photon calibrated and control sectors

- Targets: T003-T004
- Equations: EQC001-EQC003, EQC007-EQC008
- Parameters: Q1-Q12; all Table S1 J/U values; launches Q1+Q12 and Q6+Q7.
- Grid: 0-250 ns at 0.5 ns; paper snapshots at 10.5-55.5 ns.
- Sectors: two bosons (78 states), free bosons with U=0 (78), hard core (66).
- Output: density, Gij, double-occupancy probability.
- Validation: norm, total density 2, sum_ij Gij=2, below-3% double occupancy,
  and calibrated pattern closer to hard core than free bosons.

## Efficiency And Reuse Plan

- Baseline: exact dense linear algebra; no stochastic sampling.
- Main cost: eigendecomposition, O(D^3), with D<=78.
- Reuse: one diagonalization serves every time point for a Hamiltonian.
- Backend: NumPy reference and optional CuPy parity using the same domain API.
- Promotion boundary: the fixed-sector basis/observable pattern is reusable;
  paper parameters and acceptance rules remain case-local.
