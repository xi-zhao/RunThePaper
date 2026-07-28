# Numerical Methods

## NUM001 — Main Fig. 1 numerical Wigner surfaces

- Target: `T001`, the numerical content behind the overview.
- Equations/method cards: `EQC001`--`EQC005`, `EQC012`--`EQC014`;
  `METHOD001`, `METHOD002`.
- Parameters: exactly the six collective-Fock amplitudes printed in the End
  Matter; third relative mode vacuum; Gaussian kernel
  \(8e^{-6|\alpha|^2}/\pi\).
- Grid:
  - full-cut rendering: \(\Re\alpha_+,\Im\alpha_+\in[-2,2]\),
    \(\Re\alpha_-\in[-2,2]\), reconstructed isosurface sampling;
  - two-dimensional fields: \(401\times401\);
  - negative-volume quadrature: radial cutoff 4, 800 radial nodes, 3072
    angular nodes, with lower-resolution convergence records.
- Boundary conditions: Gaussian tails; the cutoff error is checked by expanding
  the radial interval.
- Solver: finite Fock sum, deterministic quadrature, FFT convolution for field
  visualization, analytic convolution at the origin.
- Tolerance: \(10^{-12}\) algebraic identities, \(5\times10^{-6}\) negative
  volume, \(10^{-10}\) smoothing-origin check.
- Random seed: none.
- Output schema: CSV grids/metrics, JSON checks, PNG figure and comparison.
- Validation checks: state norm, reduced-state trace, reality, signed slice
  integral, corrected/printed threshold separation, and
  \(-7/(16\pi)\) at the smoothed origin.
- Numerical risks: the theorem-1 certification margin is only about
  \(2.6\times10^{-4}\); the source's printed threshold is inconsistent; Fig. 1
  rendering levels are undisclosed.

## NUM002 — Main Fig. 2 W-state panels

- Target: `T002`, panels (a) and (b).
- Equations/method cards: `EQC006`--`EQC011`; `METHOD002`, `METHOD003`.
- Parameters: \(M=3\), \(r=0.7\), \(\xi_0=(85+147i)/200\), seven-point
  \(\Xi\), and a vacuum auxiliary state.
- Grid: \(401\times401\) for each heat map; analytic finite-disk integral;
  exact 7-by-7 matrix.
- Boundary conditions: displayed domains match the source:
  \(\alpha\in[-1,1]^2\) and \(\xi\in[-2,2]^2\).
- Solver: closed-form field evaluation, scalar root finding, Hermitian
  eigensolve.
- Tolerance: \(10^{-12}\) analytic identities, \(10^{-10}\) witness value.
- Random seed: none.
- Output schema: two-panel PNG, CSV field slices and witness points, JSON
  metrics/checks, side-by-side comparison.
- Validation checks: Wigner zero radius, disk threshold crossing, 19 unique
  differences, Hermiticity, and \(\mathcal N_C=0.0175804\).
- Numerical risks: the certification margin at \(r=0.7\) is small but is
  evaluated analytically, so plot resolution does not affect it.

## NUM003 — Independent invariant checks

- Target: `V001`--`V003`.
- Equations/method cards: all equation cards.
- Parameters: paper-exact.
- Solver: direct algebraic evaluation plus deterministic numerical checks.
- Output schema: one machine-readable validation JSON per target and a compact
  CSV of convergence values.
- Validation checks:
  - `V001`: W-state disk formula and threshold;
  - `V002`: characteristic-matrix spectrum and point count;
  - `V003`: Fig. 1 state norm, relative parity, signed integral, both reported
    thresholds, negative volume, and exact smoothing origin.
- Numerical risks: `V003` intentionally reports the source discrepancy as a
  finding rather than coercing it into a pass.

## Efficiency And Reuse Plan

- Baseline implementation: direct finite sums and scalar loops.
- Main bottleneck: repeated evaluation of the six-state Wigner field and the
  polar negative-volume integral.
- Efficient implementation choice: vectorized NumPy arrays, cached
  one-dimensional associated-Laguerre factors, broadcasting, and analytic
  formulas for validation points.
- Complexity or scaling: \(O(N_rN_\theta)\) for the slice integral and
  \(O(N^3)\) for the tiny \(N=7\) eigensolve.
- Performance bottleneck removed: no dense three-mode Hilbert matrix or
  repeated matrix exponentials are formed.
- Optional harness promotion candidate: a generic sparse Fock-state Wigner
  evaluator and convergence ledger could serve future continuous-variable
  cases.
- Case-specific parts that should not enter the harness: the six amplitudes,
  W-state point set, and correction to the paper's printed numerator.
- Performance evidence: written after the guarded target runs.
