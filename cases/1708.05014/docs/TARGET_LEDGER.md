# Target Ledger

`Current evidence` describes the already frozen feature run.  `Paper-scale channel`
describes runnable code only; it must not be read as a completed paper-scale result.
Every numerical target shares the top-level coverage implementation
`paper_scale_all_targets`, whose per-target machine criteria live in
`config/paper_scale.json::targets`.

| Target | Paper region | Formula | Current parameter match | Current evidence | Paper-scale channel | Expected paper-scale dataset |
| --- | --- | --- | --- | --- | --- | --- |
| T001 | Main Fig. 1(c) dynamics | EQ002, EQ003, EQ006 | reduced_scale | feature_compared | ready: chunked `N_b=40,80,160` + limit | `outputs/paper_scale/data/main_fig1_dynamics.csv` |
| T002 | Main Fig. 2 left spectrum | EQ002, EQ004 | reduced_scale | feature_compared | ready: full `N_b=36`, ratio 0.5 | `outputs/paper_scale/data/main_fig2_spectrum.csv` |
| T003 | Main Fig. 2 left inset | EQ002, EQ004 | reduced_scale | feature_compared | ready: shared full strong spectrum | `outputs/paper_scale/data/main_fig2_spectrum.csv` |
| T004 | Main Fig. 2 right spectrum | EQ002, EQ004 | reduced_scale | feature_compared | ready: full `N_b=36`, ratio 1.5 | `outputs/paper_scale/data/main_fig2_spectrum.csv` |
| T005 | Main Fig. 2 right inset | EQ002, EQ004 | reduced_scale | feature_compared | ready: shared full BTC spectrum | `outputs/paper_scale/data/main_fig2_spectrum.csv` |
| T006 | Main Fig. 3 left scaling | EQ004 | reduced_scale | feature_compared | ready: sharded BTC Arnoldi; N-list reconstructed | `outputs/paper_scale/data/main_fig3_scaling.csv` |
| T007 | Main Fig. 3 right bands | EQ004 | reduced_scale | feature_compared | ready: same converged BTC eigenpairs | `outputs/paper_scale/data/main_fig3_scaling.csv` |
| T008 | Main Fig. 4 left FFT | EQ003 | reduced_scale | feature_compared | ready: FFT only from completed T001 series | `outputs/paper_scale/data/main_fig4_fourier.csv` |
| T009 | Main Fig. 4 inset | EQ003, EQ006 | paper_exact | artifact_valid, review_pending | ready: thermodynamic ODE/FFT in campaign | `outputs/paper_scale/data/main_fig4_fourier.csv` |
| T010 | Main Fig. 4 right decay | EQ004 | reduced_scale | feature_compared | ready: leading oscillatory mode per N | `outputs/paper_scale/data/main_fig4_decay.csv` |
| T011 | Supplement S2 left moments | EQ005 | reduced_scale | feature_compared | ready: `N_b=600` shifted-jump Gram NESS | `outputs/paper_scale/data/supp_phase_diagram.csv` |
| T012 | Supplement S2 right semantics | EQ005 | reduced_scale | source_discrepancy_recorded | ready: centered/squared/second moments all retained | `outputs/paper_scale/data/supp_phase_diagram.csv` |
| T013 | Supplement S3 left | EQ004 | reduced_scale | feature_compared | ready: sharded strong-phase Arnoldi | `outputs/paper_scale/data/supp_real_scaling_strong.csv` |
| T014 | Supplement S3 right | EQ004 | reduced_scale | feature_compared | ready: shared BTC scaling eigenpairs | `outputs/paper_scale/data/main_fig3_scaling.csv` |
| T015 | Supplement S4 | EQ004 | reduced_scale | feature_compared | ready: 148 `(N_b,coupling)` shards | `outputs/paper_scale/data/supp_imaginary_gap.csv` |
| T016 | Supplement S5a | EQ006, EQ007 | paper_subset | printed couplings; independent initials/grid | ready: dense deterministic ODE grid | `outputs/paper_scale/data/supp_phase_trajectories.csv` |
| T017 | Supplement S5b | EQ006, EQ007 | paper_subset | printed couplings; independent initials/grid | ready: dense deterministic ODE grid | `outputs/paper_scale/data/supp_phase_trajectories.csv` |
| T018 | Supplement S5c | EQ006, EQ007 | paper_subset | printed couplings; independent initials/grid | ready: dense deterministic ODE grid | `outputs/paper_scale/data/supp_phase_trajectories.csv` |
| T019 | Supplement S5d | EQ006, EQ007 | paper_subset | printed couplings; independent initials/grid | ready: dense deterministic ODE grid | `outputs/paper_scale/data/supp_phase_trajectories.csv` |
| T020 | Supplement S6 | EQ006, EQ007 | paper_subset | printed field formula/couplings; independent grid/trajectories | ready: independent formula field + ODE trajectories | `outputs/paper_scale/data/supp_branch_surface.csv`; `supp_branch_trajectories.csv` |
| T021 | Supplement S7a | EQ006, EQ007 | paper_subset | printed couplings; independent initials/grid | ready: dense deterministic ODE grid | `outputs/paper_scale/data/supp_phase_trajectories.csv` |
| T022 | Supplement S7b | EQ006, EQ007 | paper_subset | printed couplings; independent initials/grid | ready: dense deterministic ODE grid | `outputs/paper_scale/data/supp_phase_trajectories.csv` |
| T023 | Supplement S7c | EQ006, EQ007 | paper_subset | printed couplings; independent initials/grid | ready: dense deterministic ODE grid | `outputs/paper_scale/data/supp_phase_trajectories.csv` |
| T024 | Supplement S7d | EQ006, EQ007 | paper_subset | printed couplings; independent initials/grid | ready: dense deterministic ODE grid | `outputs/paper_scale/data/supp_phase_trajectories.csv` |

## Gates that remain after code readiness

- T001–T008 and T010–T015 retain their current reduced-scale state until the full
  campaign produces hash-valid data and evidence files are deliberately rebuilt.
- Reconstructed finite-size/sample grids for T006–T007, T010, T013–T015 and
  presentation grids for T016–T024 require explicit parameter/reference review; a
  successful computation is not automatic `paper_exact` evidence.
- T016–T024 are now explicitly `paper_subset`: their equations and panel
  couplings match the supplement, but the author trajectory initials and full
  sampling grids are unavailable. Their figures are exploratory scientific
  reproductions, not final paper-exact artifacts.
- T012 remains an unresolved stable semantic discrepancy.  Protocol-v2 forbids
  `paper_error_candidate` without paper-exact execution, convergence, two independent
  cross-checks, falsification evidence, strict comparison, and fresh review.
- All 24 targets still require the independent fresh-context review already reported
  by authoritative `project inspect`.
