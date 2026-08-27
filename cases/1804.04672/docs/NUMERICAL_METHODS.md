# Numerical Methods

## Method Cards

### NUM001

- Target: `T001`, Fig. 3(b) cylinder complex spectrum.
- Equations/method cards: `EQC001`, `EQC002`, `MTH001`.
- Parameters: `t_x=t_y=v_x=v_y=1`, `gamma_x=gamma_y=0.2`,
  `gamma_z=0`, `m=1.717`, `L_y=40`.
- Grid or benchmark: `180` uniformly sampled `k_x` values in
  `[-pi, pi)`.
- Boundary conditions: periodic `x`, open `y`.
- Solver: dense `numpy.linalg.eig` on each `80 x 80` finite-strip matrix.
- Tolerance: Hermitian-limit residual must be below `1e-12`.
- Random seed: not applicable.
- Output schema: CSV with `target_id`, `series_id`, `kx`, `band_index`,
  `energy_real`, `energy_imag`, `edge_label`, and edge weights.
- Validation checks: row count, Hermitian-limit sanity, edge-weight bounds,
  analytic chiral edge-trace count, EPS reference point extraction, and EPS
  red-branch point matching.
- Numerical risks: right-eigenvector boundary localization can mix chiral edge
  states with non-Hermitian skin-effect localized bulk states; the rendered
  red branch therefore traces `E_+(kx)=sin(kx)+i gamma` and
  `E_-(kx)=-sin(kx)-i gamma` instead of using boundary weight alone.
- Source-reference check: the EPS red branch has `102` points. The generated
  red branch has `102` points; sorted branch-wise matching gives mean distance
  `0.0098` and max distance `0.0263`.

### NUM002

- Target: `T002`, Fig. 3(a) cylinder phase diagram.
- Equations/method cards: `EQC001`, `EQC003`, `EQC004`, `MTH002`.
- Parameters: `t_x=t_y=v_x=v_y=1`, `gamma_x=gamma_y=gamma`,
  `gamma_z=0`, `m` scanned over the phase-diagram range.
- Boundary conditions: periodic `x`, open `y`, represented by the non-Bloch
  cylinder Hamiltonian with `beta=r(k_x) exp(i tilde{k}_y)`.
- Solver: analytic band-touching condition of the `2 x 2` non-Bloch cylinder
  Hamiltonian at `k_x=0`, `tilde{k}_y=0`.
- Phase criterion: the red boundaries are
  `m=1+sqrt(1-2 gamma+2 gamma^2)` and
  `m=1+sqrt(1+2 gamma+2 gamma^2)`. Points between them are the gapless
  cylinder region; points to the left/right are rendered as `C_y=1`/`C_y=0`.
- Rendered objects: filled `C_y=1`, gapless, and `C_y=0` regions; red
  non-Bloch gapless boundary; gray dotted Bloch boundaries
  `m_\pm=2\pm\sqrt{2}\gamma`; black star at `(m,\gamma)=(1.717,0.2)`.
- Validation checks: generated CSV exists, source-vs-generated comparison
  exists, the star point is classified as `chern_one`, the generated CSV
  matches the analytic boundary, and the digitized source-panel red curve has
  RMSE below `0.025`.
- Numerical risks: the source panel is digitized from the paper PDF, so local
  pixel-level deviations are validation evidence rather than a source of the
  physical boundary.

### NUM003

- Target: `T003`, Fig. 1 open-boundary phase diagram.
- Equations/method cards: `EQC001`, `EQC003`, `EQC005`, `MTH003`.
- Parameters: `t_x=t_y=v_x=v_y=1`, `gamma_x=gamma_y=gamma`,
  `gamma_z=0`, `gamma` scanned over `[0,0.5]`.
- Boundary conditions: the figure is about square open-boundary physics; the
  current runner also implements the square real-space Hamiltonian, but does
  not yet run the full finite-size extrapolation loop.
- Rendered objects: shaded `C=1` region, `C=0` region, red open-boundary
  numerical reference curve, blue dashed non-Bloch theory curve
  `m=2+gamma^2`, gray dotted Bloch boundaries
  `m_\pm=2\pm\sqrt{2}\gamma`, and the two Fig. 2 marker points.
- Validation checks: generated CSV exists, source-vs-generated comparison
  exists, and curve provenance is recorded in
  `outputs/checks/fig1_open_boundary_phase.json`.
