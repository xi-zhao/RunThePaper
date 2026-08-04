# Numerical Methods

## Method Cards

### NUM001 — Static jump sum rule

- Target: V001.
- Equations/method cards: EQC001–EQC005, METHOD001.
- Parameters: \(M=-0.5\) and \(-3\); \(q\) from several fractions of a
  reciprocal lattice unit.
- Grid or benchmark: smoke \(N=41\), feature \(N=101\), optional convergence
  \(N=151\).
- Boundary conditions: periodic in both momentum directions.
- Solver: vectorized finite differences and periodic bilinear interpolation.
- Tolerance: \(|C-\operatorname{round}C|<10^{-8}\);
  \(K/(2\pi|C|)\ge1-0.02\); extrapolated finite-\(q\) relative error below 2%.
- Random seed: none.
- Output schema: tidy CSV rows keyed by model, grid size, and \(q\), plus JSON
  acceptance checks.
- Validation checks: analytic projector identity, constant-map negative
  control, grid convergence, and \(q^2\) convergence.
- Numerical risks: interpolation error dominates for \(q\) near/below one grid
  spacing; derivative discretization biases \(K\) downward at coarse \(N\).

### NUM002 — Small-\(q\) LLG flow

- Target: T001 and dynamic part of V001.
- Equations/method cards: EQC004–EQC007, METHOD002.
- Parameters:
  \(M=-0.5,\gamma=1.5,\lambda_D=1.25,\lambda_T=0.025\).
- Grid or benchmark: smoke \(N=41\), feature initially \(N=81\); time interval
  chosen after measured smoke stability.
- Boundary conditions: periodic.
- Solver: explicit RK4 with pointwise renormalization.
- Tolerance: maximum norm defect below \(10^{-12}\) after projection; no
  topological-sector change; positive energy increments limited to the
  measured time-discretization tolerance.
- Random seed: none.
- Output schema: one CSV row per diagnostic time.
- Validation checks: step-halving, energy monotonicity, Chern conservation, and
  correlation between \(K_{\rm jump}\) and \(K\).
- Numerical risks: exchange Laplacian stiffness, topology loss at inadequate
  resolution, and source ambiguity in the absolute Fig. 1 normalization.

### NUM003 — Exact extended-Hubbard flow and robustness scans

- Targets: T002–T004.
- Equations/method cards: EQC005, EQC015–EQC017, METHOD004.
- Main parameters:
  \(M=-0.5,\gamma=1.5,U=8,V=0.75,\lambda_T=0.025\).
- Main grid: \(N=141\), shifted by half a cell; comparison grids
  \(N=101,181\).
- Solver: projected explicit RK4 with \(\Delta t=0.01\).
- Exact convolution: five Fourier moments, algebraically identical to dense
  quadrature for the extended-Hubbard kernel.
- Geometry: periodic spectral derivatives for metric, curvature, Dirichlet
  energy, and same-mesh numerical Chern; solid-angle and centered-difference
  results are independent diagnostics.
- Acceptance checkpoints:
  \(E_D(4.32)\) within 15% of \(\pi\),
  \(C_{\rm num}(4.32)>0.75\), exact trace-deviation mean below its initial and
  small-\(q\) values, exact flow trivial by \(t=8\), and correct ordered
  response under the full \(U,V\) sweeps.
- Numerical risk: a node-centered grid samples the bubbling point
  \((\pi,\pi)\) exactly and produces an artificial symmetry-pinned spin.

## Efficiency And Reuse Plan

- Baseline implementation: NumPy arrays with shape \((N,N,3)\).
- Main bottleneck: four RK4 right-hand-side evaluations per time step.
- Efficient implementation choice: vectorized `numpy.roll` finite differences;
  FFT derivatives, and a five-moment exact interaction; no new dependencies.
- Complexity or scaling: \(O(N^2)\) memory and work per right-hand-side call.
- Performance bottleneck removed: Python loops over momentum points.
- Optional harness promotion candidate: solid-angle Chern and periodic
  unit-texture helpers after this case is validated.
- Case-specific parts that should not enter the harness: QWZ Hamiltonian,
  LLG couplings, and detector normalization.
- Performance evidence: T002 completes in 19.3 s and the 19-curve T004 sweep
  in 42.9 s on the profiled Apple M4.
