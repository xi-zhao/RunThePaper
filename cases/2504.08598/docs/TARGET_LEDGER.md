# Target Ledger

Each target is an independently executable scientific objective: formula
evaluation, algorithm/benchmark, simulation, model training/evaluation, or
data analysis. It must serve one or more scoped scientific claims. A target may
produce one or more downstream Figures; the Figure must not define the
generated values.

| Target ID | Scientific claim(s) | Objective | Reproduction mode | Formula/method dependencies | Gate | Status | Data/metric output | Figure evidence | Check output | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T001 | CLM001/2/5 | Execute k=3 A-F and emit H005 controls | simulation | EQ001-4, MTH001-3 | numeric + feature | reproduced | `outputs/data/fig5_*`, `paper_*` | `fig5_k3_annealing_reproduction.png` | `qudit_reproduction_summary.json` | A/B/C/E/F strict curve; D feature |
| T002 | CLM003/5 | Execute k=4 G-I | simulation | EQ002-4, MTH001-3 | feature | reproduced | `fig6_k4_measurement_generated.csv` | generated distributions | `qudit_reproduction_summary.json` | all three pass feature gate |
| T003A | CLM004 | Audit Figure 8 k=2 appendix | simulation | EQ002-4, MTH001-3 | per-item | partial | `fig8_*` | generated data | `qudit_reproduction_summary.json` | curve E/F and distribution E named mismatches |
| T003B | CLM004 | Audit Figure 9 k=3 appendix | simulation | EQ002-4, MTH001-3 | per-item | partial | `fig9_*` | generated data | `qudit_reproduction_summary.json` | distribution H named mismatch |
| T004 | CLM007 | Reconstruct Figure 7 | simulation | EQ002-4 | source consistency | blocked | — | — | `CONSISTENCY_REPORT.md` | protocol-c Omega conflict |

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
