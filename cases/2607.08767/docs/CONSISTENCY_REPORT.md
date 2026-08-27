# Consistency Report

| Target | Formula | Numeric | Scope / attribution |
| --- | --- | --- | --- |
| `F5A_PROXY` | passed | public Clifford branch and direction pass; paper coherent value differs | `proxy_model`; unpublished commercial pipeline, not a reproduction or paper failure |
| `T_TABLE3` | passed | every printed weight passes | paper-exact; header appears to call joint weights conditional probabilities |
| `T_FIG10` | passed | 25/25 cells pass, max error `5.29e-5` | paper-exact |

## Source Discrepancy

For each Table III transition branch, the printed `p_err|tr` values sum to
`p_tr`, whereas conditional probabilities must sum to one. Two independent
checks support this: direct blockwise Pauli expansion and normalization after
division by `p_tr`. The finding is classified `source_figure_artifact` pending
fresh review; no physics parameter or generated array was changed to produce it.

## Provenance

- author code: not used
- author numerical arrays: not used
- source pixels as numerical inputs: prohibited and not used
- exact numerical run: isolated and attested
- proxy mismatch: `missing_parameters`, not `model_mismatch`
