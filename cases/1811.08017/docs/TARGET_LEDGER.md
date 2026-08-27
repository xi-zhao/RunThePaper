# Target Ledger

T001 and T002 remain the attested aggregate target IDs. Each row below is a
separate numerical panel contract, all of which are checked by
`outputs/checks/panel_target_acceptance.json`.

| Target / panel | Paper item | Paper parameters | Formula dependencies | Implementation | Execution | Evidence | Paper-review boundary |
| --- | --- | --- | --- | --- | --- | --- | --- |
| T001 / propane | Main Fig. 2 propane | `epsilon=10^-3`, `t=10^2…10^8`, `(lambda,Lambda,L)=(426.61,6.58466,241582)` | EQ001–EQ004 | `fig2_paper_exact` | accepted run `1811.08017-paper-exact-v2` | `outputs/data/fig2_gate_counts.csv`; `outputs/checks/panel_target_acceptance.json` | `591x` prose conflict remains `inconclusive`; no paper-error label |
| T001 / carbon dioxide | Main Fig. 2 CO2 | `epsilon=10^-3`, `t=10^2…10^8`, `(608.414,10.3658,113959)` | EQ001–EQ004 | `fig2_paper_exact` | accepted run `1811.08017-paper-exact-v2` | same dataset and panel check | paper assessment is pending fresh protocol-v2 review |
| T001 / ethane | Main Fig. 2 ethane | `epsilon=10^-3`, `t=10^2…10^8`, `(768.138,4.07041,467403)` | EQ001–EQ004 | `fig2_paper_exact` | accepted run `1811.08017-paper-exact-v2` | same dataset and panel check | paper assessment is pending fresh protocol-v2 review |
| T002 / propane | Main Fig. 4 propane | `delta_E=10^-4`, `P_f=10^-1…10^-5`, printed molecule tuple | EQ001, EQ005, EQ006 | `fig4_paper_exact` | accepted run `1811.08017-paper-exact-v2` | `outputs/data/fig4_phase_estimation_counts.csv`; panel check | paper assessment is pending fresh protocol-v2 review |
| T002 / carbon dioxide | Main Fig. 4 CO2 | same figure range and printed molecule tuple | EQ001, EQ005, EQ006 | `fig4_paper_exact` | accepted run `1811.08017-paper-exact-v2` | same dataset and panel check | paper assessment is pending fresh protocol-v2 review |
| T002 / ethane | Main Fig. 4 ethane | same figure range and printed molecule tuple | EQ001, EQ005, EQ006 | `fig4_paper_exact` | accepted run `1811.08017-paper-exact-v2` | same dataset and panel check | paper assessment is pending fresh protocol-v2 review |

Main Fig. 1, Main Fig. 3, and Table I are recorded explicitly in
`figure_coverage.json`; none contains an evaluated numerical series.
