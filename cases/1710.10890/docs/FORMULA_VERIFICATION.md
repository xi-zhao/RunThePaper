# Formula Verification

All nine formula cards are open for numerical use. “Open” means the cited
source, derivation trace, implementation reference, units, and checks are
present; it does not imply that every paper parameter is available.

Machine-readable result: `outputs/checks/formula_verification.json`.

## Gate Summary

| Formula | Role | Gate | Reason |
| --- | --- | --- | --- |
| EQ001 | published scattering-length parameterization | open, reconstructed | source rows and interpolation checks exist; original coupled-channel model is absent |
| EQ002 | attraction and locked density ratio | open, verified | derived directly from printed interaction relations |
| EQ003 | coupled GPE plus LHY functional | open, verified | functional and units trace to the paper and Petrov method |
| EQ004 | equilibrium densities and length scale | open, verified | symbolic and dimensional checks pass |
| EQ005 | universal stationary droplet equation | open, verified | radial reduction and boundary conditions are explicit |
| EQ006 | critical numbers and size observable | open, reconstructed | thresholds are verified; the paper's theory-density-to-Gaussian-width functional is unstated |
| EQ007 | time-averaged optical levitation | open, verified | printed modulation integral and signed force-gradient convention are checked |
| EQ008 | Thomas-Fermi expansion scaling | open, reconstructed | valid only for the declared proxy; exact calibration input is missing |
| EQ009 | 3D split-step dynamics and observables | open, reconstructed | method, observables, recovery, and smoke checks exist; paper-scale convergence and curve-specific atom numbers remain open |

## Closed Or Unclear Formulas

There are no gate-closed formula cards. Four input/method-level questions
remain: the original coupled-channel interaction model, the Fig. 3(b)
theory-width functional, Main Fig. 4 per-curve atom numbers, and the Supplement
Fig. S2 calibration atom number. The Fig. 4 initial field itself is generated
from the stated trapped-GPE procedure; no author array is needed. These gaps
reduce parameter or review status rather than silently closing the formulas.

Run:

```bash
python PRAgent-workflow/scripts/check_formula_gate.py case/1710.10890 --write
```
