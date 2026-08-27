# Target Ledger

| Target ID | Paper item | Observable and visible series | Formula dependencies | Gate | Status before execution | Planned generated data / figure / check |
| --- | --- | --- | --- | --- | --- | --- |
| T-FIG001A | Fig. 1(a) | normalized baseline \(R_0(y)\) | EQC001, EQC002 | verified | `spec_ready` | `fig001a_baseline.csv` / `fig001a_baseline.png` / `fig001a_science.json` |
| T-FIG001B | Fig. 1(b) | separately normalized \(g_t(y)\), \(g_f(y)\) | EQC001-EQC003 | verified | `spec_ready` | `fig001b_scores.csv` / `fig001b_scores.png` / `fig001b_science.json` |
| T-FIG001C | Fig. 1(c) | optimized \(w_t,w_f\), toy \(h_1,h_2\) | EQC002-EQC005, EQC007 | verified | `spec_ready` | `fig001c_codes.csv` / `fig001c_codes.png` / `fig001c_science.json` |
| T-FIG001D | Fig. 1(d) | optimized/toy principal retention bars | EQC003-EQC007 | verified | `spec_ready` | `fig001d_retention.csv` / `fig001d_retention.png` / `fig001d_science.json` |
| T-FIGS001 | Fig. S1 | \(\rho(a)=F_{ff}/F_{tt}\) at five paper widths | EQC001-EQC004, EQC008 | verified | `spec_ready` | `figs001_width_scan.csv` / `figs001_width_scan.png` / `figs001_science.json` |

Every final command will be authorized separately with
`check_target_readiness.py` and executed through `run_target.py` with
`--stage final_reproduction`. The case runner accepts exactly one explicit
target and checks `PRAGENT_GUARDED_TARGET_ID`; it cannot mutate another
target's outputs.
