# Method Trace

## MTH001 — Independent symmetric-sector Liouvillian

- Inputs: equations, printed couplings, generated `N_b` values.
- Operations: construct `Sx,Sy,Sz,S±`; assemble sparse Lindblad superoperator; propagate, solve the NESS, or diagonalize.
- Outputs: spectra, magnetization, FFT, moments, variances, decay rates.
- Checks: spin commutator, trace preservation, NESS residual, eigenpair residual, density positivity.
- Forbidden inputs: paper pixels, vector paths, digitized coordinates, author code, author arrays.

## MTH002 — Independent semiclassical integration

- Inputs: supplement Eq. (S7), printed `omega_0,kappa,omega_x,omega_z`, deterministic initial-condition grid.
- Operations: DOP853 integration on the unit sphere; transform to `(Q,P)`; evaluate conserved `R` formula.
- Outputs: all S5–S7 phase-space data and the thermodynamic curves.
- Checks: maximum norm drift and parameter labels.

## MTH003 — Post-freeze RenderContract

- Inputs: frozen CSV hashes, declarative plot layout, original panels as reference-only assets.
- Allowed changes: figure size, axes placement, font, markers, line styles, palette, interpolation, crop.
- Forbidden changes: numerical arrays, physical parameters, solver output, target membership.

## MTH004 — Resumable paper-scale campaign

- Inputs: formula-derived case source and `config/paper_scale.json` only.
- Operations: expand 215 immutable jobs; run CPU backend parity; checkpoint dynamics
  time blocks; freeze per-parameter NPZ shards; aggregate only a complete hash-valid
  job set; apply one machine contract to each T001–T024.
- NESS specialization: reconstruct the shifted-jump identity from Eq. (2), form the
  exact finite-N Gram steady state on `N_b+1` states, and check its residual against
  the separately assembled Liouvillian.  Direct sparse steady-state parity at small N
  is mandatory.
- Outputs: 11 paper-scale CSVs, backend parity, target acceptance, machine record, run
  summary, and frozen manifest under `outputs/paper_scale/`.
- Checks: config/result SHA-256, dense NumPy/SciPy parity, sparse/dense leading-mode
  parity, direct/Gram NESS parity, monolithic/chunked dynamics parity, residuals,
  trace/Hermiticity, and sphere norm.
- Boundary: code readiness and smoke pass are not final-run evidence.  Protocol-v2
  scientific review remains separate and emits no `paper_error_candidate` here.
- Forbidden inputs: `raw/`, original/reference images, digitized curves, author code,
  author arrays, and network access.
