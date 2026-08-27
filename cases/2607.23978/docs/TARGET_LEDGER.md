# Target Ledger

| Target | Paper item | Formula gate | Scientific status | Pixel status | Outputs | Remaining limitation |
| --- | --- | --- | --- | --- | --- | --- |
| T001 | Fig. 2(c-d), optimal theory | verified | passed | high fidelity, 90.11 | `fig2_optimal.npz`, `fig2_optimal.png`, `fig2_science.json` | adjoint orientation inferred from paper's own baseline |
| T002 | Fig. 2(e-f), optimal series | verified | passed | not comparable | `fig2_expectations.npz`, `fig2_expectations.png`, `fig2_expectations_science.json` | non-optimal series and experiment share the source panels |
| T003 | Fig. 3(a), theory | verified | passed | accepted, 81.75 | `fig3a.npz`, `fig3a.png`, `fig3a_ordering_audit.png`, `fig3a_science.json` | printed Eq. (3)+(5) conflicts with plotted claim |
| T004 | Fig. 3(b-c), theory | verified | passed | accepted, 89.62 | `fig3bc.npz`, `fig3bc.png`, `fig3bc_science.json` | finite `Delta gamma` absent; target remains paper subset |

## Blocked numerical lanes

- Fig. 2(a-b): `A1/A2` matrices are absent from the public source.
- Fig. 2(e-f), non-optimal series: same blocker.
- Complete-POVM CFI: explicit POVM elements are absent.

## Excluded context

- Fig. 1 experimental apparatus.
- All measured symbols and error bars.
