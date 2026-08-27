# Figure Classification

Only scientific numerical content becomes executable. Every numerical panel and table
is listed separately so an inset cannot disappear behind a parent-figure status.

| Paper item | Class | Reproduce? | Reason |
| --- | --- | --- | --- |
| Main Fig. 1 | `schematic_context` | No | Conceptual tensor-network/transfer-matrix drawing; it contains no computed observable. |
| Main Fig. 2 main axes | `numeric_reproduction` | Yes, T001 | Disorder-averaged spectral form factor from the Floquet model. |
| Main Fig. 2 inset | `numeric_reproduction` | Yes, T002 | Distinct short-time scientific region; generated from the same independently computed time series. |
| Main Fig. 3 left | `numeric_reproduction` | Yes, T003 | Transfer-matrix gap for multiple times at zero mean field. |
| Main Fig. 3 right | `numeric_reproduction` | Yes, T004 | Transfer-matrix gap for multiple mean fields at fixed time. |
| Main Table I | `numeric_reproduction` | Yes, T005 | Numerical/algebraic multiplicities of unit-modulus transfer eigenvalues. |

The supplemental material contains derivations but no further numbered figures or
tables. Original `Fig2_9490avgs.pdf` and `Gapv6.pdf` are comparison-only assets; no
curve points are digitized or passed to the numerical runner.
