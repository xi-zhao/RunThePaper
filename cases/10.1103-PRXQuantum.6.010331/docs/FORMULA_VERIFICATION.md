# Formula Verification

Machine-readable result: `outputs/checks/formula_verification.json`.

## Gate Summary

| Formula | Role | Gate | Numerical consequence |
| --- | --- | --- | --- |
| EQ001 | Infinite-blockade ideal Hamiltonian | open / verified | May feed the direct diagnostic. |
| EQ002 | Generic cited sinusoidal pulse | open / reconstructed | May feed only `D001`; cannot establish paper-exact Fig. 15 data. |
| EQ003 | Haar-averaged connected response | open / verified | May feed the direct diagnostic. |
| EQ004 | Frequency and intensity noise operators | open / verified | May feed the direct diagnostic. |
| EQ005 | Universal Rabi-frequency scaling | open / verified | Feeds final target `T002`. |
| EQ006 | Four Appendix-L analytic response fits | open / source_only | Feeds final targets `T001` and `T002`. |

All six cards pass their declared source, symbolic, dimensional, or limiting
checks. The distinction between `verified`, `source_only`, and `reconstructed`
is preserved in downstream target metadata.

## Parameter Gate

The formula gate alone cannot certify that a named pulse is the exact trajectory
behind a figure. Direct integration with EQ001-EQ004 gives a high-fidelity CZ
and converges numerically, yet differs from Appendix L. The parameter identity
is therefore closed for a paper-exact direct reproduction and open only for the
reconstructed diagnostic.

Rebuild with:

```bash
python PRAgent-workflow/scripts/check_formula_gate.py case/10.1103-PRXQuantum.6.010331 --write
python PRAgent-workflow/scripts/render_derivation.py case/10.1103-PRXQuantum.6.010331
```
