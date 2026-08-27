# Target Ledger

| Target | Paper item | Parameter match | Status | Data | Figure/check |
| --- | --- | --- | --- | --- | --- |
| T001 | Fig. 2 | `paper_subset` | `evidence_compared`, exploratory | `outputs/data/fig2_state_thresholds.csv` | `fig2_state_thresholds.png/json` |
| T002 | Fig. 3 | `paper_exact` | `evidence_compared` | `outputs/data/fig3_*.csv` | `fig3_mechanism.png/json` |
| T003 | Fig. 4 | `paper_subset` | `evidence_compared`, exploratory | `outputs/data/fig4*.csv` | `fig4_phase_response.png`, panel checks |
| T004 | Fig. S1 | `paper_subset` | `evidence_compared`, exploratory | `outputs/data/figs1_density_profiles.csv` | `figs1_density_profiles.png/json` |
| D001 | finite size/trap | diagnostic | `passed` | `outputs/data/finite_size_and_trap.csv` | `finite_size_and_trap.json` |

All numerical targets have structured data, machine checks, formula dependencies, and source-vs-reproduction boards under `docs/comparisons/`.
