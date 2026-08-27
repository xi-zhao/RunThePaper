# Formula Verification

Machine-readable result: `outputs/checks/formula_verification.json`.

## Gate Summary

| Formula | Role | Gate | Reason |
| --- | --- | --- | --- |
| EQ001 | delayed-erasure information model | open | source equation plus no-loss limiting case |
| EQ002 | loss fraction | open | source definition and pure-noise endpoints |
| EQ003 | Error Model A | open | symbolic normalization and nonnegative probabilities |
| EQ004 | phase boundary/lifecycle fit | open | source trace and axis endpoints |
| EQ005 | effective distance | open | source trace and d=7 endpoint check |
| EQ006 | lifecycle counts | open | d=3 gate count and large-d limit |
| EQ007 | algorithm counts | open | Appendix-G gate-by-gate counts independently rederived |
| EQ008 | movement error | open | zero/monotonic limiting cases |
| EQ009 | Error Model B normalization | open | symbolic normalization and source-definition contradiction audit |
| EQ010 | maximum logical-error bound | open | endpoint and monotonic limiting cases |

Result: 10 cards total, 10 numeric gates open, 0 closed. `DERIVATION.md`
was generated from the cards and is not hand-edited.

## Deliberately Ungated Paper-Scale Quantities

Threshold crossings, effective-distance fits, logical-error Monte Carlo curves,
and space-time extrapolations are not represented as closed equations with
invented parameters. The bounded clean-room campaign attempted these targets
without author code, pixels, or numerical arrays and reached the current
system-capability boundary; they are therefore finalized as
`attempted_not_reproduced`, not left pending on author materials.
