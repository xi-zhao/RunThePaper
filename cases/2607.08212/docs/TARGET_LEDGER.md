# Target Ledger

Every numerical target has an explicit exact, subset, proxy, or blocked scope.

| Target ID | Paper item | Scope | Status | Data / check | Notes |
| --- | --- | --- | --- | --- | --- |
| ALGEBRA_CORE | Eqs. (4)-(9), (21)-(22) | exact method | reproduced | `mobius_validation_summary.csv`, `feature_reproduction_result.json` | 256 tables + 8 polarities, zero failures |
| FIG3C_NATIVE | Fig. 3(c) | paper subset | reproduced | `fig3_gate_accounting.csv` | 19 gates and depth 12 exact; stream transcribed |
| FIG3A_ZAP | Fig. 3(a) | paper subset | partial | `fig3_gate_accounting.csv` | 163 gates exact; depth 121 vs 128 |
| FIG3B_ZX | Fig. 3(b) | exact | blocked | — | source circuit and ZX configuration absent |
| ROUTING_PROXY | Figs. 4/5/8 | proxy model | algorithmically_consistent | routing CSV/JSON + three figures | eight families, 320 rows; six many-body wins; controls equal |
| ROUTING_PROXY_SCALING | Fig. 6 | proxy model | algorithmically_consistent | scaling CSV/JSON/figure | 3 families, 20-100 qubits, local M4 timings |
| ROUTING_PROXY_SENSITIVITY | Fig. 7 | proxy model | partial | sensitivity CSV/JSON/figure | 5,043 rows; degree structure passes; no break-even contours |
| FIG4_FIDELITY_EXACT | Fig. 4(a-h) | exact routed | blocked | proxy available separately | author ensemble and route state absent |
| FIG5_MOVES_EXACT | Fig. 5(a-h) | exact routed | blocked | proxy available separately | author ensemble and geometry absent |
| FIG6_RUNTIME_EXACT | Fig. 6(a-f) | exact routed | blocked | proxy available separately | author compile environment absent |
| FIG7_SENSITIVITY_EXACT | Fig. 7(a-f) | exact routed | blocked | partial proxy available | fixed author/ZAP/ZX routes absent |
| FIG8_STAGES_EXACT | Fig. 8(a-h) | exact routed | blocked | proxy available separately | author schedule/route ensemble absent |

Exact and proxy targets are intentionally separate: completion of a proxy never
changes an exact target to reproduced.
