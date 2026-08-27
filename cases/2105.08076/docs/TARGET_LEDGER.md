# Target Ledger

| Target | Paper item | Scientific object | Formula dependencies | Gate | Current status | Data | Figure |
| --- | --- | --- | --- | --- | --- | --- | --- |
| T001 | Main Fig. 1(c) | Effective-central-charge phase map | EQ001-EQ003, EQ005 | verified | feature_reproduced | `outputs/data/T001_phase_map.csv` | `outputs/figures/T001_main_fig1c.png` |
| T002 | Main Fig. 1(d) | Correlation exponent `a(p,gamma)` | EQ001-EQ005, EQ008 | verified | feature_reproduced | `outputs/data/T002_correlation_exponent.csv` | `outputs/figures/T002_main_fig1d.png` |
| T003 | Main Fig. 1(e) | Entropy exponent `b(p,gamma)` | EQ001-EQ003, EQ005, EQ008 | verified | feature_reproduced | `outputs/data/T003_entropy_exponent.csv` | `outputs/figures/T003_main_fig1e.png` |
| T004 | Main Fig. 2(a) | Half-chain entropy scaling | EQ001-EQ003, EQ005 | verified | feature_reproduced | `outputs/data/T004_entropy_size.csv` | `outputs/figures/T004_main_fig2a.png` |
| T005 | Main Fig. 2(b) | Opposite-point positive correlation scaling | EQ001-EQ005 | verified | feature_reproduced | `outputs/data/T005_correlation_size.csv` | `outputs/figures/T005_main_fig2b.png` |
| T006 | Main Fig. 3(a) | Size-dependent effective central charge | EQ001-EQ003, EQ005 | verified | feature_reproduced | `outputs/data/T006_effective_central_charge.csv` | `outputs/figures/T006_main_fig3a.png` |
| T007 | Main Fig. 3(b) | Dark-state algebraic scaling relation | EQ003, EQ007, EQ008 | verified | partial_failed_slope | `outputs/data/T007_algebraic_scaling.csv` | `outputs/figures/T007_main_fig3b.png` |
| T008 | Supplement Fig. 1(a) | Subsystem entropy collapse and inset | EQ001-EQ003, EQ005 | verified | feature_reproduced | `outputs/data/T008_subsystem_entropy.csv` | `outputs/figures/T008_supp_fig1a.png` |
| T009 | Supplement Fig. 1(b) | Subsystem correlation collapse and inset | EQ001-EQ005 | verified | feature_reproduced | `outputs/data/T009_subsystem_correlation.csv` | `outputs/figures/T009_supp_fig1b.png` |

All nine targets share one independent numerical implementation and one
paper-scale campaign contract.  The feature run is attested and the A100
campaign is code-ready for 450 conditions and 37,440 trajectories.  It remains
unexecuted, so no target is `paper_exact`.  T007 retains one failed joint
scientific assertion and is finalized as attempted but not reproduced.
