# Formula Verification

This document explains which formulas are allowed to feed numerical reproduction.

Machine-readable result:

```text
outputs/checks/formula_verification.json
```

Run:

```bash
python private validation harness/scripts/check_formula_gate.py case/<paper-id> --write
```

## Gate Summary

| Formula | Role | Gate | Reason |
| --- | --- | --- | --- |
| Q001 | lifted-product checks | open / verified | derived left/right regular actions and CSS matrices |
| Q002 | canonical logical basis | open / verified | derived linear solves; applicability depends on pivot invertibility |
| Q003 | length, dimension, rate | open / verified | exact GF(2) ranks recomputed |
| Q004 | magic-injection resources | open / verified | closed form independently evaluated |
| Q005 | sQetch Algorithm 1 | open / verified | pseudocode reimplemented and tested on Steane |
| Q006 | sketch hit probability | open / verified | inclusion and amplification bounds checked |
| Q007 | real-time utilization | open / verified | Eq. I1 arithmetic independently evaluated |

## Closed Or Unclear Formulas

| Formula | Reason | Numerical consequence |
| --- | --- | --- |
| none | all seven formula gates are open | numerical execution is permitted |

The open formula gate does not imply every paper claim passed. Q001's literal
Table-XIII input makes mitten-300's pivots singular, which is retained as a
scientific finding rather than patched from reported outputs.
