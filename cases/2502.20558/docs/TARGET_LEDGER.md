# Target Ledger

| Target ID | Paper item | Type | Formula dependencies | Formula gate | Status | Data output | Figure output | Check output | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T001 | Fig. 2(b) | independent proxy Monte Carlo | EQ001, EQ002 | passed | physically_consistent | `outputs/data/fig2b_proxy.csv` | `outputs/figures/fig2b_proxy.png` | `outputs/checks/fig2b_proxy.json` | Paper d=5, p_loss=1%, and rounds 2/4/6/8; repetition-code analogue, `proxy_model`, exploratory. |
| T002 | Fig. 4(b) | analytic relation | EQ004 | passed | reproduced | `outputs/data/fig4b_lifecycle_threshold.csv` | `outputs/figures/fig4b_lifecycle_threshold.png` | `outputs/checks/fig4b_lifecycle_threshold.json` | Printed fit `7/lifecycle^(1/3)` at paper domain; the separate simulation series were attempted under T009 but not reproduced. |
| T003 | Fig. 6(b) | exact combinatorial count | EQ007 | passed | reproduced | `outputs/data/fig6b_algorithm_lifecycles.csv` | `outputs/figures/fig6b_algorithm_lifecycles.png` | `outputs/checks/fig6b_algorithm_lifecycles.json` | `paper_exact`, final reproduction. |
| T004 | Fig. 14(c) | exact/reconstructed circuit count | EQ006 | passed | reproduced | `outputs/data/fig14c_swap_lifecycles.csv` | `outputs/figures/fig14c_swap_lifecycles.png` | `outputs/checks/fig14c_swap_lifecycles.json` | Both atomic all-qubit invariant curves pass; unpublished boundary convention remains a disclosed paper-subset caveat. |
| T005 | Fig. 16(a) | exact/reconstructed circuit count | EQ006 | passed | reproduced | `outputs/data/fig16a_lifecycle_comparison.csv` | `outputs/figures/fig16a_lifecycle_comparison.png` | `outputs/checks/fig16a_lifecycle_comparison.json` | All four atomic curves assigned to T005 pass; the separate SWAP role curves are assigned to T016. |
| T006 | Table I analytic rows | exact formulas/table contract | EQ006, EQ007 | passed | reproduced | `outputs/data/table_i_analytic_rows.csv` | n/a | `outputs/checks/table_i_analytic_rows.json` | Lifecycle and overhead rows exact; numerical performance rows map to finalized T019/T020 attempts. |

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

The complete machine ledger contains 29 targets. Its final target projection is
13 `reproduced`, 1 `externally_blocked`, 15 `attempted_not_reproduced`, and 0
`pending`. T007-T020 use the formula/method-driven clean-room campaign in
`outputs/data/implementation_validation/`; every output is exploratory and
explicitly carries `scientific_acceptance=not_claimed`. T021-T029 use the
analytic claim suite. The authoritative per-item projection lives in
`outputs/checks/authoritative_reproduction_state.json`.
