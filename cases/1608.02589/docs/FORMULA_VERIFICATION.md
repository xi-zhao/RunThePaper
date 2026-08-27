# Formula Verification

This case uses `EQUATION_CARDS.json` as the machine-readable formula map.

Machine-readable result:

```text
outputs/checks/formula_verification.json
```

Run:

```bash
python PRAgent-workflow/scripts/check_formula_gate.py case/1608.02589 --write
```

## Gate Summary

| Formula | Role | Gate | Reason |
| --- | --- | --- | --- |
| DTC001 | Floquet unitary | verified | Defines one-period binary Floquet evolution. |
| DTC002 | Pulse Hamiltonian | verified | Defines imperfect global spin flip and the noninteracting peak shift. |
| DTC003 | Interaction and disorder Hamiltonian | verified | Defines diagonal disorder phases for the driven spin chain. |
| DTC004 | Autocorrelation and half-frequency response | verified | Defines stroboscopic spin autocorrelation and subharmonic response. |
| DTC005 | Floquet level statistics | verified | Defines quasienergy adjacent-gap ratio. |
| DTC006 | Endpoint mutual information | verified | Defines endpoint mutual information for Floquet eigenstates. |
| DTC007 | Half-frequency peak variance | verified | Defines sample-to-sample half-frequency variance diagnostic. |

## Closed Or Unclear Formulas

None in the current local feature-level reproduction.
