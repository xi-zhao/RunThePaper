# Formula Verification

Machine-readable gate: `outputs/checks/formula_verification.json`.

## Gate Summary

All eight cards are numerically open; no target ran before this gate passed.

| Formula | Role | Derivation status | Numeric gate | Main check |
| --- | --- | --- | --- | --- |
| EQ001 | finite AA Hamiltonian | verified | open | Hermiticity and clean-chain spectrum |
| EQ002 | GAA corrections | verified | open | source parameters and Hermiticity |
| EQ003 | steady cavity amplitude | verified | open | zero-pump and positivity limits |
| EQ004 | susceptibility channels | verified | open | positivity and completeness sum rule |
| EQ005 | critical pump | verified | open | direct Eq. (7), sine-basis, analytic-limit and finite-size checks |
| EQ006 | localized self-channel | verified | open | IPR classifier and deep-localized limit |
| EQ007 | momentum/channel indices | verified | open | Parseval scale and indices `151,137,27` |
| EQ008 | nonlinear mean field | reconstructed | open | zero-field limit and normalization |

## Disclosed Formula Ambiguities

- EQ005: the published one-factor Eq. (7) is the sole scientific convention. Its stable disagreement with Fig. 3(a) and Fig. 4(b) is preserved for fresh review; the factor-two branch is a post-generation falsification hypothesis only.
- EQ008/EQ003: the literal published one-factor cavity denominator also reproduces the nonlinear Fig. 4(a) onset and passes a second solver schedule.
- S1: the equations are explicit, but pump samples and solver initialization are missing.

The Fig. 3(a)/Fig. 4(b) discrepancy is not hidden as an implementation default or tuned away. Fig. S1 remains externally blocked by unpublished inputs.
