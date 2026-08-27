# Target Ledger

| Target | Paper item | Formula | Parameter status | Result | Evidence |
| --- | --- | --- | --- | --- | --- |
| `F5A_PROXY` | Fig. 5(a) | `PLAQ009`, `PLAQ010` | `proxy_model` | exploratory; public direction passes, paper parity not testable | `outputs/checks/fig5a_proxy_result.json` |
| `T_TABLE3` | Table III | `PLAQ012` | `paper_exact` | all printed values reproduced; header semantics inconsistent | `outputs/checks/public_exact_targets.json#targets.T_TABLE3` |
| `T_FIG10` | Fig. 10 | `PLAQ020` | `paper_exact` | all 25 entries pass within `1e-4` | `outputs/checks/public_exact_targets.json#targets.T_FIG10` |
| `T_FIG5B` | Fig. 5(b) | `PLAQ012` | not run | uncovered: no independent leakage-aware QEC runner | next: `outputs/checks/t_fig5b_leakage_qec.json` |
| `T_FIG6A` | Fig. 6(a) | `PLAQ015_016` | not run | uncovered: no transmon distance-three QEC scan | next: `outputs/checks/t_fig6a_transmon_d3.json` |
| `T_FIG6B` | Fig. 6(b) | `PLAQ015_016` | not run | uncovered: no distance-nine scan/convergence | next: `outputs/checks/t_fig6b_transmon_d9.json` |
| `T_FIG7` | Fig. 7 | `PLAQ015_016` | not run | uncovered: no finite-size threshold pipeline | next: `outputs/checks/t_fig7_threshold_scaling.json` |
| `T_FIG8` | Fig. 8 | `PLAQ018_019` | not run | uncovered: no Rydberg threshold surface; exact rays unprinted | next: `outputs/checks/t_fig8_neutral_atom_surface.json` |
| `T_FIG11` | Fig. 11 | `PLAQ020`, `PLAQ022` | not run | uncovered: no non-stationary sector-history QEC fit | next: `outputs/checks/t_fig11_ion_threshold.json` |

All nine eligible numerical items now have an explicit target contract. The six
uncovered items count as zero in reproduction degree but are excluded from the
mean fidelity of covered items. Their direct cause, root cause, code-fault
assessment, affected scope, and next discriminating test are recorded in the
machine scorecard; no unavailable author array is silently treated as a
substitute for independent scientific computation.
