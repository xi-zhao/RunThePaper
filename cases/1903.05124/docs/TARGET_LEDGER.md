# Target Ledger

Each target is an independently executable scientific objective: formula
evaluation, algorithm/benchmark, simulation, model training/evaluation, or
data analysis. It must serve one or more scoped scientific claims. A target may
produce one or more downstream Figures; the Figure must not define the
generated values.

| Target ID | Scientific claim(s) | Objective | Reproduction mode | Formula/method dependencies | Gate | Status | Data/metric output | Figure evidence | Check output | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T001 | CLM004, CLM005 | Simulate Main Fig. 2(b–e): protected entropy growth, measurement-induced entropy change, steady-state density, and `(d/m,p)` phase diagram. | independent stabilizer numerics | EQC002, EQC005, EQC006, EQC008; MTH001, MTH003 | formula, dynamics, and finite-size methods verified | partial | 3,804-trajectory CSV/raw NPZ plus eight independently fitted transition markers | `outputs/figures/main_fig2_reproduction.png`; feature presentation `75.09`, SSIM `0.64918` | `outputs/checks/t001_scientific_checks.json`, `outputs/checks/pixel_evidence.json` | All four panels pass at paper geometry with reduced sampling/grid; mean Table-SI `p_c` error `0.00409`; final paper-scale precision remains open. |
| T002 | CLM003 | Estimate `F^(1..4)` for the depth-`d`, `n=22` random Clifford ensemble and test the unitary-design interpretation. | independent Clifford numerics | EQC003, EQC004; MTH002 | formula and method verified | reproduced | `outputs/data/supp_fig_s2_frame_potential.csv`, 50,000 exact `Q_U` samples per depth; late-depth `F4=29.00±0.85` | `outputs/figures/supp_fig_s2_reproduction.png`; presentation `62.05`, SSIM `0.76454` | `outputs/checks/t002_scientific_checks.json`, `outputs/checks/pixel_evidence.json` | Paper-exact 22 depths and sample count; 95% lower bound `27.34>24`; source pixels absent from generation. |
| T003 | CLM004 | Simulate all eight regimes in Supp. Fig. S3, retaining both entropy and `Delta S_meas` observables. | independent stabilizer numerics | EQC002, EQC005, EQC006; MTH001 | formula and method verified | reproduced | 1,920 raw trajectories plus sixteen mean/SD/SE time series | `outputs/figures/supp_fig_s3_reproduction.png`; presentation `71.90`, SSIM `0.73621` | `outputs/checks/t003_scientific_checks.json`, `outputs/checks/pixel_evidence.json` | Paper-exact `L=32,m=11`, eight settings, 240 realizations each; source pixels absent; likely caption SD/SE inconsistency recorded. |
| T004 | CLM005 | Reproduce half-chain size scaling, three measurement scans, three data-collapse insets, and `nu(d)`. | independent stabilizer numerics plus scaling fit | EQC005, EQC007; MTH001, MTH003 | dynamics and scaling method verified | partial | shared 4,352-trajectory entropy ensemble, 17-point curves, collapse coordinates, and eight fresh `p_c,nu` fits | `outputs/figures/supp_fig_s4_reproduction.png`; feature presentation `67.27`, SSIM `0.69957` | `outputs/checks/t004_scientific_checks.json`, `outputs/checks/pixel_evidence.json` | All ten items and every core/exponent check pass; mean `p_c` error `0.01182`, mean `nu=1.074`; paper sizes through `L=64` remain to extend. |
| T005 | CLM005, CLM006 | Reproduce `I3(p,L)`, three collapses, and the more reliable `nu(d)` estimate. | independent stabilizer numerics plus scaling fit | EQC005, EQC008; MTH001, MTH003 | dynamics and scaling method verified | partial | 4,352 independent trajectories, 17-point curves, collapse coordinates, and eight fitted `p_c,nu` pairs | `outputs/figures/supp_fig_s5_reproduction.png`; feature presentation `67.03`, SSIM `0.81619` | `outputs/checks/t005_refinement_checks.json`, `outputs/checks/t005_scientific_checks.json`, `outputs/checks/pixel_evidence.json` | All seven panels and nine core checks pass; mean `p_c` error `0.00484`, but `nu` span `0.679` fails weak-depth-dependence. Sizes stop at `L=24` and each cell uses eight realizations. |
| T006 | CLM006, CLM007 | At fixed `d/m=3`, reproduce `p_c(m)`, `nu(m)`, and `alpha(m)` for `m=3,5,7,9,11,13`. | independent stabilizer numerics plus scaling fit | EQC002, EQC008, EQC010; MTH001, MTH003 | dynamics and scaling methods verified | partial | 2,880 independent trajectories, adaptive `I3` grids, six `p_c,nu` fits, and six critical-entropy regressions | `outputs/figures/supp_fig_s6_reproduction.png`; feature presentation `66.45`, SSIM `0.88215` | `outputs/checks/t006_scientific_checks.json`, `outputs/checks/pixel_evidence.json` | All three panels and frozen science checks pass; `p_c` grows `0.596→0.913`, mean `nu=0.989`, and `alpha` is constant-compatible within uncertainty. Sizes stop at `L=24` versus paper `L=64`. |

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
