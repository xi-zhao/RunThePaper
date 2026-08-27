# Formula Verification

`EQUATION_CARDS.json` is the machine-readable formula map. All seven numeric
cards are open and source/derivation verified:

| Card | Scientific role |
| --- | --- |
| MSC001 | magic states as PSC eigenstates |
| MSC002 | controlled-H Pauli propagation |
| MSC003 | Pauli-rank fidelity expansion |
| MSC004 | benchmark acceptance estimator |
| MSC005 | logical-state infidelity estimator |
| MSC006 | inverse-square-root sampling precision |
| MSC007 | runtime claim and environment boundary |

The authoritative result is `outputs/checks/formula_verification.json`. Formula
verification validates the observable definitions and implementation links; it
does not override the T001/T002 numerical mismatch or the T003 external
benchmark boundary.
