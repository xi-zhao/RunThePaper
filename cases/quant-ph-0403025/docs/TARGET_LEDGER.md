# Target Ledger

| Target | Paper item | Formula dependencies | Status | Planned data | Planned figure | Acceptance |
| --- | --- | --- | --- | --- | --- | --- |
| T001 | Main Fig. 2 upper | EQ001-EQ005, EQ008 | review_pending | `outputs/data/t_type_curves.csv` | `outputs/figures/main_fig2a_reproduction.png` | closed form equals 32-state projector enumeration; fixed point, quadratic limit and 99.6531 scientific pixel score pass |
| T002 | Main Fig. 2 lower | EQ002-EQ004, EQ008 | review_pending | `outputs/data/t_type_curves.csv` | `outputs/figures/main_fig2b_reproduction.png` | closed form equals projector enumeration; endpoints, monotonicity and 99.7807 scientific pixel score pass |
| T003 | Main Fig. 3 | EQ001, EQ006-EQ009 | review_pending | `outputs/data/h_type_curves.csv` | `outputs/figures/main_fig3_reproduction.png` | closed form equals Reed-Muller enumeration; fixed point, cubic limit and 99.6574 scientific pixel score pass |
| T004 | Sec. VII `n=11,17` simulation trend | generic stabilizer projector and signed Pauli weight enumerators | code_ready_input_blocked | `outputs/data/gf4_threshold_campaign.json` | not applicable until exact codes exist | general evaluator, configuration, run contract and five-qubit known-answer test pass; paper comparison requires the unpublished code generators/search definition |

## Deferred quantitative claim

The Section VII n=11/17 code-search statement now has a complete generic
execution channel, but the paper-specific run remains blocked: the manuscript
omits the code generators/search definition and every threshold result.
`GF4_CODE_INPUT_CONTRACT.md` defines the exact missing input, and
`NUMERICAL_CLAIM_AUDIT.md` records the direct and root cause.
