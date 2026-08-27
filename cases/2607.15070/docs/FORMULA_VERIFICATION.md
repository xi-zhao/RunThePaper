# Formula Verification

## Gate Summary

| Formula | Role | Gate | Reason |
| --- | --- | --- | --- |
| EQC001 | radial oscillator spectrum | open / trusted | direct symbolic reduction and ground-state substitution |
| EQC002 | Landau-like energy integral | open / trusted | source-checked and independently transformed |
| EQC003 | additional energy integral | open / trusted | source-checked with dimensional correction in printed Eq. (27) |
| EQC004 | positive Bessel-series representation | open / trusted | independently derived and numerically cross-checked |
| EQC005 | weak-coupling limits | open / trusted | analytic limit plus numerical comparison |
| EQC006 | strong-coupling asymptotic | open / trusted | Bessel asymptotic plus numerical comparison |
| EQC007 | total-to-Landau ratio | open / trusted | algebraic identity checked on every data row |

All seven cards pass `source_and_symbolic` policy. The machine-readable result
is `outputs/checks/formula_verification.json`.

## Verified Source Discrepancies

| Paper location | Independent result | Numerical consequence |
| --- | --- | --- |
| Eq. (11) | \(\lambda=2\alpha(2n+|l|+1)\) | paper spectrum is lower by a factor two |
| Eqs. (18)-(19) to Eq. (26) | second sum's printed lower index conflicts with the closed denominator | the plotted denominator corresponds to the zero-based series |
| Eq. (27), first dimensionless line | denominator requires \(\alpha_0\tau^2\) | code uses the dimensionless coupling |
| Eq. (36) | leading correction uses \(m_0^3K_3(2jm_0)/j^3\) | corrected weak-coupling approximation has 2.0% error at the diagnostic point, versus 59.5% for printed \(K_2\) |
| Eq. (31), final line | exponent is \(-2j\sqrt{m_0^2+f\alpha_0}\) | corrected leading term has 3.27% error at \(\alpha_0=30\), while the printed form is effectively zero |

## Authorization

EQC002 and EQC003 authorize reproduction of the displayed integrals as
conditional numerical objects. They do not override EQC001 or imply that the
paper's preceding spectrum follows from its action.
