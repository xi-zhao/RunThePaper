# Target Ledger

Each numeric figure/table/panel target gets one entry.

| Target ID | Paper item | Type | Formula dependencies | Formula gate | Status | Data output | Figure output | Check output | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T001 | Main Fig. 2 left - theory loci | analytic sweep | EQ002, EQ003 | verified | reproduced | `outputs/data/T001_main_fig2_left.csv` | `outputs/figures/T001_main_fig2_left.png` | `outputs/checks/target_checks.json` | paper-exact printed `alpha` values; experimental markers excluded |
| T002 | Main Fig. 2 right - `a_-` | analytic sweep | EQ004, EQ005 | verified | reproduced | `outputs/data/T002_main_fig2_right.csv` | `outputs/figures/T002_main_fig2_right.png` | `outputs/checks/target_checks.json` | paper-exact `alpha=0.94`, `gamma_f'=15` |
| T003 | Main Fig. 4 - theory curves | exact propagation | EQ003, EQ006 | verified | reproduced | `outputs/data/T003_main_fig4_theory.csv` | `outputs/figures/T003_main_fig4_theory.png` | `outputs/checks/target_checks.json` | theory layer only; no author measurements |
| T004 | Supplement Fig. 1 | analytic spectrum | EQ004 | verified | reproduced | `outputs/data/T004_supp_fig1.csv` | `outputs/figures/T004_supp_fig1.png` | `outputs/checks/target_checks.json` | paper-exact `alpha=1`, `gamma_f' in [0,10]` |
| T005 | Supplement Fig. 2 | analytic loci | EQ003, EQ004 | verified | reproduced | `outputs/data/T005_supp_fig2.csv` | `outputs/figures/T005_supp_fig2.png` | `outputs/checks/target_checks.json` | all five displayed loci and bifurcation branches |
| T006 | Supplement Fig. 3 | geometric modes | EQ003-EQ005 | verified | reproduced | `outputs/data/T006_supp_fig3.csv` | `outputs/figures/T006_supp_fig3.png` | `outputs/checks/target_checks.json` | complete displayed family of fast-mode chords |
| T007 | Supplement Fig. 4 left | exact propagation | EQ003, EQ005, EQ006 | verified | reproduced | `outputs/data/T007_supp_fig4_left.csv` | `outputs/figures/T007_supp_fig4_left.png` | `outputs/checks/target_checks.json` | all three printed initial temperatures |
| T008 | Supplement Fig. 4 right | exact late-time propagation | EQ003, EQ005, EQ006 | verified | reproduced | `outputs/data/T008_supp_fig4_right.csv` | `outputs/figures/T008_supp_fig4_right.png` | `outputs/checks/target_checks.json` | same data, separately scored subpanel |
| T009 | Supplement Fig. 5 left | root sweep | EQ003, EQ005, EQ006 | verified | reproduced | `outputs/data/T009_supp_fig5_left.csv` | `outputs/figures/T009_supp_fig5_left.png` | `outputs/checks/target_checks.json` | exact crossing-time solve |
| T010 | Supplement Fig. 5 right | optimization sweep | EQ003, EQ005, EQ006 | verified | reproduced | `outputs/data/T010_supp_fig5_right.csv` | `outputs/figures/T010_supp_fig5_right.png` | `outputs/checks/target_checks.json` | exact post-crossing maximum |
| T011 | Main-vs-supplement dissipator-rate consistency | analytic claim | EQ001, EQ002, EQ008 | source_only | uncovered | N/A | N/A | `outputs/checks/paper_consistency_checks.json` | exact factor-two conflict; fresh-context adjudication pending; code fault not found after three checks |
| T012 | Experimental-prose Hamiltonian normalization | analytic claim | EQ001, EQ002 | source_only | uncovered | N/A | N/A | `outputs/checks/paper_consistency_checks.json` | `Omega` vs `Omega/2` source conflict; fresh-context definition audit pending |

## Status Values

- `not_started`
- `spec_ready`
- `running`
- `reproduced`
- `physically_consistent`
- `algorithmically_consistent`
- `partial`
- `blocked`
- `planned_large_scale`
- `failed`
- `uncovered`

For `blocked` or `planned_large_scale` targets, add a plan document and config
path in the `Notes` column, for example:

```text
PLANNED_LARGE_SCALE_RUNS.md
config/<target>_recommended.yaml
```