- Numerical risks: the red boundary is currently based on the supplemental
  numerical boundary table, so this is not yet an independent finite-size
  square-spectrum reproduction of the red curve.

### NUM004

- Target: `T004`, Fig. 2 square spectra and wave-packet dynamics.
- Equations/method cards: `EQC001`, `EQC006`, `MTH004`.
- Parameters: `L=30`, `t_x=t_y=v_x=v_y=1`, `gamma_x=gamma_y=0.15`,
  `gamma_z=0`, `m=2.2121` for Fig. 2(a), `m=1.7879` for Fig. 2(b).
- Boundary conditions: open `x`, open `y`.
- Solver: sparse square Hamiltonian; eigenvalues closest to zero are computed
  for the spectrum panels, and `scipy.sparse.linalg.expm_multiply` is used for
  `psi(t)=exp(-iHt)psi(0)`.
- Initial state: normalized Gaussian
  `exp-(x-15)^2/40-(y-1)^2/10^T`.
- Rendered objects: two low-energy spectrum marker plots and six normalized
  intensity maps at `t=0,5,20`.
- Validation checks: generated spectrum CSV, wave-packet CSV, check JSON,
  rendered figure, and source-vs-generated comparison exist.
- Numerical risks: the current target is source-visual comparison only; the
  source intensity maps and low-energy points have not yet been digitized into
  a quantitative pixel/dynamics gate.

### NUM005

- Target: `T005`, Supplemental Fig. S2 disk finite-size gap-square fitting.
- Equations/method cards: `EQC001`, `EQC007`, `MTH005`.
- Parameters: disk geometry `x^2+y^2<=L^2`,
  `t_x=t_y=v_x=v_y=1`, `gamma_x=gamma_y=0.2`, `gamma_z=0`,
  `m=2.2000, 2.0800, 2.0400`.
- Radius set: current local run uses `L=20,24,28,32`, matching the original
  figure's `1/L^2` scale but not exhausting the authors' full possible radius
  set.
- Solver: sparse disk Hamiltonian; eigenvalues closest to zero are computed
  with shift-invert sparse eigensolve.
- Gap diagnostic: `|Delta|^2=min |E|^2`.
- Extrapolation: fit `|Delta|^2 = intercept + slope/L^2`; the intercept is
  the thermodynamic-limit gap square.
- Rendered objects: three vertical fit panels with open blue radius samples,
  red dash-dot fit lines, and intercept arrows.
- Validation checks: generated gap CSV, fit CSV, check JSON, rendered figure,
  and source-vs-generated comparison exist.
- Numerical risks: the current radius subset reproduces the nonzero/nonzero/
  near-zero intercept feature, but larger radii and digitized source-curve
  matching are still needed for a stricter method-validation gate.

### NUM006

- Target: `T006`, Supplemental Fig. S3 disk phase diagram.
- Equations/method cards: `EQC001`, `EQC005`, `EQC007`, `MTH006`.
- Parameters: disk geometry, `t_x=t_y=v_x=v_y=1`,
  `gamma_x=gamma_y=gamma`, `gamma_z=0`.
- Rendered objects: red disk numerical boundary reference from the supplement
  table, blue non-Bloch theory curve `m=2+gamma^2`, gray dotted Bloch fan
  `m_\pm=2\pm\sqrt{2}\gamma`, and shaded `C=1/C=0` regions.
- Validation checks: generated CSV, check JSON, rendered figure, and
  source-vs-generated comparison exist.
- Numerical risks: this target checks geometry-independence visually and
  semantically, but the red disk boundary is still a table reference rather
  than a fresh disk finite-size scan over all `gamma`.

## Efficiency And Reuse Plan

- Baseline implementation: direct dense diagonalization for each `k_x`.
- Main bottleneck: repeated eigensolves scale cubically in `2L_y`.
- Efficient implementation choice: no optimization needed for `L_y=40`;
  correctness and traceability come first.
- Complexity or scaling: `O(N_k * (2L_y)^3)`.
- Performance bottleneck removed: none.
- Optional harness promotion candidate: none yet; this model is paper-specific.
- Case-specific parts that should not enter the harness: Hamiltonian terms,
  parameters, and edge-state classification assumptions.
- Performance evidence: first local paper-parameter run finished in about a few
  seconds and wrote `outputs/checks/first_target.json`.
