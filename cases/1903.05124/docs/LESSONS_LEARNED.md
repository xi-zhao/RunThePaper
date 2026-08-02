# Durable lessons

1. The scientific scope must count every visible numerical inset separately.
   This paper contains 44 theory-numerical items even though they are grouped
   into only six figure-level targets.
2. Circuit-layer timing is part of the physical model. Entropy before and after
   measurement must be tied to an explicit even/odd brick-wall convention.
3. Stabilizer trajectories should be shared across compatible observables, but
   each scientific claim still needs its own frozen inference and acceptance
   rule.
4. The phase-aware fixed-Pauli kernel makes the `n=22` Clifford frame-potential
   calculation polynomial and keeps every Monte Carlo sample exact.
5. More probability points can stabilize a collapse optimizer, but they cannot
   replace larger system sizes or more trajectories when estimating critical
   exponents.
6. Validation invariants must use the same normalization as the scaling law.
   The extensive entropy and entropy density have different derivative scaling.
7. “Constant within uncertainty” should be tested with uncertainty-weighted
   statistics, not only a raw maximum-minus-minimum range.
8. Scientific fidelity and raster fidelity remain separate. Pixel comparison
   is useful after the numerical evidence is frozen, but source pixels may not
   create, select, or alter scientific arrays.

The resulting package therefore preserves raw generated observations, seeds,
fit outputs, target-level checks, and explicit paper-scale versus feature-scale
labels. This makes later precision upgrades auditable without changing the
scientific model or hiding the current finite-size boundary.
