# Consistency Report

## Summary

| Level | Count | Meaning |
| --- | ---: | --- |
| exact_match | 3 | Main Fig. 2 and its two independent validation targets reproduce the analytic paper values. |
| feature_match | 1 | Main Fig. 1 fields and topology reproduce, with undisclosed rendering parameters. |
| partial_match | 1 | Fig. 1 invariant validation resolves the printed state but exposes a source contradiction. |
| blocked | 0 | No target is blocked by data, hardware, or compute. |

## Per-Target Consistency

| Target | Paper item | Level | Evidence | Difference | Likely reason |
| --- | --- | --- | --- | --- | --- |
| `T001` — theorem-overview fields | Main Fig. 1 | feature_match | `outputs/checks/t001_paper_target_run.json` | 3D presentation differs; printed +56 threshold is not satisfied | source omits rendering settings and contains an algebraic inconsistency |
| `T002` — W-state panels | Main Fig. 2(a,b) | exact_match | `outputs/checks/t002_paper_target_run.json` | raster styling only | analytic fields and witness parameters are fully disclosed |
| `V001` — disk threshold | Fig. 2(a) invariant | exact_match | `outputs/checks/v001_paper_target_run.json` | none | independent quadrature matches the closed form |
| `V002` — characteristic matrix | Fig. 2(b) invariant | exact_match | `outputs/checks/v002_paper_target_run.json` | none | direct Hermitian eigensolve reproduces 0.0176 |
| `V003` — Fig. 1 invariants | Fig. 1 End Matter | partial_match | `outputs/checks/v003_paper_target_run.json` | state gives +52; source prints +56 | source-internal inconsistency |

## Scientific Verdict

The W-state example is fully reproduced. For the illustrative Fig. 1 state,
the second theorem is exactly reproduced:
\(\widetilde W(0)=-7/(16\pi)\). The first-theorem conclusion is supported by
the displayed state only after correcting the threshold numerator from 56 to
52. The uncorrected printed inequality is not reproduced.
