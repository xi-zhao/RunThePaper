# Formula Verification

All eleven formula cards passed both source tracing and an independent
symbolic, normalization, limiting-case, or numerical check before numerical
execution was allowed.

| Formula | Role | Independent check | Gate |
| --- | --- | --- | --- |
| `EQC001` | GKSL generator | trace preservation and analytic damping | open |
| `EQC002` | Choi reshuffling | identity Choi and program normalization | open |
| `EQC003` | SWAP-dephasing factorization | commutation, idempotence, endpoints | open |
| `EQC004` | exact Fig. 2 overlap | Bell-basis derivation | open |
| `EQC005` | fixed HPTP processor | Hermiticity, trace, programmed action | open |
| `EQC006` | signed sampling | trace-weight identity and unbiased expectation | open |
| `EQC007` | cost versus overhead | definition, axis, and script objective | open |
| `EQC008` | programming-cost SDP | trace and epsilon-LMI reduction | open |
| `EQC009` | program contraction | explicit index expansion | open |
| `EQC010` | HP diamond norm | known identity and Pauli-channel norms | open |
| `EQC011` | Fig. 3 models and grids | analytic channel and loop audit | open |

## Source findings

The Supplemental displayed loss-term transpose placement conflicts with its
own identity
\(\operatorname{vec}(ABC)=(A\otimes C^T)\operatorname{vec}(B)\). Direct
algebra supplies the implemented form. The target models have real diagonal
\(L^\dagger L\), so the displayed inconsistency does not change either
reproduced curve.

The Fig. 3 scripts allocate the \(t=10\) endpoint but iterate only through
\(t=9.99\). The source-exact loop is preserved and \(t=10\) is separately
verified for every recovered solution.
