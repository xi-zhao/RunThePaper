# Derivation trace

| Claim | Source/input | Derivation | Code check |
| --- | --- | --- | --- |
| Reflection tail | Source Eqs. (S14)-(S15) | Laplace endpoint integral | `reflection_tail_asymptotic` |
| Printed `g_T` divergence | Source/frozen Eq. (S11) | Exact path expansion at `phi=pi/6` | `task1_divergent_path` |
| Frozen PPB set empty | Frozen definition C | Symmetric-polynomial numerator | `frozen_numerator_n3` |
| Source zero family | Source Eq. (S30) | Cubic factorization | `source_ppb_family` |
| Correct source radius/Jacobian | Source zero family | Global one-variable minimum and analytic derivative | `source_closest_radius`, `source_jacobian_singular_values` |
