# Method Trace

Use this file for algorithmic or systems papers where the key reproduction
object is a method rather than a formula.

## Method Cards

### METHOD001 — Static geometry and finite-\(q\) convergence

- Source: paper's massive Dirac model plus EQC001–EQC005.
- Role: primary go/no-go test for the proposed geometric jump sum rule.
- Inputs: mass \(M\), grid size \(N\), and physical probe momenta \(q\).
- Outputs: Chern number, \(K\), \(E_D\), \(K_{\rm jump}(q)\), relative errors,
  and curvature-sign diagnostics.
- Algorithm steps:
  1. sample the lower-band QWZ unit texture on a periodic grid;
  2. compute derivatives, quantum metric, Berry curvature, and solid-angle
     Chern number;
  3. periodically interpolate the texture at four momentum displacements;
  4. integrate the mismatch and fit the leading \(q^2\) error.
- Parameters: topological \(M=-0.5\); trivial negative control \(M=-3\);
  multiple \(N\) and \(q\) values.
- Code pointer: `src/chern_jump_geometry.py` and
  `scripts/run_validation.py`.
- Checks: topological integer, Chern bound, zero constant-texture response,
  finite-\(q\) convergence, and trivial control.
- Status: equations verified; numerical protocol reconstructed because the
  paper does not disclose its mesh, grid origin, time step, or integrator.
- Open questions: detector-specific mapping remains outside this method.

### METHOD002 — Feature-level LLG integration

- Source: paper Eq. `LLG equation`.
- Role: test whether the same finite-\(q\) estimator tracks the geometric
  relaxation used by the paper.
- Inputs: QWZ initial texture and paper couplings.
- Outputs: time series of energy, \(K\), \(K_{\rm jump}\), Chern number, and
  maximum norm error.
- Algorithm steps: periodic Laplacian, RK4, unit-vector projection, regular
  diagnostic snapshots.
- Parameters:
  \((M,\gamma,\lambda_D,\lambda_T)=(-0.5,1.5,1.25,0.025)\).
- Code pointer: `src/chern_jump_geometry.py:integrate_llg`.
- Checks: norm preservation, energy monotonicity within tolerance, Chern-sector
  preservation, and estimator correlation.
- Status: specification ready.
- Open questions: exact match to Fig. 1 is limited by unspecified numerical
  details and a visible normalization ambiguity in the source asset.

### METHOD003 — Detector-fixed go/pivot/stop test

- Source: published Supplemental Material Eqs. (50), (74)–(85), and
  (103)–(104), plus EQC008–EQC014.
- Role: decide whether the paper bath or a separately calibrated density probe
  can support the click-record topology claim.
- Inputs: QWZ projector, paper identity-superoperator vertex basis, scalar
  finite-\(q\) density vertex, Ohmic kernel, temperature, coupling, and detector
  energy window.
- Outputs: small-\(q\) metric extrapolation, raw thermal rates, coupling
  scaling, spectral-window recovery, and topological/trivial vertex controls.
- Algorithm steps:
  1. construct gauge-free \(2\times2\) projectors from the QWZ texture;
  2. evaluate the paper bath's complete same-\(k\) Hilbert–Schmidt vertex sum;
  3. evaluate finite-\(q\) scalar density weights and interband gaps;
  4. apply the Ohmic/Bose detector kernel transition by transition;
  5. calibrate before spectral integration and sweep window, temperature, and
     coupling;
  6. compare Chern and constant-projector negative controls.
- Code pointer: `src/detector_sum_rule.py` and
  `scripts/run_detector_validation.py`.
- Checks: nine preregistered detector-level checks in
  `outputs/checks/detector_sum_rule_validation.json`.
- Status: verified; outcome is `pivot`.
- Open questions: estimator variance and spectator-probe backaction during the
  full time-dependent flow are not yet modeled.

### METHOD004 — Exact versus small-\(q\) extended-Hubbard evolution

- Source: official Supplemental Eqs. (117)–(134), main Figs. 2–3, and
  Supplemental Figs. 3–6.
- Role: independently reproduce the finite-\(q\) Hartree–Fock evolution that
  tests whether relaxation toward ideal geometry survives beyond the
  small-\(q\) approximation.
- Inputs:
  \((M,\gamma,U,V,\lambda_T,Q)=
  (-0.5,1.5,8,0.75,0.025,\pi/2)\), the lower-band initial texture, a periodic
  momentum mesh, and an explicit time step.
- Outputs: exact and approximate Dirichlet-energy trajectories, two Chern
  estimators, curvature-sign diagnostics, and the three
  \(\Delta_{\rm tr}(\mathbf k)\) maps at \(t=0\) and
  \(T_{\rm short}=4.32\).
- Algorithm:
  1. construct the paper's massive-Dirac lower-band texture;
  2. evaluate the exact interaction convolution through the five Fourier
     moments derived in EQC015;
  3. evaluate the comparison Laplacian field using \(\lambda_D\) from EQC016;
  4. advance both tangent flows with the same projected RK4 method;
  5. offset the periodic grid by half a cell so the bubbling point
     \((\pi,\pi)\) is approached rather than symmetry-pinned on a node;
  6. compute metric, curvature, Dirichlet energy, and numerical Chern number
     with one periodic spectral derivative scheme, while retaining centered
     differences and solid-angle topology as independent diagnostics;
  7. compare \(N=101,141,181\) to identify the mesh that simultaneously
     resolves the near-\(\pi\) plateau, the \(C\simeq1\) value at
     \(T_{\rm short}\), and the localized peak reported in the supplement.
- Checks: exact low-rank convolution against a dense small-grid sum, tangent
  right-hand side, unit norm, initial \(C=1\), nonnegative continuum
  trace-condition deviation up to derivative tolerance, and agreement of
  \(\lambda_D\) with the supplement.
- Code pointers:
  `src/chern_jump_geometry.py:integrate_extended_hubbard_comparison`
  and `scripts/run_paper_target.py`.
- Status: source equations verified and numerical protocol reconstructed. The
  reproduced \(N=141\), half-cell-shifted
  trajectory gives \(E_D(4.32)=3.1452\), \(C_{\rm num}(4.32)=0.9965\),
  and the subsequent finite-mesh transition. Because the paper does not
  disclose mesh, grid origin, step size, or integrator, artifacts remain
  exploratory rather than paper-exact.
