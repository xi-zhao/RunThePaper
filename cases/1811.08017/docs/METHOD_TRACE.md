# Method Trace

| Method | Paper source | Independent implementation | Gate |
| --- | --- | --- | --- |
| NUM001 | Appendix qDRIFT/Trotter/Suzuki error bounds | float log-domain bracket plus 60-digit Decimal boundary refinement | verified |
| NUM002 | Appendix phase-estimation Eqs. (E14), (E28) | direct floating-point evaluation on declared `P_f` grid | verified |
| AUDIT001 | all six numerical panels and prose audit points | independent grid, monotonicity, formula-parity, power-law, speedup, and crossover checks | verified |
| RENDER001 | source figures after data freeze | Matplotlib renderer reads only hash-frozen CSV arrays | verified |

The numerical computation is deterministic; no OpenFermion Hamiltonian or
author program is required because the resource bounds depend only on the three
parameter tuples printed in the paper.

The runner and panel audit never emit a paper verdict. Failed numerical or
precision invariants are `reproduction_defect`; a stable mismatch is
`inconclusive`. `paper_supported` and `paper_error_candidate` remain reserved
for a fresh protocol-v2 reviewer, with the latter requiring every additional
evidence gate recorded in `outputs/checks/panel_target_acceptance.json`.
