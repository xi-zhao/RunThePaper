# Consistency Report

## Summary

| Level | Count | Meaning |
| --- | ---: | --- |
| high-fidelity scientific render | 1 | Fig. 6 passes the complete-region 90-point band. |
| scientific result with render gap | 2 | Figs. 5 and 7 pass physics but remain below the 80-point render gate. |
| source discrepancy | 3 | The same displacement-sign conflict affects publication-wide parameter identity for all targets. |
| not in numerical scope | 4 | Figs. 1–4 are method/geometry schematics; Fig. 4 still supplies an input parameter. |

## Per-target consistency

| Target | Science | Discretization | Publication variant | Pixel | Direct remaining issue |
| --- | --- | --- | --- | ---: | --- |
| T001 | passed | exact declared equivalence class | exact Fig. 4 branch | 69.0193 | sparse-curve rendering and fresh sign review |
| T002 | passed | exact declared equivalence class | exact Fig. 4 branch | 97.3720 | fresh sign review only |
| T003 | passed | exact declared equivalence class | exact Fig. 4 branch | 53.6671 | sparse-curve rendering and fresh sign review |

No code defect was found after parameter audit, convergence, independent
formula implementation, unit tests and isolated execution. The publication
conflict is recorded as probable, not promoted to a paper error without an
independent claim-level review.
