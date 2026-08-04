# Formula Verification

Machine-readable evidence: `outputs/checks/formula_verification.json`.

## Gate Summary

| Formula | Role | Gate | Verification |
| --- | --- | --- | --- |
| EQ001 | Multinomial LLR, degrees of freedom, p-value | `open / trusted` | Source and derivation verified; worked examples reproduce ≈0.1% and 92% p-values. |
| EQ002 | Hochberg pseudo-threshold | `open / trusted` | Source and algorithm verified against all reported ICT counts. |
| EQ003 | Aggregate LLR and signed `N_sigma` | `open / trusted` | All ten pairwise and the joint Figure 2 statistics match. |
| EQ004 | Observed JSD | `open / trusted` | Entropy and LLR definitions agree to `2.3e-16`. |
| EQ005 | TVD, SSTVD, maximum SSTVD | `open / trusted` | All seven Figure 3 maxima match exactly. |

## Closed Or Unclear Formulas

None. All five formulas feeding numerical targets are open, trusted, and have
durable source, derivation, code, and numerical evidence.

## Source-Figure Finding

The released Figure 2 notebook divides the two-pool LLR by
`2*N_per_context`, whereas Eq. 15 uses `2*N_total`. For equal 100-shot pools
this creates an exact factor of two in the plotted ordinate. The reproduction
stores the standard JSD and the source-compatible ordinate separately; no
p-value, detection, ordering, or physical conclusion changes.
