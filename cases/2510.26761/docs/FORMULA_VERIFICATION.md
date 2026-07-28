# Formula Verification

Machine-readable result:
`outputs/checks/formula_verification.json`.

## Gate Summary

- Cards: 14
- Numeric gates open: 14
- Trusted cards: 13
- Reconstructed cards: 1 (`EQC013`)
- Closed cards: 0
- Gate result: `passed`

| Formula group | Role | Gate | Reason |
| --- | --- | --- | --- |
| `EQC001`--`EQC002` | conventions and collective coordinates | trusted | vacuum normalization and canonical transformation checked |
| `EQC003`--`EQC006` | two GME theorems and finite-region criterion | trusted | source traced and independently reduced to the \(M=3\) forms |
| `EQC007`--`EQC009` | W-state Wigner slice and disk threshold | trusted | collective-mode derivation, analytic integration, and root finding agree |
| `EQC010`--`EQC011` | finite characteristic-function witness | trusted | Hermiticity, point count, and eigenspectrum independently checked |
| `EQC012` | illustrative collective-Fock state | trusted | creation-operator expansion and unit norm checked |
| `EQC013` | illustrative slice bound | exploratory | the state-derived formula is verified, while the source prints an incompatible numerator |
| `EQC014` | reduced state and smoothed origin | trusted | trace, Laguerre integral, and \(-7/(16\pi)\) checked |

## Source Inconsistency

The source prints

\[
\mathcal N_{2D}^{\rm GME}=(75\sqrt2+56)/600.
\]

Its displayed normalized state has relative parity \(-13/25\), which gives

\[
\int W\,d^2\alpha=-52/(75\pi^2),\qquad
\mathcal N_{2D}^{\rm GME}=(75\sqrt2+52)/600.
\]

The numerical lane remains open only because this discrepancy is explicit:
target `T001` and validation `V003` are restricted to `exploratory`, preserve
both values, and evaluate the state-derived conclusion separately from the
source-printed inequality.
