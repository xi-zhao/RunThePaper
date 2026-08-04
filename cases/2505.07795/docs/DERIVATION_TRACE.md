# Derivation trace

| Result | Source | Independent check |
| --- | --- | --- |
| `Tr rho(g)=d^(N_A l(g))` | permutation definition and replica trace | exact cycle enumeration |
| normalized late coefficient | supplement `SM:limiting_distribution_MSPE_after_replica` | unit-trace tests |
| finite-time raw correction | supplement large-t correction section | exact Eq. A3 dense solve |
| normalization subtraction | supplement normalization `C` and `K` | zero correction trace |
| Task 3 rate | supplement `eq:convergence_rate_for_norm_2` | source trace |
| Task 4 branches | supplement conditional-entropy section | source saddle trace |

The finite-time test uses (k=3) and compares the analytic first-order
coefficient with the exact (6\times6) permutation Gram system. The remaining
error falls by about four when (t) increases by one at (d=2), as expected
for (O(d^{-2(t+1)})).
