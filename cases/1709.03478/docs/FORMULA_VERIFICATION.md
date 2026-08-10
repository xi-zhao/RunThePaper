# Formula Verification

The executable formula gate passed all nine cards.  Its machine-readable result
is `outputs/checks/formula_verification.json`; the reader-facing derivation is
`DERIVATION.md`.

| Formula | Role | Gate | Evidence / qualification |
| --- | --- | --- | --- |
| EQC001 | continuum Hamiltonian | open, verified | Main Eq. (1), unit conversion checked. |
| EQC002 | finite-difference operator | open, verified | Independent second-order stencil and symmetry test. |
| EQC003 | (J) and (	au=\hbar/J) | open, verified | (J) independently integrated from the primary Bloch band. |
| EQC004 | CDW imbalance | open, verified | Paper definition and normalization check. |
| EQC005 | center-third edge density | open, verified | Paper definition; normalized by the projected (N_c(0)). |
| EQC006 | spectral / diagonal-ensemble propagation | open, verified | Spectral theorem and a direct diagonal-only unit test. |
| EQC007 | FWHM and RMS | open, reconstructed | Uses the standard square-root RMS because the supplement's printed right side is dimensionally inconsistent. |
| EQC008 | tube average | open, reconstructed | Deterministic two-node proxy; the author tube histogram is unavailable. |
| EQC009 | 0.015 threshold | open, source-only | Fig. 3 caption; linear interpolation only between generated samples. |

No digitized curve, author numerical array, or image pixel contributes to a
formula or numerical input.  Reconstructed EQC007–008 cap the affected targets
below a paper-exact claim.
