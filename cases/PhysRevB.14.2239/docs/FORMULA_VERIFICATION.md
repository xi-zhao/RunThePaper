# Formula Verification

| Formula | Role | Gate | Evidence |
| --- | --- | --- | --- |
| EQ001 | Harper operator | verified | Hermiticity tests and direct residuals |
| EQ002 | Transfer matrix | verified | band-edge `|Tr Q|=4` cross-check |
| EQ003 | q bands | verified | q bands for independent rational fluxes |
| EQ004 | Symmetries/bound | verified | residuals below `1e-14`; exact `[-4,4]` endpoints |
| EQ005 | Recursive maps | verified | analytic endpoint maps and resolved subcells |
| EQ006 | Field union | verified | printed window and band-count bound |
| EQ007 | Wavefunction reorder | verified | exact printed order, energies and residuals |

Machine-readable cards live in `EQUATION_CARDS.json`; the Harness formula gate
is the authority for whether targets may run.
