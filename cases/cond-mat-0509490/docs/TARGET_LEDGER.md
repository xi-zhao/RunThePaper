# Target Ledger

| Target ID | Paper item | Type | Formula dependencies | Formula gate | Status | Data output | Figure output | Check output | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T001 | Eqs. (1)-(14) | quantitative claim | EQ001 | verified | physically_consistent | `outputs/data/dispersion.csv` | auxiliary validation board | `outputs/checks/science_checks.json` | Critical dispersion and half-integer grid. |
| T002 | Eqs. (15)-(23) | quantitative claim | EQ002-EQ004 | verified | physically_consistent | `outputs/data/excitation_probability.csv` | auxiliary validation board | `outputs/checks/science_checks.json` | Direct ODE versus LZ formula. |
| T003 | Eqs. (24)-(25) | quantitative claim | EQ004-EQ005 | verified | physically_consistent | `outputs/data/defect_density.csv` | auxiliary validation board | `outputs/checks/science_checks.json` | Exponent `-1/2` and exact prefactor. |
| T004 | Eqs. (26)-(27) | quantitative claim | EQ004, EQ006 | verified | physically_consistent | `outputs/data/ground_state_probability.csv` | auxiliary validation board | `outputs/checks/science_checks.json` | Product probability and `N^2` collapse. |
| T005 | Eqs. (28)-(29) | quantitative claim | EQ002-EQ005, EQ007 | verified | physically_consistent | `outputs/data/reverse_quench_density.csv`, `outputs/data/reverse_quench_modes.csv` | auxiliary validation board | `outputs/checks/science_checks.json` | Forward and reverse BdG sweeps are both executed; equality is not a copied-array identity. |

The generated board `outputs/figures/scientific_claim_validation.png` is not a paper-figure reproduction.
