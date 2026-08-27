# Target Ledger

| ID | Paper item | Formula dependencies | Gate | Status | Planned data / figure |
| --- | --- | --- | --- | --- | --- |
| T001 | Fig. 1(c) | EQ001, EQ003, EQ006 | open | passed | `size_scaling.csv`, `fig1c_size_scaling.png` |
| T002 | Fig. 2(a,b) | EQ001, EQ003-EQ007 | open | passed | `fig2_dynamics.csv`, `fig2_reproduction.png` |
| T003 | Fig. 2(c,d) | EQ001, EQ003-EQ007 | open | passed | same tidy data/figure as T002 |
| T004 | Fig. 3(a-c) | EQ001-EQ003, EQ006 | open | passed | `temperature_*.csv`, `fig3_temperature.png` |
| T005 | Fig. S1(a,b), map/markers/pure-channel cuts | EQ001, EQ003, EQ006 | open | passed | `site_n_sweep.csv`, `figS1_site_n_sweep.png` |
| T006 | Table S1 | EQ001, EQ003, EQ006 | open | passed | `table_s1_regimes.csv` |
| T007 | Table S2 | EQ001, EQ003, EQ006 | open | passed | `table_s2_detuning.csv` |
| T008 | Fig. S2(a,b) | T001 data, EQ004 | open | passed | `scaling_fits.json`, `figS2_scaling_laws.png` |
| T009 | Fig. S3(a,b) | EQ001, EQ003, EQ006, EQ007 | open | passed | `site_n_dynamics.csv`, `figS3_site_n_dynamics.png` |
| T010 | Fig. S4 | EQ001-EQ003, EQ006 | open | passed_reduced_grid | `temperature_map_n64.csv`, `figS4_temperature_n64.png` |
| T011 | Fig. S5, four benchmark series | QCLE Eq. (S18) | blocked | blocked_missing_parameter | publication omits indispensable QCLE benchmark inputs; author numerics are not accepted as a substitute |
| T012 | Fig. S1(b), no-dissipation baseline | EQ001, EQ006 | open | passed | `implementation_probe/site_n_no_dissipation_baseline.csv`, `site_n_baseline_check.json` |

## Shared reconstructed parameter card

- **Paper model:** full single-excitation Lindblad equation in dimension N+2.
- **Paper-stated core values:** `g=1.5 meV`, `delta_t=0.5 meV`, cavity
  `gamma_lead=0.5 meV`, resonant coherent Hamiltonian, 15--25 disorder samples.
- **Generated values:** `t=1 meV`, source `|1>`, master seeds starting at 0;
  these are reused across mechanisms.
- **Evidence for reconstruction:** QCLE peak near `g=t`, pump/source schematic,
  initial dark fraction, Table S2 and Fig. 3 endpoint agreement.
- **Missing metadata:** author seeds and exact grids.
- **parameter_match:** `paper_subset` for T001--T010 and T012.
- **artifact_stage:** `exploratory`; strict workflow policy reserves
  `final_reproduction` for `paper_exact` only.
- **generated_data_provenance:** `independent_numerics`.

## Per-target paper parameter cards

### T001 / T008 — size scaling

- Paper: cavity drain, `N=3..96`, `g=1.5`, `delta_t=0.5`, `T=25`, 15
  realizations; pure rescue/dephasing independently optimized; dephasing grid
  extends from max 10 to 100 meV for `N>=48`.
- Generated: same N support points and physical parameters; declared log grids
  plus local refinement, 15 paired realizations.
- Match limitation: exact author N support, grid density, and seeds are absent.

### T002 / T003 — matched-rate dynamics

- Paper: `N=4,16,32` with 15 realizations and `N=6` with 20; time 0--30;
  `gamma_rec=gamma_deph=1`, `g=1.5`, `delta_t=0.5`, `gamma_lead=0.5` meV.
- Generated: same values, source `|1>`, `t=1`, seeds 0--14/19, 301 times.
- Match limitation: reconstructed `t`, source notation, and independent seeds.

### T004 / T010 — finite temperature

- Paper: cavity drain, `N=6/64`, `T=25`, 15 realizations,
  `gamma_deph=0.5`, ratio sweep, `gamma_abs/gamma_rec=exp(-Delta/kBT)`.
- Generated: same physical values; explicit log grids recorded in config.
- Match limitation: most main-Fig. 3 parameters/grid values are inferred from
  the N=64 caption and plotted endpoints rather than printed together.

### T005 / T006 / T012 — site-N and regime sweeps

- Paper: rate axes `1e-3..1e1`, `N=6` baseline at `T=25`, plus the seven
  scenarios printed in Table S1.
- Generated: same scenarios and a declared log grid; 15 paired realizations.
- Match limitation: paper grid density and seeds are absent.
- T012 is independently generated from 15 realizations at zero rescue and zero
  dephasing. It yields `eta=0.5536 +/- 0.0548` versus the paper's `0.65`; the
  absolute error `0.0964` passes the predeclared `0.12` tolerance. The old gap
  was an internal scope omission, not a compute or publication-input limit.

### T007 — coherent detuning

- Paper: detuning `[0,5,10,20]`, `N=6`, matched rate 1, `T=30`, 15 samples.
- Generated: identical listed parameters with reconstructed `t/source/seeds`.

### T009 — site-N manifold dynamics

- Paper: `N=6`, `g=1.5`, `delta_t=0.5`, site-N drain, rescue 0 or 0.05.
- Generated: same printed values; remaining baseline values follow the shared
  configuration and are declared in config.

### T011 — QCLE benchmark

- Paper: Fig. S5 contains phenomenological and QCLE time traces plus two
  coupling-dependent curves.
- Missing input: chemical potentials, temperature, lead-coupling matrix,
  initial state, and dimensional conventions required for a like-for-like run.
- Boundary: all four items remain eligible but uncovered. Original pixels and
  author numerical implementation cannot fill the scientific input gap.
