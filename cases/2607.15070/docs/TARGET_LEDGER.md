# Target Ledger

Each numeric figure/table/panel target gets one entry.

| Target ID | Paper item | Type | Formula/method dependencies | Formula gate | Status | Data output | Figure output | Check output | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T001 | Fig. 2(a,b) | two-panel line plot | EQC002-EQC006; MTH001 | verified | reproduced | `outputs/data/fig2_energy_contributions.csv` | `outputs/figures/fig2_left.png`, `fig2_right.png` | `outputs/checks/T001_scientific_checks.json` | All four masses and both panels; paper-exact ranges; six checks passed. |
| T002 | Fig. 3 | ratio line plot | EQC002-EQC007; MTH001 | verified | reproduced | `outputs/data/fig3_energy_ratio.csv` | `outputs/figures/fig3_ratio.png` | `outputs/checks/T002_scientific_checks.json` | Independently recomputes both contributions; five checks passed. |

## Authorization Boundary

Each script requires `--target` and checks
`PRAGENT_GUARDED_TARGET_ID`. T001 never writes T002 artifacts and T002 never
writes T001 artifacts. Data, checks, rendering, and comparison are separate
guarded phases.

## Scientific Boundary

The targets reproduce the paper's displayed renormalized integrals. The
corrected radial-operator derivation and corrected asymptotic formulas are
recorded as mandatory checks; plot agreement is not presented as validation of
the inconsistent paper spectrum.

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
