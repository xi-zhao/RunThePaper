# Target Ledger

Each numeric figure/table/panel target gets one entry.

| Target ID | Paper item | Type | Formula dependencies | Formula gate | Status | Data output | Figure output | Check output | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T001 | Main Fig. 1(a) | Husimi-Q surface | EQ004 | open | algorithmically_consistent | `outputs/data/T001_main_fig1a_husimi.csv` | `outputs/figures/T001_main_fig1a_husimi.png` | `outputs/checks/target_checks.json` | N=20, tau=0 |
| T002 | Main Fig. 1(b) | Husimi-Q surface | EQ004 | open | algorithmically_consistent | `outputs/data/T002_main_fig1b_husimi.csv` | `outputs/figures/T002_main_fig1b_husimi.png` | `outputs/checks/target_checks.json` | N=20, tau=N^(-2/3) |
| T003 | Main Fig. 1(c) | eigenvalue curves | EQ001, EQ002, EQ004, EQ005 | open | algorithmically_consistent | `outputs/data/T003_main_fig1c_qfim.csv` | `outputs/figures/T003_main_fig1c_qfim.png` | `outputs/checks/target_checks.json` | analytic and numerical paths both pass |
| T004 | Main Fig. 1(d) | generator path | EQ001, EQ002, EQ004, EQ005 | open | algorithmically_consistent | `outputs/data/T004_main_fig1d_generator.csv` | `outputs/figures/T004_main_fig1d_generator.png` | `outputs/checks/target_checks.json` | projector invariant plus deterministic representative |
| T005 | Main Fig. 2(a) | SU(4) eigenvalue curves | EQ001, EQ002, EQ003, EQ006, EQ007 | open | algorithmically_consistent | `outputs/data/T005_main_fig2a_qfim.csv` | `outputs/figures/T005_main_fig2a_qfim.png` | `outputs/checks/target_checks.json` | N=20 exact symmetric space |
| T006 | Main Fig. 2(b) | coefficient heatmap | EQ001, EQ002, EQ003, EQ006 | open | algorithmically_consistent | `outputs/data/T006_main_fig2b_coefficients.csv` | `outputs/figures/T006_main_fig2b_coefficients.png` | `outputs/checks/target_checks.json` | deterministic gauge; projector invariants are primary |

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

For `blocked` or `planned_large_scale` targets, add a plan document and config
path in the `Notes` column, for example:

```text
PLANNED_LARGE_SCALE_RUNS.md
config/<target>_recommended.yaml
```
