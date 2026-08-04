# Numerical methods

The audit uses IEEE double precision only after exact algebra determines the
expected result. The evidence script samples a deterministic asymptotic path,
evaluates the exact source PPB family, differentiates the rational amplitude
analytically, and uses NumPy SVD on a `2 x 3` Jacobian.

This is a T0 local computation. An A100 would not improve the exact symbolic
obstruction and was therefore not used.
