# Numerical Methods

## NUM-WIGNER-DIRECT

- Targets: `T-FIG003`, `T-FIG004`, `T-FIG005A`, `T-FIG005B`.
- Equation cards: all seven `EQC-*` cards.
- Method card: `MTH-SCANS`.
- Parameters: the target-specific paper values recorded in
  `physics_reproduction_project.json`.
- Grid: inclusive \(0^\circ\)-\(360^\circ\) grid at \(0.5^\circ\).
- Boundary conditions: angular projectors are periodic modulo \(180^\circ\).
- Solver: direct complex linear algebra on a \(4\times4\) density matrix;
  there is no optimization, fit, interpolation, or stochastic solver.
- Tolerance: \(10^{-12}\) for algebraic identities and physical range checks.
- Random seed: not applicable.
- Output schema: CSV columns
  `angle_deg,p_ab,p_bc,p_ac,wigner,w_limit`.
- Validation checks: trace, Hermiticity, positive semidefiniteness,
  probability bounds, Wigner identity, periodicity, exact analytic extrema,
  fidelity, and all-five-series presence.
- Numerical risks: degree/radian confusion, party/order reversal in the
  asymmetric scans, treating Figure 4's central angle as its start angle, or
  using a \(2\times2\) identity instead of \(I_4\).

## Independence Boundary

The target runner reads only the target specification and paper-derived
parameters. It does not read the PDF, source-figure pixels, experimental ZIP,
measured probabilities, or digitized coordinates. Reference assets enter only
after the generated CSV and figure exist.

## Efficiency And Reuse Plan

- Baseline implementation: vectorized direct Born evaluation.
- Complexity: \(O(N)\) grid points with constant \(4\times4\) work.
- Main bottleneck: plotting and PNG encoding, not physics.
- Performance choice: local CPU; no GPU or remote service.
- Reuse boundary: all physics and scan conventions remain case-local because
  they encode this paper's measurement ordering and figure targets.
