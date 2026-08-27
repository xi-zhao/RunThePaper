# Target Ledger

Each target is an independently executable scientific objective: formula
evaluation, algorithm/benchmark, simulation, model training/evaluation, or
data analysis. It must serve one or more scoped scientific claims. A target may
produce one or more downstream Figures; the Figure must not define the
generated values.

| Target ID | Scientific claim(s) | Objective | Reproduction mode | Formula/method dependencies | Gate | Status | Data/metric output | Figure evidence | Check output | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T001 | CLM002 | Solve the continuum domain wall and place its edge curve against independently sampled bulk-energy regions. | formula numericalization | EQC002, EQC003, MTH002 | formula and method open | reproduced | bulk NPZ and edge CSV; max matching residual `1.43e-14`; minimum localization margin `0.649` | `outputs/figures/main_fig1_reproduction.png` | `outputs/checks/t001_scientific_checks.json` | Paper-exact parameters; contiguous localized branch connects the independently generated bulk sheets. No source pixels in solver. |
| T002 | CLM003, CLM004 | Evaluate the canonical EP model, track branches continuously, and verify half winding, defectiveness, and square-root scaling. | analytic reference + direct diagonalization | EQC004, EQC007, MTH001 | open | reproduced | loop/cut CSV, surface NPZ; `|nu|=0.5`; exponent `0.5000000014` | `outputs/figures/main_fig2_reproduction.png` | `outputs/checks/t002_scientific_checks.json` | Seven scientific checks pass; pixel target declared and evidence pending. |
| T003 | CLM005 | Generate separable/inseparable regions and closed-form EP trajectories. | formula numericalization | EQC002, EQC006, MTH001 | open | reproduced | phase NPZ and trajectory CSV; opposite `±1/2` charges | `outputs/figures/main_fig3_reproduction.png` | `outputs/checks/t003_scientific_checks.json` | EP residual and ellipse identity pass at machine precision; pixel tuning pending. |
| T004 | CLM002 | Solve the domain-wall matching equations over `(kappa_y1,kappa_y2)` and test the zero-energy line. | formula numericalization | EQC003, MTH002 | formula and method open | reproduced | complex-energy surface NPZ; closed-form/root error `6.20e-16`; zero-plane error `0` | `outputs/figures/supp_fig2_reproduction.png` | `outputs/checks/t004_scientific_checks.json` | Algebraic common-spinor solution cross-checked by independent nonlinear roots. |
| T005 | CLM006 | Build the `80×80` cylinder matrix for each `k_y` and diagonalize both caption parameter sets. | independent numerics | EQC005, MTH003 | formula and method open | reproduced | complex bands plus left/right boundary weights NPZ | `outputs/figures/supp_fig3_reproduction.png` | `outputs/checks/t005_scientific_checks.json` | Paper-exact `n=40`; 482 eigensystems, max residual `1.60e-15`, edge-dispersion error `6.19e-15`. |
| T006 | CLM005 | Evaluate hybrid-point surfaces and orthogonal cuts; fit the two anisotropic exponents. | formula numericalization | EQC006, MTH001 | open | reproduced | surface NPZ, two cut CSVs; exponents `0.5000000000` and `1.0000000000` | `outputs/figures/supp_fig4_reproduction.png` | `outputs/checks/t006_scientific_checks.json` | Paper-exact `m=delta=1`; zero winding and defectiveness pass; pixel tuning pending. |

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
