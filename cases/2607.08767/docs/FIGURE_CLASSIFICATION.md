# Figure Classification

| Paper item | Class | Decision | Reason |
| --- | --- | --- | --- |
| Fig. 1–4 | `schematic_context` | excluded | platform and algorithm diagrams |
| Table I–II | `algorithm_trace` | excluded | qualitative capability taxonomies |
| Table III | `numeric_reproduction` | `T_TABLE3` exact | fully determined by Eq. (12) |
| Fig. 5(a) | `numeric_reproduction` | `F5A_PROXY` exploratory | independent proxy covers direction, not paper parity |
| Fig. 5(b) | `numeric_reproduction` | `T_FIG5B` uncovered | independent leakage-aware QEC method not implemented |
| Fig. 6(a) | `numeric_reproduction` | `T_FIG6A` uncovered | transmon distance-three scan not implemented |
| Fig. 6(b) | `numeric_reproduction` | `T_FIG6B` uncovered | larger-code scan and convergence not implemented |
| Fig. 7 | `numeric_reproduction` | `T_FIG7` uncovered | finite-size threshold pipeline not implemented |
| Fig. 8 | `numeric_reproduction` | `T_FIG8` uncovered | Rydberg threshold surface not implemented; exact rays unprinted |
| Fig. 9 | `schematic_context` | excluded | ion-sector diagram |
| Fig. 10 | `numeric_reproduction` | `T_FIG10` exact | fully determined by Eqs. (20)–(21) |
| Fig. 11 | `numeric_reproduction` | `T_FIG11` uncovered | sector-history QEC threshold pipeline not implemented |

Machine-readable coverage and blocker details are authoritative in
`figure_coverage.json`.
