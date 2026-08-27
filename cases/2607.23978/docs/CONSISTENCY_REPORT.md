# Consistency Report

## Summary

| Level | Count | Meaning |
| --- | ---: | --- |
| scientific feature passed | 4 | Every publicly defined theory target passed an analytic/numerical gate. |
| scientific render regions accepted (>=80) | 3 | All comparable theory-only regions pass. |
| high-fidelity render regions (>=90) | 1 | Fig. 2(c-d) reaches 90.11. |
| pixel not comparable | 1 | Optimal Fig. 2(e-f) series are interleaved with unavailable series. |
| blocked public inputs | 3 | `A1/A2`, full POVM, and finite `Delta gamma`. |
| not in scope | 1 | Fig. 1 apparatus. |

## Per-target consistency

| Target | Scientific evidence | Pixel evidence | Verdict |
| --- | --- | --- | --- |
| T001 | exact flat baselines and probability bounds | masked theory region 90.11 | science and render passed |
| T002 | adjoint conjugacy error `1.11e-16` | not comparable; analytic alternative evidence | science passed; pixel scope explicit |
| T003 | intended/literal identities agree within `2.58e-10` | masked theory region 81.75 | science and render passed; paper equation inconsistency recorded |
| T004 | Kraus validity and curve ordering pass all grid points | masked theory region 89.62 | science/render passed; paper-subset cap remains |

The source pixels are comparison-only evidence generated after numerical execution. They never enter the model or runner. The theory masks are generated from frozen independent arrays, are SHA-256 recorded, and cannot change the physical data.
