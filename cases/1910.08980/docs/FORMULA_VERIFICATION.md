# Formula Verification

| Card | Numerical role | Gate | Independent check |
| --- | --- | --- | --- |
| EQ001 | Signed cubic Ising ensemble | verified | Degree, edge-count, and coupling-domain invariants. |
| EQ002 | QAOA state and ratio | verified | Analytic beta maximum; exact denominator checked against brute force. |
| EQ003 | Level-1 edge correlations | verified | Direct four-qubit statevector parity to `2e-12`. |
| EQ004 | RQAOA contractions | verified | Original/reduced energy identity and exact cutoff sizes. |
| EQ005 | Exact normalization | verified | XOR algebra and zero-gap MILP certificate. |

The only unresolved information is instance identity, not a formula: the paper
does not disclose the random samples or seeds behind its bars.
