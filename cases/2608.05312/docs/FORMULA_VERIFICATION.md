# Formula Verification

| Card | Gate | Evidence |
| --- | --- | --- |
| EQ001 | source_only | Hamiltonian and disorder law are explicit in Main Eq. (1). |
| EQ002 | verified | Bose-factor algebra independently gives the printed detailed-balance ratio. |
| EQ003 | source_only | All jump operators are explicit in the main text and SM. |
| EQ004 | verified | Factorization and completeness prove the one-way sum rule analytically. |
| EQ005 | source_only | SM Appendix C prints the closed-form solution used only as a check. |
| EQ006 | verified | Column-vectorization identity reproduces SM Eq. (S19). |
| EQ007 | source_only | SM Appendix E explicitly defines the projector partition. |

The formula lane is open for implementation. Parameter reconstruction is a
separate evidence issue: the paper omits mean `t`, exact source-state notation,
seeds, and some grids. Those gaps reduce parameter-match status but do not
alter the verified equations.
