# Numerical Methods

## Method Cards

### NUM001 — density-matrix Born evaluation

- Targets: `T-FIG003`, `T-FIG004`, `T-FIG005A`, `T-FIG005B`
- Equation cards: `EQC001` through `EQC006`
- Parameters: the target-specific \(w,v,\xi\) and angle geometry reported in
  Section V of the paper
- Grid: \(0^\circ\) to \(360^\circ\), inclusive, at \(0.25^\circ\)
  increments
- Boundary conditions: not applicable; polarization angles are checked for
  \(180^\circ\) periodicity
- Solver: direct real-valued NumPy matrix products and traces of \(4\times4\)
  matrices
- Tolerance: \(10^{-12}\) for matrix/scalar agreement, normalization, and
  periodicity
- Random seed: not applicable; the calculation is deterministic
- Output schema: CSV columns
  `angle_deg,p_abprime,p_bcprime,p_acprime,wigner,violation_limit`
- Validation checks: density-matrix trace/Hermiticity/positivity, projector
  normalization, probability bounds, independent scalar Born identity,
  Wigner identity, period, and analytic extrema
- Numerical risks: degree/radian conversion, tensor-product ordering, swapped
  fixed/rotating observer, and an incorrect sign for the \(\xi=\pi\) phase

## Efficiency And Reuse Plan

- Baseline implementation: explicit matrix Born trace for each scan point
- Main bottleneck: none at this scale; fewer than six thousand \(4\times4\)
  traces cover all four targets
- Efficient implementation choice: keep the small explicit matrices because
  they make the physical basis and independent checks auditable
- Complexity or scaling: \(O(N)\) in angle samples with constant \(4\times4\)
  work
- Performance bottleneck removed: not applicable
- Optional harness promotion candidate: none; this model is paper-specific
- Case-specific parts that should not enter the harness: state parameters,
  angle mapping, target labels, line styles, and analytic limits
- Performance evidence: recorded per target in
  `outputs/checks/<target>_scientific.json` and aggregated in
  `outputs/checks/local_compute_time.json`
