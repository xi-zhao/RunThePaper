# Formula Verification

| Formula | Role | Gate | Key evidence |
| --- | --- | --- | --- |
| EQ001 | Dimensionless MBM | verified | complete-shell cutoff convergence |
| EQ002 | q lattice / T matrices | verified | Hermitian, C3-closed coupling graph |
| EQ003 | velocity/gap/magic criterion | verified | six reported magic velocities all below 0.012 |
| EQ004 | Wilson loop | verified | reciprocal embedding and C2x symmetry |
| EQ005 | PH-breaking expansion | verified_with_note | one printed `1.039°` label evaluates to `1.029°` |
| EQ006 | TB4-1V | verified | analytic Gamma levels agree to `2.22e-16` |
| EQ007 | TB8-2V | verified | intervalley term opens K gap |
| EQ008 | Wannier projection | verified | `det S(k)` in `[15.8215,16.0000]` |
| EQ009 | TB4-2V | verified | tuned K-mass identity satisfied |

Machine-readable formula cards are `EQUATION_CARDS.json`; the harness gate writes `outputs/checks/formula_verification.json`. The scientific solver has no API for reference images, author code, or source numerical arrays.
