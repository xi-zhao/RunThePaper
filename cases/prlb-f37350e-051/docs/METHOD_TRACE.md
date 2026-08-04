# Method trace

- Source recovery: official APS full text and page-level equation inspection.
- Symbolic audit: variational Hessian/response sign closure and exact rational
  series inversion.
- Numerical audit: arbitrary-precision Lindhard evaluation, deterministic scan,
  and bisection for the first positive root.
- Logical audit: explicit Yukawa/Coulomb distinction for high-q versus large-r.

No A100 was used because all decisive checks are analytic/T0 and high precision
is more useful than GPU throughput here.
