# Numerical Methods

## Shared Parameter Card

| Quantity | Value | Provenance |
| --- | ---: | --- |
| cavity-emitter coupling `g` | 1.5 meV | paper |
| hopping disorder `delta_t` | 0.5 meV | paper |
| mean hopping `t` | 1.0 meV | reconstructed from QCLE peak and cross-figure endpoints |
| coherent detuning | 0 unless T007 | paper protocol |
| cavity drain rate | 0.5 meV | paper |
| source state | `|1><1|` | reconstructed from source schematic/text |
| disorder seeds | consecutive from 0 | author says fixed seeds but does not publish them |
| units | energy/rate in meV; time in `hbar/meV` | paper |

All generated artifacts therefore declare `parameter_match=paper_subset` and `artifact_stage=exploratory`.

## Method Cards

### NUM001 — Lindblad generator and propagation

- Targets: T001–T010
- Equations: EQ001, EQ003, EQ006
- State space: `d=N+2` with cavity, N emitters, and sink.
- Vectorization: column-stacked `vec(rho)`.
- Generator:
  `-i(I kron H - H^T kron I) + sum_mu D[L_mu]`.
- Solver: `scipy.sparse.linalg.expm_multiply`, applied to the initial vector without forming the dense matrix exponential.
- Baseline equivalence: compared against `scipy.linalg.expm` for a small mixed-channel model.
- Tolerance: maximum density-matrix difference `<1e-10`; observed `3.40e-16`.
- Physicality: trace and Hermiticity errors `<1e-10`, minimum density eigenvalue `>-1e-10`.
- Numerical risk: incorrect Kronecker ordering silently changes the master equation; a sparse-vs-dense regression test protects this invariant.

### NUM002 — Disorder ensemble and rate optimization

- Targets: T001, T005, T006, T008
- Disorder: `t_i=t+delta_t X_i`, independent standard-normal `X_i` per bond.
- Pairing: each mechanism uses the same realization seeds.
- Optimization: log-spaced coarse scan plus local log refinement; T001 uses 5 pilot seeds to choose a rate and 15 seeds to evaluate it.
- Large-N dephasing: upper bound increases from 10 to 100 meV at `N>=48`, following the paper.
- Output: tidy CSV rows with mean, SEM, selected rate, sample count, parameter match, and artifact stage.
- Numerical risk: the author grid and seeds are absent, so optimum-sensitive site-N values need wider tolerances than Table S2.

### NUM003 — Dynamics and finite temperature

- Targets: T002–T004, T009, T010
- Time propagation: evenly sampled `0..30` for main dynamics; `0..60` for site-N dynamics.
- Temperature law: `gamma_abs/gamma_rec=exp[-Delta/(k_B T)]`, represented by the dimensionless ratio `k_B T/Delta`.
- Boundary extraction: interpolate the `Delta eta=0` crossing linearly in `Delta eta` and logarithmically in the rate ratio.
- N=6 map: 15 realizations, `15x15` grid.
- N=64 map: 5 realizations, `9x9` grid in the committed exploratory output.
- Numerical risk: contour appearance is grid-dependent; acceptance uses the interpolated boundary and endpoint values rather than pixels.

### NUM004 — Paper-facing evaluation

- Targets: T001–T010
- Input: committed CSV/JSON observables only; figures are not numerical truth.
- Checks: 26 claims covering invariants, monotonicity, printed endpoints, table error, fitted coefficients, zero-boundaries, and mechanism rankings.
- Score: feature match `/50`, numeric closeness `/35`, paper scope `/15`, followed by evidence and parameter caps.
- Output: `numerical_feature_checks.json`, `source_comparisons.json`, and `similarity_scorecard.json`.

## Efficiency And Reuse Plan

- Baseline implementation: dense Liouvillian exponential, matching the paper's stated SciPy method.
- Main bottleneck: repeated matrix exponentials over large N, rates, and disorder seeds.
- Efficient choice: sparse Liouvillian action with cached Hamiltonian/channel generators per realization.
- Scaling: avoids explicitly constructing the dense exponential; ensemble work is embarrassingly parallel over seeds.
- Reusable core: `TransportModel`, `ChannelRates`, `PreparedTransport`, and the column-vectorized generator.
- Case-local layer: paper target grids, reconstructed parameters, figure layout, and acceptance thresholds.
- Evidence: 15-sample scaling through N=96 completed in 347.17 s on a 16-GiB M4 machine while preserving dense equivalence to `3.40e-16` on the regression model.
