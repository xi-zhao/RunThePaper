# Method Trace

## METHOD001 — Scientific-before-render pipeline

- Inputs: printed formulas and explicit primary-source parameter rows.
- Numerical action: generate T001--T007 NPZ files in the isolated runner.
- Freeze: hash every generated data file and bind it to the run attestation.
- Render action: read only the frozen NPZ files and a separate render contract.
- Reference action: crop original panels only after the data freeze.
- Comparison: scientific features first; pixels only where registration is
  meaningful.
- Forbidden: digitizing curves, tracing vector paths, loading author arrays,
  or tuning physical parameters against figure pixels.

## METHOD002 — Paper-scale 3D dynamics

- Source: supplement “Numerical simulations”, Eqs. (3)--(6), Main Fig. 4
  discussion, and Supplement Fig. S2 caption.
- Preparation: solve the single-component state-2 trapped GPE in imaginary
  time at the configured field and atom number.
- Main Fig. 4 event: copy the prepared spatial mode into a 50/50 two-component
  state, release into the levitation potential, and evolve the coupled local-LHY
  equations without losses.
- Supplement Fig. S2 event: retain the state-2 component and evolve either in
  free space or with 12 Hz vertical confinement, with LHY disabled.
- Propagator: second-order Strang split-step FFT in three Cartesian dimensions.
- State: every task is identified by a canonical config hash; checkpoints store
  that hash, fields, step number, and accumulated observables.
- Resume invariant: a checkpoint made from a different task/config is rejected.
- Observable boundary: Main Fig. 4 reports
  `sigma=2*sqrt(RMS_x*RMS_z)`; S2 reports the moment-equivalent vertical
  Thomas-Fermi radius `sqrt(7)*RMS_z`.
- Scientific gates: norm drift, outer-box mass, finite/bounded values,
  512³-production-vs-640³ grid refinement, production-vs-half-step refinement, LHY
  energy-derivative check, and radial Pohozaev identity.
- Execution status: NumPy smoke path passed; the 12-task CuPy production lane is
  code-ready and unrun.

## METHOD003 — Paper-review classification

- Solver, invariant, convergence, or implementation failures are
  `reproduction_defect`.
- Missing unpublished atom numbers are `missing_source_input`; an N=4e5 run is
  an explicit assumption/sensitivity result, never a paper-exact result.
- The persistent T005 branch-order difference is `inconclusive` because the
  theory-width functional and paper-exact scattering model are missing.
- `paper_error_candidate` is forbidden unless paper-exact inputs, frozen
  paper-scale data, convergence, two genuinely independent passing methods,
  explicit falsification, a full discrepancy record, and fresh-context review
  all pass protocol-v2.
