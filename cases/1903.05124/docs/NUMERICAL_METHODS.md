# Numerical Methods

## Method Cards

### NUM001 — stabilizer dynamics

- Target: T001, T003, T004, T005, T006.
- Equations/method cards: EQC005–EQC008, EQC010, MTH001.
- Parameters: target-specific `L,m,d,p`; paper-realization count 240 where stated.
- Grid or benchmark: paper system sizes through `L=64`; smoke grids are explicitly tagged and never reported as paper-exact.
- Boundary conditions: periodic for the four-part `I3` observable; the half-chain run follows the circuit layout and records its boundary choice.
- Solver: binary stabilizer tableau with GF(2) rank entropy.
- Tolerance: exact binary algebra; statistical convergence is checked with standard errors and split-sample drift.
- Random seed: deterministic `SeedSequence` hierarchy, persisted per run.
- Output schema: long-form CSV plus compressed raw-realization NPZ and JSON metadata.
- Validation checks: dense small-system states, tableau invariants, complement entropy, measurement sign, convergence, and source-pixel guard.
- Numerical risks: paper omits seeds and exact equilibration windows; high-`L,m,d` scans may require checkpointed overnight execution.
- Performance evidence: one paper-geometry trajectory takes `2.58 s` for `d=44,t=40` and `3.45 s` for `d=3,t=300`; the complete 8-setting, 24-realization S3 feature run took `66.33 s`, and the paper-exact 240-realization run took `636.96 s` wall time with eight workers. The wider T001 feature campaign completed 3,804 trajectories in `651.50 s`; T005 added 2,048 midpoint trajectories in `590.18 s`; T006 completed 2,880 trajectories in `771.05 s`. All use persistent worker pools and resumable cell checkpoints.

### NUM002 — frame potential

- Target: T002.
- Equations/method cards: EQC003, EQC004, MTH002.
- Parameters: `n=22`, `d=2..44`, `k=1..4`, final 50,000 samples per depth.
- Solver: binary symplectic composition, GF(2) kernel, phase-aware trace classification.
- Tolerance: exact per-circuit `Q_U`; Monte Carlo standard errors on moments.
- Random seed: deterministic root seed with deterministic child streams for eight independent worker batches.
- Output schema: one row per `(d,k)`, compressed exact `Q_U` samples, and JSON provenance/check metadata.
- Validation checks: complete 11,520-element local Clifford group, dense traces at small `n`, power-of-two/zero trace structure, paper parameters, `F_1..F_3` Haar approach, and trajectory-level 95% test that `F_4>24` for `d>=n`.
- Numerical risks: fourth powers have heavy tails; final sample count and confidence intervals cannot be replaced by a smooth visual fit.

### NUM003 — scaling fits

- Target: T001, T004, T005, T006.
- Equations/method cards: EQC007, EQC008, EQC010, MTH003.
- Solver: deterministic bounded two-parameter collapse search, symmetric interpolation only on common support, source-style measurement-grid bootstrap, and weighted logarithmic regression.
- Tolerance: synthetic `p_c` recovery within `0.002`, synthetic `nu` recovery within `0.04`, explicit search-boundary flags, and leave-one-size-out stability before fitting paper data.
- Output schema: fit JSON, cost-grid NPZ, collapse CSV, and bootstrap samples.
- Numerical risks: finite-size systematic error is larger than bootstrap error; both are reported separately. In the reduced T001 grid, the `d=1` fitted `nu=1.757` reaches the search boundary even though `p_c=0.1631` does not; it is retained as a diagnostic and cannot support a final exponent claim.
- T005 refinement: strict interval midpoints are selected from generated grid coordinates only. They double every periodic `I3` curve from 9 to 17 points without reading old observable values, source pixels, or Table-SI parameters. All eight exponent fits move inside the search bounds, but `nu` still spans `0.679`; larger sizes/statistics—not more visual tuning—are required for final acceptance.
- T004 entropy collapse: the same independently generated trajectory pool supplies half-chain entropy, but T004 performs a fresh EQC007 fit and 100-repeat measurement-grid bootstrap. All eight fits are interior; mean `p_c` error is `0.01182`, mean `nu=1.074`, and the extensive-entropy derivative—not the normalized-density derivative—is used for the formula-level sharpening invariant.
- T006 block-size scaling: for each exact paper block size `m=3,5,7,9,11,13` at `d=3m`, a nine-point generated `I3` grid is followed by four interval midpoints selected only from the preliminary generated fit. Fresh EQC008 fits determine `p_c,nu`; independent critical-entropy trajectories at those fitted `p_c` values determine `alpha` through EQC010. Constancy is assessed with uncertainty-weighted reduced chi-square and maximum pairwise standardized separation, not raw range alone.

## Efficiency And Reuse Plan

- Baseline implementation: dense state vectors only for `n<=10` validation.
- Main bottleneck: repeated random Clifford gates and entropy ranks over up to 704 qubits, multiplied by parameter grids and 240 realizations.
- Efficient implementation choice: packed binary tableau/rank operations, deterministic batches, and checkpointed aggregate statistics.
- Shared-observable optimization: one evolved trajectory now supplies both half-chain entropy and the seven subsystem entropies entering `I3`; T001/T004/T005 do not rerun identical circuits for each observable.
- Complexity or scaling: polynomial in qubit count per Clifford/measurement operation; no `2^(Lm)` state vector appears in production runs.
- Performance bottleneck removed: MTH002 replaces a `2^22 x 2^22` trace with a `44 x 44` binary kernel problem.
- Reusable workflow candidate: a generic source-pixel guard and checkpointed Monte Carlo ledger; the scientific stabilizer implementation remains case code until independently reused.
- Case-specific parts remain local: qubit-block layout, observables, paper parameter grids, and acceptance thresholds.
- Performance evidence: T002 smoke took `0.66 s`; feature scale took `18.46 s` serial and `3.56 s` with eight workers; the paper-exact 50,000-sample run took `179.30 s` with eight workers.
